"""
logger.py — Configuración centralizada de logging para la aplicación Contactos.

Uso en cualquier módulo:
    from app.comunes.logger import get_logger
    log = get_logger(__name__)
    log.info("mensaje")
    log.warning("aviso")
    log.error("error")

Los logs se escriben simultáneamente en:
  - Consola (stdout)
  - Fichero rotativo data/contactos.log (máx 2 MB, 5 backups)
"""

import logging
import logging.handlers
import os


# ── Ruta del fichero de log (junto a la BD, en data/) ────────────────────────
_BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_LOG_DIR   = os.environ.get('RUTA_LOG') or os.path.join(_BASE_DIR, 'data')
_LOG_FILE  = os.path.join(_LOG_DIR, 'contactos.log')
print(f"[logger] Log de la aplicación: {_LOG_FILE}")

# Formato: 2025-03-31 12:00:00,123 [INFO ] personas.routes : mensaje
_FMT  = '%(asctime)s [%(levelname)-5s] %(name)-30s: %(message)s'
_DATEFMT = '%Y-%m-%d %H:%M:%S'

_configurado = False


class _RotatingHandlerWindows(logging.handlers.RotatingFileHandler):
    """
    Subclase de RotatingFileHandler que cierra el fichero antes de renombrarlo.

    En Windows, un fichero abierto no se puede renombrar (WinError 32).
    La solución es cerrar el stream justo antes de la rotación y reabrirlo
    después. Python 3.12+ incluye esto de serie, pero esta subclase lo
    añade a versiones anteriores.
    """

    def rotation_filename(self, default_name: str) -> str:
        """Devuelve el nombre del fichero de backup (sin cambios)."""
        return default_name

    def doRollover(self) -> None:
        """Cierra el fichero antes de rotar para liberar el bloqueo en Windows."""
        if self.stream:
            self.stream.close()
            self.stream = None          # evita doble cierre en la clase padre
        super().doRollover()


def _configurar():
    global _configurado
    if _configurado:
        return

    os.makedirs(_LOG_DIR, exist_ok=True)

    raiz = logging.getLogger()
    raiz.setLevel(logging.DEBUG)

    fmt = logging.Formatter(_FMT, datefmt=_DATEFMT)

    # Handler consola
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fmt)

    # Handler fichero rotativo: 2 MB × 5 backups
    # Se usa la subclase _RotatingHandlerWindows para evitar WinError 32
    # cuando el proceso intenta renombrar el fichero mientras lo tiene abierto.
    try:
        fh = _RotatingHandlerWindows(
            _LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=5,
            encoding='utf-8', delay=True
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        raiz.addHandler(fh)
    except OSError as e:
        # Si no se puede escribir el fichero, solo consola
        print(f"[logger] No se puede crear fichero de log '{_LOG_FILE}': {e}")

    raiz.addHandler(ch)

    # Silenciar loggers muy verbosos de librerías externas
    for lib in ('werkzeug', 'sqlalchemy.engine', 'sqlalchemy.pool',
                'urllib3', 'pandas'):
        logging.getLogger(lib).setLevel(logging.WARNING)

    _configurado = True


def get_logger(nombre: str) -> logging.Logger:
    """Devuelve un logger ya configurado con el nombre dado."""
    _configurar()
    return logging.getLogger(nombre)
