"""Tests del protocolo de mensajes sobre socket (PFO3)."""

import socket
import threading

import protocolo


def _par_de_sockets():
    """Crea un par de sockets conectados entre sí (TCP loopback)."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    puerto = servidor.getsockname()[1]

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect(("127.0.0.1", puerto))
    conexion, _ = servidor.accept()
    servidor.close()
    return cliente, conexion


def test_enviar_y_recibir_mensaje_simple():
    a, b = _par_de_sockets()
    try:
        mensaje = {"id": "1", "op": "ping", "payload": {"x": 5}, "token": None}
        protocolo.enviar_mensaje(a, mensaje)
        recibido = protocolo.recibir_mensaje(b)
        assert recibido == mensaje
    finally:
        a.close()
        b.close()


def test_roundtrip_varios_mensajes():
    a, b = _par_de_sockets()
    try:
        for i in range(5):
            protocolo.enviar_mensaje(a, {"id": str(i), "op": "eco", "payload": i})
            assert protocolo.recibir_mensaje(b) == {
                "id": str(i),
                "op": "eco",
                "payload": i,
            }
    finally:
        a.close()
        b.close()


def test_unicode_se_preserva():
    a, b = _par_de_sockets()
    try:
        mensaje = {"id": "u", "op": "eco", "payload": "contraseña ñ áéíóú"}
        protocolo.enviar_mensaje(a, mensaje)
        assert protocolo.recibir_mensaje(b) == mensaje
    finally:
        a.close()
        b.close()


def test_conexion_cerrada_lanza_error():
    a, b = _par_de_sockets()
    a.close()
    try:
        try:
            protocolo.recibir_mensaje(b)
            assert False, "debería lanzar"
        except protocolo.ErrorDeProtocolo:
            pass
    finally:
        b.close()


def test_mensaje_no_serializable_lanza_error():
    a, _ = _par_de_sockets()
    try:
        try:
            protocolo.enviar_mensaje(a, {"id": "x", "op": "o", "payload": object()})
            assert False, "debería lanzar"
        except protocolo.ErrorDeProtocolo:
            pass
    finally:
        a.close()


def test_bidireccional_concurrente():
    a, b = _par_de_sockets()
    resultados = {}

    def worker():
        resultados["b"] = protocolo.recibir_mensaje(b)

    hilo = threading.Thread(target=worker)
    hilo.start()
    protocolo.enviar_mensaje(a, {"id": "c", "op": "hola"})
    hilo.join(timeout=2)
    assert resultados["b"] == {"id": "c", "op": "hola"}
    a.close()
    b.close()