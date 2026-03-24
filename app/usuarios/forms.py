from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired






class LoginForm(FlaskForm):
	username = StringField('Login', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	submit 	 = SubmitField('Entrar')


class formUsuario(FlaskForm):
	username = StringField('Login', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	nombre   = StringField('Nombre completo')
	email    = EmailField('Email')
	submit   = SubmitField('Aceptar')	


class formChangePassword(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	submit   = SubmitField('Aceptar')	


class formSINO(FlaskForm):
	si = SubmitField('Si')
	no = SubmitField('No')
