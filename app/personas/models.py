from sqlalchemy import Column, ForeignKey, DateTime, Date
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.app import db




class Personas(db.Model):
    """Personas — Tabla de personas con auditoría"""
    __tablename__ = 'personas'
    id           = Column(Integer, primary_key=True)
    UsuarioId    = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    apodo        = Column(String(150), nullable=False)
    nombre       = Column(String(200), nullable=False)
    notas        = Column(String(255))
    
    usuario_alta = Column(String(100), nullable=False)
    fecha_alta   = Column(DateTime, nullable=False, default=datetime.now)
    usuario_mod  = Column(String(100))
    fecha_mod    = Column(DateTime)
    usuario_baja = Column(String(100))
    fecha_baja   = Column(DateTime)

    rel_etiquetas   = relationship("Rel_persona_etiqueta",
                                    cascade="all, delete-orphan", lazy='dynamic')

    rel_eventos     = relationship("Eventos",
                                    cascade="all, delete-orphan", lazy='dynamic')

    rel_relaciones  = relationship("Relaciones",
                                    foreign_keys="Relaciones.PersonaId",
                                    cascade="all, delete-orphan", lazy='dynamic')

    rel_contactos   = relationship("Contactos",
                                    cascade="all, delete-orphan", lazy='dynamic')

    def __repr__(self):
        return f'<Personas {self.id}: {self.nombre}>'



class Rel_persona_etiqueta(db.Model):
    """Relación persona ↔ etiqueta con auditoría"""
    __tablename__ = 'rel_persona_etiqueta'
    id           = Column(Integer, primary_key=True)
    EtiquetaId   = Column(Integer, ForeignKey('etiquetas.id'), nullable=False)
    PersonaId    = Column(Integer, ForeignKey('personas.id'), nullable=False)
    usuario_alta = Column(String(100), nullable=False)
    fecha_alta   = Column(DateTime, nullable=False, default=datetime.now)
    usuario_mod  = Column(String(100))
    fecha_mod    = Column(DateTime)
    usuario_baja = Column(String(100))
    fecha_baja   = Column(DateTime)

    def __repr__(self):
        return f'<Rel_persona_etiqueta persona={self.PersonaId} eti={self.EtiquetaId}>'



class Eventos(db.Model):
    """Eventos de una persona (cumpleaños, aniversarios, etc.) con auditoría.
    
    El campo TiposValoresId referencia la tabla tipos_valores, cuyo TipoId
    debe apuntar siempre al registro de la tabla tipos con nombre 'Eventos'.
    """
    __tablename__    = 'eventos'
    # __table_args__   = {'extend_existing': True}
    id               = Column(Integer, primary_key=True)
    PersonaId        = Column(Integer, ForeignKey('personas.id'), nullable=False)
    TiposValoresId   = Column(Integer, ForeignKey('tipos_valores.id'), nullable=False)
    fecha            = Column(Date, nullable=False)

    usuario_alta     = Column(String(100), nullable=False)
    fecha_alta       = Column(DateTime, nullable=False, default=datetime.now)
    usuario_mod      = Column(String(100))
    fecha_mod        = Column(DateTime)
    usuario_baja     = Column(String(100))
    fecha_baja       = Column(DateTime)

    # Relación de consulta hacia TiposValores (para obtener el nombre del evento)
    tipo_valor       = relationship("TiposValores", lazy='joined')

    def __repr__(self):
        return f'<Eventos persona={self.PersonaId} tipo={self.TiposValoresId} fecha={self.fecha}>'



class Relaciones(db.Model):
    """Relaciones entre personas (pareja, hijo, amigo, etc.) con auditoría.

    TiposValoresId referencia tipos_valores cuyo TipoId apunta al registro
    de la tabla tipos con nombre 'Relaciones'.
    PersonaRelacionadaId es la otra persona de la relación.
    """
    __tablename__          = 'relaciones'
    id                     = Column(Integer, primary_key=True)
    PersonaId              = Column(Integer, ForeignKey('personas.id'), nullable=False)
    TiposValoresId         = Column(Integer, ForeignKey('tipos_valores.id'), nullable=False)
    PersonaRelacionadaId   = Column(Integer, ForeignKey('personas.id'), nullable=False)

    usuario_alta           = Column(String(100), nullable=False)
    fecha_alta             = Column(DateTime, nullable=False, default=datetime.now)
    usuario_mod            = Column(String(100))
    fecha_mod              = Column(DateTime)
    usuario_baja           = Column(String(100))
    fecha_baja             = Column(DateTime)

    tipo_valor             = relationship("TiposValores", lazy='joined')
    persona_relacionada    = relationship("Personas",
                                          foreign_keys=[PersonaRelacionadaId],
                                          lazy='joined')

    def __repr__(self):
        return (f'<Relaciones persona={self.PersonaId} '
                f'tipo={self.TiposValoresId} '
                f'con={self.PersonaRelacionadaId}>')



class Contactos(db.Model):
    """Datos de contacto de una persona (teléfono, email, web, etc.) con auditoría.

    TipoContactoId  → TiposValores cuyo TipoId apunta al Tipos con nombre 'Contacto'
                      (Teléfono, Email, Dirección, Web, …)
    TipoLugarId     → TiposValores cuyo TipoId apunta al Tipos con nombre 'Lugar Contacto'
                      (Personal, Casa, Trabajo, Móvil, WhatsApp, …)
    valor           → el dato en sí (número, dirección, URL, …)
    """
    __tablename__    = 'contactos'
    id               = Column(Integer, primary_key=True)
    PersonaId        = Column(Integer, ForeignKey('personas.id'),      nullable=False)
    TipoContactoId   = Column(Integer, ForeignKey('tipos_valores.id'), nullable=False)
    TipoLugarId      = Column(Integer, ForeignKey('tipos_valores.id'), nullable=False)
    valor            = Column(String(255), nullable=False)

    usuario_alta     = Column(String(100), nullable=False)
    fecha_alta       = Column(DateTime, nullable=False, default=datetime.now)
    usuario_mod      = Column(String(100))
    fecha_mod        = Column(DateTime)
    usuario_baja     = Column(String(100))
    fecha_baja       = Column(DateTime)

    tipo_contacto    = relationship("TiposValores",
                                    foreign_keys=[TipoContactoId], lazy='joined')
    tipo_lugar       = relationship("TiposValores",
                                    foreign_keys=[TipoLugarId],    lazy='joined')

    def __repr__(self):
        return (f'<Contactos persona={self.PersonaId} '
                f'tipo={self.TipoContactoId} lugar={self.TipoLugarId} '
                f'valor={self.valor!r}>')
