import os
from app.app import app as aplicacion
from app.app import db, log
from app.tipos_valores.models import Tipos, TiposValores




# ---------------------------------------------------------------------------
# Datos por defecto para TIPOS y TIPOS_VALORES
# Se insertan solo si las tablas están vacías (primera ejecución).
# ---------------------------------------------------------------------------

TIPOS_DEFECTO = [
    (1, 'Eventos',        'Cumpleaños, Aniversarios, etc.'),
    (2, 'Relaciones',     'Pareja, Marido, Esposa, Hijos, Padres, Empresa'),
    (3, 'Contacto',       'Teléfono, Email, Dirección, Web, etc.'),
    (4, 'Lugar Contacto', 'Personal, Casa, Antiguo, Móvil, Trabajo, Whatsapp, Atención Cliente, etc.'),
]

TIPOS_VALORES_DEFECTO = [
    (1,  1, 'Cumpleaños'),
    (2,  1, 'Aniversario'),
    (3,  2, 'Pareja'),
    (4,  2, 'Marido'),
    (5,  2, 'Mujer'),
    (6,  2, 'Hijo/a'),
    (7,  2, 'Padres'),
    (8,  2, 'Empresa'),
    (9,  3, 'Teléfono'),
    (10, 3, 'Email'),
    (11, 3, 'Dirección'),
    (12, 3, 'Web'),
    (13, 3, 'Empresa'),
    (14, 4, 'Personal'),
    (15, 4, 'Casa'),
    (16, 4, 'Trabajo'),
    (17, 4, 'Antiguo'),
    (18, 4, 'Móvil'),
    (19, 4, 'WhatsApp'),
    (20, 4, 'Atención Cliente'),
]


def insertar_datos_defecto():
    """Inserta los tipos y tipos_valores por defecto si las tablas están vacías."""
    if Tipos.query.count() == 0:
        for id_, nombre, descripcion in TIPOS_DEFECTO:
            db.session.add(Tipos(id=id_, nombre=nombre, descripcion=descripcion))
        db.session.commit()

    if TiposValores.query.count() == 0:
        for id_, tipo_id, nombre in TIPOS_VALORES_DEFECTO:
            db.session.add(TiposValores(id=id_, TipoId=tipo_id, nombre=nombre))
        db.session.commit()



if __name__ == "__main__":
    try:
        with aplicacion.app_context():
            db.create_all()
            insertar_datos_defecto()
    except Exception as e:
        log.error(f"Error al inicializar la base de datos: {e}")
        raise

    APP_PORT_CONTACTOS = int(os.environ.get("APP_PORT_CONTACTOS") or 5000)
    aplicacion.run(port=APP_PORT_CONTACTOS)
    # aplicacion.run(host="0.0.0.0", port=APP_PORT_CONTACTOS)

    # Conexión segura https para el NAS
    # aplicacion.run(ssl_context=('/usr/config/cert.pem', '/usr/config/privkey.pem'),
    #               host="192.168.1.41", port=5010, debug=True)
        
    # Cambiamos a HTTP utilizando el proxy inverso del NAS
    #    aplicacion.run(port=5010)
