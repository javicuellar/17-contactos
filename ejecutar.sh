#!/bin/bash
# ══════════════════════════════════════════════
#  SCRIPT DE ARRANQUE — 17-contactos
# ══════════════════════════════════════════════
#
# Autor: Javier C.
# Fecha: 2026-03-16

# Actualizar e instalar tzdata para evitar problemas con la zona horaria
apt-get update && apt-get install -y --no-install-recommends \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

# Timezone (override with TZ env var)
export TZ=Europe/Madrid
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# instalar dependencias de Python
pip install --no-cache-dir -r ./requirements.txt

set -e

echo "  Arrancando Aplicación Contactos ..."
echo "    Base de datos : $RUTA_BD_CONTACTOS"
echo "    Puerto        : $APP_PORT_CONTACTOS"
echo ""

python run.py
