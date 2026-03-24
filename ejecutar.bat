echo off

:: Autor: Javier C.
:: Fecha: 2026-03-23

:: Definición de variables de entorno
SET APP_PORT_CONTACTOS=5012
SET RUTA_BD_CONTACTOS=D:\\Python\\Proyectos\\17-contactos\\data\\contactos.db
SET SECRET_KEY='A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
SET DEBUG=True

::  Ejecuatar aplicación Flask para gestionar contactos
echo Arrancando Appweb Contactos...
echo     Base de datos : %RUTA_BD_CONTACTOS%
echo     Puerto        : %APP_PORT_CONTACTOS%
echo --------------------------------------------------------------------------

python run.py
