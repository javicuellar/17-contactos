from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.app import db






class Tipos(db.Model):
	"""Tipos de valores para los campos de la aplicación"""
	__tablename__ = 'tipos'
	id 			= Column(Integer, primary_key=True)
	nombre 		= Column(String(100))
	descripcion = Column(String(255))

	rel_tipos_valores = relationship("TiposValores",
                                      cascade="all, delete-orphan", lazy='dynamic')
	
	def __repr__(self):
		return (u'<{self.__class__.__name__}: {self.id}>'.format(self=self))



class TiposValores(db.Model):
	"""Valores para los campos de la aplicación"""
	__tablename__ = 'tipos_valores'
	id 			= Column(Integer, primary_key=True)
	TipoId      = Column(Integer, ForeignKey('tipos.id'), nullable=False)
	nombre 		= Column(String(100))

	def __repr__(self):
		return (u'<{self.__class__.__name__}: {self.id}>'.format(self=self))
