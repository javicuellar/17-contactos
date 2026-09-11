from sqlalchemy import Column 
from sqlalchemy import Integer, String

from app.app import db






class Etiquetas(db.Model):
	"""Etiquetas de los contactos"""
	__tablename__ = 'etiquetas'
	id 			= Column(Integer, primary_key=True)
	nombre 		= Column(String(100))
	descripcion = Column(String(255))

	def __repr__(self):
		return (u'<{self.__class__.__name__}: {self.id}>'.format(self=self))
