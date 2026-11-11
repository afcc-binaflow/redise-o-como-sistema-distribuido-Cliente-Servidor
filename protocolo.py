"""Protocolo de mensajes sobre socket TCP (PFO3).

Formato de trama (framing):
    [4 bytes big-endian: longitud del payload JSON][payload JSON UTF-8]

Se usa longitud prefijada en lugar de delimitadores porque el JSON puede
contener cualquier caracter, incluido el separador elegido, y porque permite
enviar mensajes de tamaño arbitrario sin ambigüedad.

Cada mensaje es un dict con al menos:
    - "id": identificador de la petición (para correlacionar respuesta)
    - "op": operación solicitada
    - "payload": datos de la operación
    - "token": token de autenticación (opcional)
"""

import json
import socket
import struct

LONGITUD_CABECERA = 4  # bytes
CODIFICACION = "utf-8"
MAX_MENSAJE = 10 * 1024 * 1024  # 10 MiB, protección contra OOM


class ErrorDeProtocolo(Exception):
    """Error al enviar o recibir un mensaje."""


def _enviar_todo(sock, datos):
    """Envía todos los bytes; lanza ErrorDeProtocolo si la conexión se corta."""
    vista = memoryview(datos)
    total = 0
    while total < len(datos):
        try:
            enviados = sock.send(vista[total:])
        except (OSError, socket.error) as error:
            raise ErrorDeProtocolo(f"error de envío: {error}") from error
        if enviados == 0:
            raise ErrorDeProtocolo("conexión cerrada durante el envío")
        total += enviados


def enviar_mensaje(sock, mensaje):
    """Serializa `mensaje` (dict) y lo envía con framing por longitud."""
    try:
        payload = json.dumps(mensaje, ensure_ascii=False).encode(CODIFICACION)
    except (TypeError, ValueError) as error:
        raise ErrorDeProtocolo(f"mensaje no serializable: {error}") from error
    if len(payload) > MAX_MENSAJE:
        raise ErrorDeProtocolo("mensaje demasiado grande")
    cabecera = struct.pack("!I", len(payload))
    _enviar_todo(sock, cabecera + payload)


def _recibir_exacto(sock, cantidad):
    """Recibe exactamente `cantidad` bytes o lanza ErrorDeProtocolo."""
    buffer = bytearray()
    while len(buffer) < cantidad:
        try:
            bloque = sock.recv(cantidad - len(buffer))
        except (OSError, socket.error) as error:
            raise ErrorDeProtocolo(f"error de recepción: {error}") from error
        if not bloque:
            raise ErrorDeProtocolo("conexión cerrada durante la recepción")
        buffer.extend(bloque)
    return bytes(buffer)


def recibir_mensaje(sock):
    """Lee una trama y devuelve el dict deserializado."""
    cabecera = _recibir_exacto(sock, LONGITUD_CABECERA)
    (longitud,) = struct.unpack("!I", cabecera)
    if longitud == 0 or longitud > MAX_MENSAJE:
        raise ErrorDeProtocolo(f"longitud inválida: {longitud}")
    payload = _recibir_exacto(sock, longitud)
    try:
        return json.loads(payload.decode(CODIFICACION))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ErrorDeProtocolo(f"payload inválido: {error}") from error