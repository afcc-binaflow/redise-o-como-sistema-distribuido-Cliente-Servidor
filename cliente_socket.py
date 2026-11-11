"""Cliente de consola del gestor de tareas sobre socket (PFO3).

Misma separacion en dos capas que `cliente.py`:
- `ApiDeTareasSocket` es transporte: arma el mensaje, lo envia con framing, lee
  la respuesta y la traduce a datos o excepcion. No imprime nada.
- `menu` es presentacion: lee opciones, llama al transporte e imprime.

El protocolo es el de `protocolo.py` (JSON con longitud prefijada sobre TCP).
"""

import os
import socket
import sys
import uuid

import protocolo

URL_BASE_POR_DEFECTO = "127.0.0.1:9000"
TIEMPO_ESPERA = 5
_SALIR = "7"


class ErrorDeApi(Exception):
    def __init__(self, codigo, mensaje, sesion_cerrada=False):
        super().__init__(f"{codigo}: {mensaje}")
        self.codigo = codigo
        self.mensaje = mensaje
        self.sesion_cerrada = sesion_cerrada


class ErrorDeRed(Exception):
    def __init__(self, motivo):
        super().__init__(motivo)
        self.motivo = motivo


class ErrorDeUso(Exception):
    pass


class _FinDeEntrada(Exception):
    pass


class ApiDeTareasSocket:
    def __init__(self, direccion=URL_BASE_POR_DEFECTO, tiempo_espera=TIEMPO_ESPERA):
        host, _, puerto = direccion.rpartition(":")
        self.host = host or "127.0.0.1"
        self.puerto = int(puerto)
        self.tiempo_espera = tiempo_espera
        self.token = None

    def _host_puerto(self):
        return self.host, self.puerto

    def _enviar(self, op, payload=None, autenticada=True):
        mensaje = {
            "id": str(uuid.uuid4()),
            "op": op,
            "payload": payload or {},
            "token": self.token if (autenticada and self.token) else None,
        }
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.tiempo_espera)
        try:
            sock.connect((self.host, self.puerto))
            protocolo.enviar_mensaje(sock, mensaje)
            respuesta = protocolo.recibir_mensaje(sock)
        except (OSError, protocolo.ErrorDeProtocolo) as error:
            raise ErrorDeRed(str(error)) from None
        finally:
            try:
                sock.close()
            except OSError:
                pass

        if not isinstance(respuesta, dict):
            raise ErrorDeRed("respuesta invalida del servidor")
        if respuesta.get("status") != "ok":
            codigo = respuesta.get("code", 400)
            sesion_cerrada = codigo == 401 and bool(self.token) and autenticada
            if sesion_cerrada:
                self.token = None
            raise ErrorDeApi(codigo, respuesta.get("error", "error"), sesion_cerrada)
        return respuesta.get("data")

    # -- autenticacion -----------------------------------------------------
    def registrar(self, usuario, contrasena):
        return self._enviar("registrar", {"usuario": usuario, "contraseña": contrasena}, autenticada=False)

    def iniciar_sesion(self, usuario, contrasena):
        datos = self._enviar("login", {"usuario": usuario, "contraseña": contrasena}, autenticada=False)
        self.token = datos["token"]
        return datos

    def cerrar_sesion(self):
        self.token = None

    # -- tareas ------------------------------------------------------------
    def listar_tareas(self):
        return self._enviar("listar", {})

    def crear_tarea(self, titulo):
        return self._enviar("crear", {"titulo": titulo})

    def actualizar_tarea(self, tarea_id, titulo, completada):
        return self._enviar("actualizar", {"id": tarea_id, "titulo": titulo, "completada": completada})

    def borrar_tarea(self, tarea_id):
        return self._enviar("borrar", {"id": tarea_id})


def formatear_error(error):
    if isinstance(error, ErrorDeApi):
        linea = f"Error {error.codigo}: {error.mensaje}"
        if error.sesion_cerrada:
            linea += ". Volvé a iniciar sesión (opción 2)"
        return linea
    if isinstance(error, ErrorDeRed):
        return f"No se pudo conectar con el servidor: {error.motivo}"
    return str(error)


