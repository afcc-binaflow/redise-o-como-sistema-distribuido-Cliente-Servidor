"""Logica de dominio independiente de transporte (PFO3).

Estas funciones encapsulan las operaciones del gestor de tareas (usuarios y
tareas) sin depender de HTTP ni de sockets. Tanto la API REST (routes.py) como
los workers del sistema distribuido las llaman, de modo que la regla de
negocio vive en un solo lugar.

Cada funcion recibe una conexion SQLite como primer argumento y devuelve un
dict con la forma:
    {"ok": bool, "status": int, "data": ..., "error": str | None}
donde `status` es el codigo HTTP equivalente (util para compatibilidad con la
API REST) y `data`/`error` son mutuamente excluyentes en el caso feliz.
"""

import sqlite3

import repository
import security
from db import conectar


def _ok(status, data):
    return {"ok": True, "status": status, "data": data, "error": None}


def _error(status, mensaje):
    return {"ok": False, "status": status, "data": None, "error": mensaje}


def registrar(conexion, usuario, contrasena):
    if not isinstance(usuario, str) or not usuario.strip():
        return _error(400, "El campo 'usuario' es obligatorio y debe ser un texto no vacío")
    if not isinstance(contrasena, str) or not contrasena:
        return _error(400, "El campo 'contraseña' es obligatorio y debe ser un texto no vacío")
    usuario = usuario.strip()
    try:
        repository.crear_usuario(conexion, usuario, security.hashear_password(contrasena))
    except sqlite3.IntegrityError:
        return _error(409, "El usuario ya existe")
    return _ok(201, {"usuario": usuario})


def iniciar_sesion(conexion, usuario, contrasena, clave=None):
    if not isinstance(usuario, str) or not usuario.strip():
        return _error(400, "El campo 'usuario' es obligatorio y debe ser un texto no vacío")
    if not isinstance(contrasena, str) or not contrasena:
        return _error(400, "El campo 'contraseña' es obligatorio y debe ser un texto no vacío")
    usuario = usuario.strip()
    guardado = repository.buscar_usuario_por_nombre(conexion, usuario)
    if guardado is None or not security.verificar_password(guardado["password_hash"], contrasena):
        return _error(401, "Usuario o contraseña incorrectos")
    token = security.crear_token(guardado["id"], clave=clave)
    return _ok(200, {"token": token})


def listar_tareas(conexion, usuario_id):
    tareas = repository.listar_tareas_de(conexion, usuario_id)
    return _ok(200, tareas)


def crear_tarea(conexion, usuario_id, titulo, completada=False):
    if not isinstance(titulo, str) or not titulo.strip():
        return _error(400, "El campo 'titulo' es obligatorio y debe ser un texto no vacío")
    titulo = titulo.strip()
    if len(titulo) > 200:
        return _error(400, "El campo 'titulo' no puede superar los 200 caracteres")
    if not isinstance(completada, bool):
        return _error(400, "El campo 'completada' debe ser un booleano")
    tarea_id = repository.crear_tarea(conexion, titulo, usuario_id, completada)
    return _ok(201, {"id": tarea_id, "titulo": titulo, "completada": completada})


def obtener_tarea(conexion, usuario_id, tarea_id):
    if not (1 <= tarea_id <= 2 ** 63 - 1):
        return _error(404, "Recurso no encontrado")
    tarea = repository.obtener_tarea_de(conexion, tarea_id, usuario_id)
    if tarea is None:
        return _error(404, "Recurso no encontrado")
    return _ok(200, tarea)


def actualizar_tarea(conexion, usuario_id, tarea_id, titulo, completada):
    if not isinstance(titulo, str) or not titulo.strip():
        return _error(400, "El campo 'titulo' es obligatorio y debe ser un texto no vacío")
    titulo = titulo.strip()
    if len(titulo) > 200:
        return _error(400, "El campo 'titulo' no puede superar los 200 caracteres")
    if not isinstance(completada, bool):
        return _error(400, "El campo 'completada' debe ser un booleano")
    if not (1 <= tarea_id <= 2 ** 63 - 1):
        return _error(404, "Recurso no encontrado")
    if not repository.actualizar_tarea_de(conexion, tarea_id, usuario_id, titulo, completada):
        return _error(404, "Recurso no encontrado")
    actualizada = repository.obtener_tarea_de(conexion, tarea_id, usuario_id)
    return _ok(200, actualizada)


def borrar_tarea(conexion, usuario_id, tarea_id):
    if not (1 <= tarea_id <= 2 ** 63 - 1):
        return _error(404, "Recurso no encontrado")
    if not repository.borrar_tarea_de(conexion, tarea_id, usuario_id):
        return _error(404, "Recurso no encontrado")
    return _ok(204, None)


def decodificar_token(token, clave=None):
    """Devuelve el usuario_id o None si el token es invalido."""
    import jwt
    try:
        payload = security.decodificar_token(token, clave=clave)
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return None


def abrir_conexion(ruta):
    """Helper para workers: abre una conexion lista para usar."""
    return conectar(ruta)