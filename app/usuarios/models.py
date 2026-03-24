from sqlalchemy import Boolean, Column
from sqlalchemy import Integer, String
from werkzeug.security import generate_password_hash, check_password_hash

from app.app import db




class Usuarios(db.Model):
	"""Usuarios"""
	__tablename__ = 'usuarios'
	id = Column(Integer, primary_key=True)
	username = Column(String(100),nullable=False)
	password_hash = Column(String(128),nullable=False)
	nombre = Column(String(200),nullable=False)
	email = Column(String(200),nullable=False)
	admin = Column(Boolean, default=False)


	def __repr__(self):
		return (u'<{self.__class__.__name__}: {self.id}>'.format(self=self))

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

 	
# Flask-Login integration
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return str(self.id)

	def is_admin(self):
		return self.admin
