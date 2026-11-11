"""Tests E2E del cliente de consola sobre socket (PFO3)."""

import io
import time

import pytest

from db import conectar, inicializar
from servidor_socket import ServidorSocket
from cliente_socket import ApiDeTareasSocket, menu


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
    time.sleep(0.2)
    yield srv
    srv.detener()
    try:
        conexion.close()
    except Exception:
        pass


def _api(servidor):
    return ApiDeTareasSocket(f"127.0.0.1:{servidor.puerto}", tiempo_espera=5)


def test_flujo_completo_por_menu(servidor):
    api = _api(servidor)
    entradas = [
        "1", "juan", "1234",          # registrarse
        "2", "juan", "1234",          # iniciar sesion
        "4", "estudiar",              # crear
        "3",                          # listar
        "7",                          # salir
    ]
    lector = iter(entradas)
    salida = io.StringIO()
    codigo = menu(api, leer=lambda _: next(lector), escribir=salida.write)
    assert codigo == 0
    texto = salida.getvalue()
    assert "Usuario 'juan' creado" in texto
    assert "Sesión iniciada como 'juan'" in texto
    assert "Tarea" in texto and "creada" in texto


def test_sin_sesion_muestra_aviso(servidor):
    api = _api(servidor)
    entradas = ["3", "7"]
    lector = iter(entradas)
    salida = io.StringIO()
    codigo = menu(api, leer=lambda _: next(lector), escribir=salida.write)
    assert codigo == 0
    assert "Primero inici" in salida.getvalue()


def test_opcion_invalida(servidor):
    api = _api(servidor)
    entradas = ["9", "7"]
    lector = iter(entradas)
    salida = io.StringIO()
    codigo = menu(api, leer=lambda _: next(lector), escribir=salida.write)
    assert codigo == 0
    assert "inválida" in salida.getvalue() or "invalida" in salida.getvalue()


def test_error_de_red_no_revienta(servidor):
    # apuntar a un puerto inexistente
    api = ApiDeTareasSocket("127.0.0.1:1", tiempo_espera=1)
    entradas = ["1", "juan", "1234", "7"]
    lector = iter(entradas)
    salida = io.StringIO()
    codigo = menu(api, leer=lambda _: next(lector), escribir=salida.write)
    assert codigo == 1
    assert "No se pudo conectar" in salida.getvalue()


def test_login_erroneo_muestra_error(servidor):
    _api(servidor).registrar("juan", "1234")
    api = _api(servidor)
    entradas = ["2", "juan", "mala", "7"]
    lector = iter(entradas)
    salida = io.StringIO()
    codigo = menu(api, leer=lambda _: next(lector), escribir=salida.write)
    assert codigo == 1
    assert "Error" in salida.getvalue()