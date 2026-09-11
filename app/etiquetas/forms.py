from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired






class formEtiqueta(FlaskForm):                      
	nombre 		= StringField("Etiqueta:", validators=[DataRequired("Tienes que introducir el dato")])
	descripcion	= StringField("Descripción:", validators=[DataRequired("Tienes que introducir el dato")])
	submit 		= SubmitField('Enviar')



class formSINO(FlaskForm):      
	si = SubmitField('Si') 
	no = SubmitField('No') 
