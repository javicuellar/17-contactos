from sqlalchemy import Column, ForeignKey, DateTime
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
    rel_etiquetas = relationship("Rel_persona_etiqueta",
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
