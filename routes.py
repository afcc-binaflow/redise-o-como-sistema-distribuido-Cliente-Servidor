"""Capa HTTP: parsea, valida, llama y responde. Nada mas (RNF-11).

Aca no hay SQL ni hashing. Cada vista delega en `servicios` y se limita a
traducir entre HTTP y el dominio. La logica de negocio vive en servicios.py,
que es la misma que usan los workers del sistema distribuido (PFO3).
"""

import functools
import sqlite3

import jwt
from flask import current_app, g, jsonify, render_template, request

import servicios
from db import obtener_conexion

LIMITE_TITULO = 200
ID_MAXIMO = 2 ** 63 - 1


def bienvenida():
    return render_template("bienvenida.html")


def _validar_credenciales(datos):
    if not isinstance(datos, dict):
        return None, "El cuerpo debe ser un objeto JSON"
    usuario = datos.get("usuario")
    contrasena = datos.get("contraseña")
    if not isinstance(usuario, str) or not usuario.strip():
        return None, "El campo 'usuario' es obligatorio y debe ser un texto no vacío"
    if not isinstance(contrasena, str) or not contrasena:
        return None, "El campo 'contraseña' es obligatorio y debe ser un texto no vacío"
    return (usuario.strip(), contrasena), None


def _validar_tarea(datos):
    if not isinstance(datos, dict):
        return None, "El cuerpo debe ser un objeto JSON"
    titulo = datos.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        return None, "El campo 'titulo' es obligatorio y debe ser un texto no vacío"
    titulo = titulo.strip()
    if len(titulo) > LIMITE_TITULO:
        return None, "El campo 'titulo' no puede superar los 200 caracteres"
    completada = datos.get("completada", False)
    if not isinstance(completada, bool):
        return None, "El campo 'completada' debe ser un booleano"
    return (titulo, completada), None


def _id_fuera_del_rango(tarea_id):
    return not 1 <= tarea_id <= ID_MAXIMO


def _usuario_del_token():
    cabecera = request.headers.get("Authorization", "")
    esquema, _, token = cabecera.partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        return None
    usuario_id = servicios.decodificar_token(token.strip(), clave=current_app.config["SECRET_KEY"])
    return usuario_id


def requiere_token(vista):
    @functools.wraps(vista)
    def envoltura(*args, **kwargs):
        usuario_id = _usuario_del_token()
        if usuario_id is None:
            return jsonify({"error": "Token ausente o inválido"}), 401
        g.usuario_id = usuario_id
        return vista(*args, **kwargs)
    return envoltura


def registrar():
    datos = request.get_json(silent=True)
    credenciales, error = _validar_credenciales(datos)
    if error:
        return jsonify({"error": error}), 400
    usuario, contrasena = credenciales
    resultado = servicios.registrar(obtener_conexion(), usuario, contrasena)
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["status"]
    return jsonify(resultado["data"]), resultado["status"]


def iniciar_sesion():
    datos = request.get_json(silent=True)
    credenciales, error = _validar_credenciales(datos)
    if error:
        return jsonify({"error": error}), 400
    usuario, contrasena = credenciales
    resultado = servicios.iniciar_sesion(
        obtener_conexion(), usuario, contrasena, clave=current_app.config["SECRET_KEY"]
    )
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["status"]
    return jsonify(resultado["data"]), resultado["status"]


@requiere_token
def listar_tareas():
    resultado = servicios.listar_tareas(obtener_conexion(), g.usuario_id)
    return jsonify(resultado["data"]), resultado["status"]


@requiere_token
def crear_tarea():
    datos = request.get_json(silent=True)
    tarea, error = _validar_tarea(datos)
    if error:
        return jsonify({"error": error}), 400
    titulo, completada = tarea
    resultado = servicios.crear_tarea(obtener_conexion(), g.usuario_id, titulo, completada)
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["status"]
    return jsonify(resultado["data"]), resultado["status"]


@requiere_token
def obtener_tarea(tarea_id):
    if _id_fuera_del_rango(tarea_id):
        return jsonify({"error": "Recurso no encontrado"}), 404
    resultado = servicios.obtener_tarea(obtener_conexion(), g.usuario_id, tarea_id)
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["status"]
    return jsonify(resultado["data"]), resultado["status"]


@requiere_token
def actualizar_tarea(tarea_id):
    datos = request.get_json(silent=True)
    tarea, error = _validar_tarea(datos)
    if error:
        return jsonify({"error": error}), 400
    titulo, completada = tarea
    if _id_fuera_del_rango(tarea_id):
        return jsonify({"error": "Recurso no encontrado"}), 404
    resultado = servicios.actualizar_tarea(obtener_conexion(), g.usuario_id, tarea_id, titulo, completada)
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["status"]
    return jsonify(resultado["data"]), resultado["status"]


@requiere_token
def borrar_tarea(tarea_id):
    if _id_fuera_del_rango(tarea_id):
        return jsonify({"error": "Recurso no encontrado"}), 404
    resultado = servicios.borrar_tarea(obtener_conexion(), g.usuario_id, tarea_id)
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["status"]
    respuesta = current_app.response_class(status=204)
    respuesta.headers.pop("Content-Type", None)
    return respuesta


def recurso_no_encontrado(error):
    return jsonify({"error": "Recurso no encontrado"}), 404


def metodo_no_permitido(error):
    respuesta = jsonify({"error": "Método no permitido"})
    respuesta.status_code = 405
    metodos = getattr(error, "valid_methods", None)
    if metodos:
        respuesta.headers["Allow"] = ", ".join(metodos)
    return respuesta


def error_no_controlado(error):
    current_app.logger.exception("Error no controlado")
    return jsonify({"error": "Error interno del servidor"}), 500


def registrar_rutas(app):
    app.add_url_rule("/tareas", view_func=bienvenida, methods=["GET"])
    app.add_url_rule("/registro", view_func=registrar, methods=["POST"])
    app.add_url_rule("/login", view_func=iniciar_sesion, methods=["POST"])
    for regla, vista, metodos in (
        ("/api/tareas", listar_tareas, ["GET"]),
        ("/api/tareas", crear_tarea, ["POST"]),
        ("/api/tareas/<int:tarea_id>", obtener_tarea, ["GET"]),
        ("/api/tareas/<int:tarea_id>", actualizar_tarea, ["PUT"]),
        ("/api/tareas/<int:tarea_id>", borrar_tarea, ["DELETE"]),
    ):
        app.add_url_rule(
            regla,
            view_func=vista,
            methods=metodos,
            provide_automatic_options=False,
        )
    app.register_error_handler(404, recurso_no_encontrado)
    app.register_error_handler(405, metodo_no_permitido)
    app.register_error_handler(Exception, error_no_controlado)