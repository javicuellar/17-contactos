from flask import render_template, redirect, url_for, abort, request
import unicodedata
from flask_login import login_required, current_user

from app.app import app, db
from .models import Etiquetas
from .forms import formEtiqueta, formSINO
from app.contactos.models import Rel_contacto_etiqueta






@app.route('/etiquetas/')
@login_required
def etiquetas(id='0'):
	# Filtros desde querystring (GET)
	f_nombre = request.args.get('nombre', '').strip()
	f_desc   = request.args.get('descripcion', '').strip()

	def sin_tildes(s):
		return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()

	etiquetas = Etiquetas.query.order_by(Etiquetas.nombre.asc()).all()

	if f_nombre:
		busq = sin_tildes(f_nombre)
		etiquetas = [e for e in etiquetas if busq in sin_tildes(e.nombre or '')]
	if f_desc:
		busq = sin_tildes(f_desc)
		etiquetas = [e for e in etiquetas if busq in sin_tildes(e.descripcion or '')]

	# Añadir número de contactos por etiqueta para el modal de borrado
	for eti in etiquetas:
		eti.num_contactos = Rel_contacto_etiqueta.query.filter_by(EtiquetaId=eti.id).count()

	return render_template("etiquetas/etiquetas.html", etiquetas=etiquetas)



@app.route('/etiqueta/new', methods=["get","post"])
@app.route('/etiqueta/<id>/edit', methods=["get","post"])
@login_required
def etiqueta_edit(id=None):
	# Control de permisos
	if not current_user.is_admin():
		abort(404)

	if id is None:
		form= formEtiqueta()
		eti = Etiquetas()
	else:
		eti = Etiquetas.query.get(id)
		if eti is None:
			abort(404)

		form= formEtiqueta(obj=eti)
	
	if form.validate_on_submit():
		form.populate_obj(eti)

		if id is None:
			db.session.add(eti)
		db.session.commit()
		
		return redirect(url_for("etiquetas"))
	
	return render_template("etiquetas/etiqueta_new.html",form=form, id=id)



@app.route('/etiqueta/<id>/delete', methods=["get","post"])
@login_required
def etiqueta_delete(id):
	if not current_user.is_admin():
		abort(404)

	eti = Etiquetas.query.get(id)
	if eti is None:
		abort(404)

	if request.method == 'POST':
		db.session.delete(eti)
		db.session.commit()
		return redirect(url_for("etiquetas"))

	num_contactos = Rel_contacto_etiqueta.query.filter_by(EtiquetaId=id).count()
	form = formSINO()
	return render_template("etiquetas/etiqueta_delete.html", form=form, eti=eti, num_contactos=num_contactos)
