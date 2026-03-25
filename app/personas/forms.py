from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Optional





class formContacto(FlaskForm):                      
	apodo 		= StringField("Apodo:", validators=[DataRequired("Tienes que introducir el dato")])
	nombre 		= StringField("Nombre:", validators=[Optional()])
	notas 		= TextAreaField("Notas:")
	Etiquetas 	= SelectMultipleField("Etiquetas:", validators=[Optional()], choices=[])
	submit 		= SubmitField('Enviar')



class formImportar(FlaskForm):
	submit = SubmitField('Importar')



class formEtiqueta(FlaskForm):                      
	nombre = StringField("Etiqueta:", validators=[DataRequired("Tienes que introducir el dato")])
	submit = SubmitField('Enviar')



class formSINO(FlaskForm):      
	si = SubmitField('Si') 
	no = SubmitField('No') 
