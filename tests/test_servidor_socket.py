"""Tests del servidor de sockets (PFO3)."""

import socket
import time

import pytest

from db import conectar, inicializar
from servidor_socket import ServidorSocket


@pytest.fixture
def servidor():
    conexion = conectar(":memory:", check_same_thread=False)
    inicializar(conexion)
    srv = ServidorSocket(
        host="127.0.0.1",
        puerto=0,
        num_workers=2,
        clave="clave-solo-para-tests-de-32-bytes-o-mas",
        conexion_compartida=conexion,
    )
    srv.iniciar()
    # esperar a que el socket este listo
    time.sleep(0.2)
    yield srv
    srv.detener()
    try:
        conexion.close()
    except Exception:
        pass


def _enviar(srv, mensaje):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(("127.0.0.1", srv.puerto))
    import protocolo
    protocolo.enviar_mensaje(sock, mensaje)
    resp = protocolo.recibir_mensaje(sock)
    sock.close()
    return resp


def test_ping(servidor):
    import protocolo
    resp = _enviar(servidor, {"id": "1", "op": "ping", "payload": {}, "token": None})
    assert resp["status"] == "ok"
    assert resp["data"] == {"pong": True}


def test_flujo_completo(servidor):
    import protocolo
    # registrar
    r = _enviar(servidor, {"id": "r", "op": "registrar", "payload": {"usuario": "juan", "contraseña": "1234"}, "token": None})
    assert r["status"] == "ok"
    assert r["data"]["usuario"] == "juan"

    # login
    r = _enviar(servidor, {"id": "l", "op": "login", "payload": {"usuario": "juan", "contraseña": "1234"}, "token": None})
    assert r["status"] == "ok"
    token = r["data"]["token"]
    assert isinstance(token, str)

    # crear tarea
    r = _enviar(servidor, {"id": "c", "op": "crear", "payload": {"titulo": "estudiar", "completada": False}, "token": token})
    assert r["status"] == "ok"
    assert r["data"]["titulo"] == "estudiar"
    tarea_id = r["data"]["id"]

    # listar
    r = _enviar(servidor, {"id": "ls", "op": "listar", "payload": {}, "token": token})
    assert r["status"] == "ok"
    assert len(r["data"]) == 1

    # obtener
    r = _enviar(servidor, {"id": "g", "op": "obtener", "payload": {"id": tarea_id}, "token": token})
    assert r["status"] == "ok"
    assert r["data"]["id"] == tarea_id

    # actualizar
    r = _enviar(servidor, {"id": "u", "op": "actualizar", "payload": {"id": tarea_id, "titulo": "estudiar a fondo", "completada": True}, "token": token})
    assert r["status"] == "ok"
    assert r["data"]["completada"] is True

    # borrar
    r = _enviar(servidor, {"id": "d", "op": "borrar", "payload": {"id": tarea_id}, "token": token})
    assert r["status"] == "ok"

    # listar vacio
    r = _enviar(servidor, {"id": "ls2", "op": "listar", "payload": {}, "token": token})
    assert r["status"] == "ok"
    assert r["data"] == []


def test_sin_token_devuelve_error(servidor):
    r = _enviar(servidor, {"id": "x", "op": "listar", "payload": {}, "token": None})
    assert r["status"] == "error"
    assert r["code"] == 401


def test_operacion_desconocida(servidor):
    r = _enviar(servidor, {"id": "x", "op": "foo", "payload": {}, "token": None})
    assert r["status"] == "error"


def test_usuario_duplicado(servidor):
    _enviar(servidor, {"id": "r1", "op": "registrar", "payload": {"usuario": "juan", "contraseña": "1234"}, "token": None})
    r = _enviar(servidor, {"id": "r2", "op": "registrar", "payload": {"usuario": "juan", "contraseña": "1234"}, "token": None})
    assert r["status"] == "error"
    assert r["code"] == 409


def test_concurrencia(servidor):
    import threading
    resultados = []

    def worker():
        r = _enviar(servidor, {"id": "p", "op": "ping", "payload": {}, "token": None})
        resultados.append(r)

    hilos = [threading.Thread(target=worker) for _ in range(10)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=5)
    assert len(resultados) == 10
    assert all(r["status"] == "ok" for r in resultados)