# ---------------------------------------------------------------------------
# Presentacion (igual que cliente.py)
# ---------------------------------------------------------------------------
def menu(api, leer=input, escribir=print):
    def pedir(mensaje):
        try:
            return leer(mensaje)
        except (EOFError, StopIteration):
            raise _FinDeEntrada from None

    codigo = 0
    while True:
        _mostrar_menu(api, escribir)
        try:
            opcion = pedir("Opción: ").strip()
            if opcion == _SALIR:
                escribir("Hasta luego.")
                return codigo
            entrada = _ACCIONES.get(opcion)
            if entrada is None:
                escribir("Opción inválida. Elegí un número del 1 al 7.")
                continue
            _, accion = entrada
            accion(api, pedir, escribir)
        except _FinDeEntrada:
            return codigo
        except (ErrorDeApi, ErrorDeRed, ErrorDeUso) as error:
            escribir(formatear_error(error))
            codigo = 1


def _mostrar_menu(api, escribir):
    escribir("")
    escribir("=== Gestor de tareas (socket) ===")
    escribir("Sesión iniciada." if api.token else "Sin sesión iniciada.")
    for clave, (etiqueta, _) in _ACCIONES.items():
        escribir(f"{clave}. {etiqueta}")
    escribir(f"{_SALIR}. Salir")


def _hay_sesion(api, escribir):
    if api.token:
        return True
    escribir("Primero iniciá sesión (opción 2).")
    return False


def _registrarse(api, pedir, escribir):
    usuario = pedir("Usuario: ").strip()
    contrasena = pedir("Contraseña: ")
    datos = api.registrar(usuario, contrasena)
    escribir(f"Usuario '{datos['usuario']}' creado. Ahora iniciá sesión (opción 2).")


def _iniciar_sesion(api, pedir, escribir):
    usuario = pedir("Usuario: ").strip()
    contrasena = pedir("Contraseña: ")
    api.iniciar_sesion(usuario, contrasena)
    escribir(f"Sesión iniciada como '{usuario}'.")


def _listar(api, pedir, escribir):
    if not _hay_sesion(api, escribir):
        return
    tareas = api.listar_tareas()
    if not tareas:
        escribir("No tenés tareas todavía.")
        return
    for tarea in tareas:
        marca = "[x]" if tarea["completada"] else "[ ]"
        escribir(f"{tarea['id']} {marca} {tarea['titulo']}")


def _crear(api, pedir, escribir):
    if not _hay_sesion(api, escribir):
        return
    titulo = pedir("Título: ")
    tarea = api.crear_tarea(titulo)
    escribir(f"Tarea {tarea['id']} creada.")


def _editar(api, pedir, escribir):
    if not _hay_sesion(api, escribir):
        return
    tarea_id = _pedir_id(pedir)
    titulo = pedir("Título: ")
    completada = _pedir_completada(pedir)
    tarea = api.actualizar_tarea(tarea_id, titulo, completada)
    escribir(f"Tarea {tarea['id']} actualizada.")


def _borrar(api, pedir, escribir):
    if not _hay_sesion(api, escribir):
        return
    tarea_id = _pedir_id(pedir)
    api.borrar_tarea(tarea_id)
    escribir(f"Tarea {tarea_id} borrada.")


def _pedir_id(pedir):
    texto = pedir("Id de la tarea: ").strip()
    try:
        return int(texto)
    except ValueError:
        raise ErrorDeUso("El id tiene que ser un número entero") from None


def _pedir_completada(pedir):
    texto = pedir("¿Completada? (s/n): ").strip().lower()
    if texto == "s":
        return True
    if texto == "n":
        return False
    raise ErrorDeUso("Respondé s o n")


_ACCIONES = {
    "1": ("Registrarse", _registrarse),
    "2": ("Iniciar sesión", _iniciar_sesion),
    "3": ("Listar tareas", _listar),
    "4": ("Crear tarea", _crear),
    "5": ("Editar tarea", _editar),
    "6": ("Borrar tarea", _borrar),
}


def _configurar_utf8():
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")


def principal():
    _configurar_utf8()
    direccion = os.environ.get("PFO3_API_URL", URL_BASE_POR_DEFECTO)
    return menu(ApiDeTareasSocket(direccion))


if __name__ == "__main__":
    sys.exit(principal())