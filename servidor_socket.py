"""Servidor de sockets del sistema distribuido (PFO3).

Recibe tareas (operaciones del gestor) por TCP, las encola en una cola de
mensajes (simulada con `queue.Queue`, que representa a RabbitMQ) y las
distribuye a un pool de workers con hilos. Cada worker ejecuta la operacion de
dominio contra el almacenamiento y devuelve el resultado al cliente.

Protocolo: ver `protocolo.py` (framing por longitud).
"""

import queue
import socket
import threading
import uuid

import protocolo
import servicios
from db import conectar


class ServidorSocket:
    def __init__(
        self,
        host="127.0.0.1",
        puerto=0,
        ruta_db=":memory:",
        num_workers=4,
        clave=None,
        conexion_compartida=None,
    ):
        self.host = host
        self.puerto = puerto
        self.ruta_db = ruta_db
        self.num_workers = num_workers
        self.clave = clave
        self.conexion_compartida = conexion_compartida
        self._lock_db = threading.Lock() if conexion_compartida is not None else None

        self._cola_entrada = queue.Queue()
        self._pendientes = {}  # id_peticion -> (evento, contenedor)
        self._lock_pendientes = threading.Lock()

        self._socket = None
        self._workers = []
        self._conexiones = []
        self._hilo_aceptador = None
        self._activo = threading.Event()

    # -- ciclo de vida -------------------------------------------------------
    def iniciar(self):
        self._activo.set()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.puerto))
        self.puerto = self._socket.getsockname()[1]
        self._socket.listen(128)
        self._socket.settimeout(0.5)

        for _ in range(self.num_workers):
            hilo = threading.Thread(target=self._worker_loop, daemon=True)
            hilo.start()
            self._workers.append(hilo)

        self._hilo_aceptador = threading.Thread(target=self._aceptar_loop, daemon=True)
        self._hilo_aceptador.start()

    def detener(self):
        self._activo.clear()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
        # desbloquear workers
        for _ in self._workers:
            self._cola_entrada.put(None)
        for hilo in self._workers:
            hilo.join(timeout=2)
        self._workers.clear()
        for conn in list(self._conexiones):
            try:
                conn.close()
            except OSError:
                pass
        self._conexiones.clear()
        if self._hilo_aceptador is not None:
            self._hilo_aceptador.join(timeout=2)

    # -- aceptacion de conexiones -------------------------------------------
    def _aceptar_loop(self):
        while self._activo.is_set():
            try:
                conn, _ = self._socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._conexiones.append(conn)
            hilo = threading.Thread(target=self._manejar_conexion, args=(conn,), daemon=True)
            hilo.start()

    def _manejar_conexion(self, conn):
        try:
            while self._activo.is_set():
                try:
                    mensaje = protocolo.recibir_mensaje(conn)
                except protocolo.ErrorDeProtocolo:
                    break
                if not isinstance(mensaje, dict):
                    protocolo.enviar_mensaje(conn, {"id": None, "status": "error", "error": "mensaje invalido"})
                    continue
                id_peticion = mensaje.get("id") or str(uuid.uuid4())
                evento = threading.Event()
                contenedor = {}
                with self._lock_pendientes:
                    self._pendientes[id_peticion] = (evento, contenedor)
                self._cola_entrada.put({
                    "id": id_peticion,
                    "op": mensaje.get("op"),
                    "payload": mensaje.get("payload") or {},
                    "token": mensaje.get("token"),
                })
                # esperar resultado del worker
                if evento.wait(timeout=30):
                    respuesta = contenedor.get("resultado", {"status": "error", "error": "sin resultado"})
                else:
                    respuesta = {"status": "error", "error": "timeout del worker"}
                protocolo.enviar_mensaje(conn, {"id": id_peticion, **respuesta})
        except (OSError, protocolo.ErrorDeProtocolo):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    # -- worker loop ---------------------------------------------------------
    def _obtener_conexion(self):
        if self.conexion_compartida is not None:
            return self.conexion_compartida, False
        return conectar(self.ruta_db), True

    def _worker_loop(self):
        while self._activo.is_set():
            item = self._cola_entrada.get()
            if item is None:
                break
            id_peticion = item["id"]
            resultado = self._procesar(item)
            with self._lock_pendientes:
                pendiente = self._pendientes.pop(id_peticion, None)
            if pendiente is not None:
                evento, contenedor = pendiente
                contenedor["resultado"] = resultado
                evento.set()

    def _procesar(self, item):
        op = item.get("op")
        payload = item.get("payload") or {}
        token = item.get("token")
        conexion, propia = self._obtener_conexion()
        try:
            if self._lock_db is not None:
                with self._lock_db:
                    return self._ejecutar_op(op, payload, token, conexion)
            return self._ejecutar_op(op, payload, token, conexion)
        except Exception as error:  # noqa: BLE001
            return {"status": "error", "error": f"error interno: {error}"}
        finally:
            if propia:
                try:
                    conexion.close()
                except Exception:  # noqa: BLE001
                    pass

    def _usuario_id_desde_token(self, token):
        if not token:
            return None
        return servicios.decodificar_token(token, clave=self.clave)

    def _ejecutar_op(self, op, payload, token, conexion):
        if op == "ping":
            return {"status": "ok", "data": {"pong": True}}

        if op == "registrar":
            r = servicios.registrar(conexion, payload.get("usuario"), payload.get("contraseña"))
            return self._traducir(r)

        if op == "login":
            r = servicios.iniciar_sesion(conexion, payload.get("usuario"), payload.get("contraseña"), clave=self.clave)
            return self._traducir(r)

        usuario_id = self._usuario_id_desde_token(token)
        if usuario_id is None:
            return {"status": "error", "error": "Token ausente o inválido", "code": 401}

        if op == "listar":
            r = servicios.listar_tareas(conexion, usuario_id)
            return self._traducir(r)
        if op == "crear":
            r = servicios.crear_tarea(conexion, usuario_id, payload.get("titulo"), payload.get("completada", False))
            return self._traducir(r)
        if op == "obtener":
            r = servicios.obtener_tarea(conexion, usuario_id, int(payload.get("id", 0)))
            return self._traducir(r)
        if op == "actualizar":
            r = servicios.actualizar_tarea(
                conexion, usuario_id, int(payload.get("id", 0)),
                payload.get("titulo"), payload.get("completada", False),
            )
            return self._traducir(r)
        if op == "borrar":
            r = servicios.borrar_tarea(conexion, usuario_id, int(payload.get("id", 0)))
            return self._traducir(r)

        return {"status": "error", "error": f"operacion desconocida: {op}", "code": 400}

    @staticmethod
    def _traducir(resultado):
        if resultado["ok"]:
            return {"status": "ok", "data": resultado["data"], "code": resultado["status"]}
        return {"status": "error", "error": resultado["error"], "code": resultado["status"]}