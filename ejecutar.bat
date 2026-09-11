echo off

:: ══════════════════════════════════════════════
::  SCRIPT DE ARRANQUE — 17-contactos
:: ══════════════════════════════════════════════
::
:: Autor: Javier C.
:: Fecha: 2026-03-23

:: Leer las variables de entorno desde el archivo var.env
for /f "usebackq tokens=1,* delims==" %%A in ("E:\\Python\\config\\DES\\var.env") do (
    set "%%A=%%B"
    )

::  Ejecuatar aplicación Flask para gestionar contactos
echo Arrancando Appweb Contactos...
echo     Base de datos : %RUTA_BD_CONTACTOS%
echo     Puerto        : %APP_PORT_CONTACTOS%
echo --------------------------------------------------------------------------

python run.py
