from flask import render_template, redirect, url_for, request, abort, jsonify
from flask_login import login_user, logout_user, current_user, login_required

from app.app import app, db, login_manager
from .models import Usuarios
from .forms import LoginForm, formUsuario, formSINO





@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))



@app.route('/', methods=['get', 'post'])
@app.route('/login', methods=['get', 'post'])
def login():
	# Control de permisos
	if current_user.is_authenticated:
		return redirect(url_for("personas"))

	form = LoginForm()
	if form.validate_on_submit():
		user=Usuarios.query.filter_by(usuario=form.usuario.data).first()
		if user!=None and user.verify_password(form.password.data):
			login_user(user)
			next = request.args.get('next')
			return redirect(next or url_for('personas'))
		form.usuario.errors.append("Usuario o contraseña incorrectas.")
	return render_template('usuarios/login.html', form=form)



@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('login'))



@app.route("/registro",methods=["get","post"])
def registro():
	# Control de permisos
	if current_user.is_authenticated:
		return redirect(url_for("personas"))

	form=formUsuario()
	if form.validate_on_submit():
		existe_usuario=Usuarios.query.filter_by(usuario=form.usuario.data).first()
		if existe_usuario==None:
			user=Usuarios()
			form.populate_obj(user)
			user.admin=False
			db.session.add(user)
			db.session.commit()
			return redirect(url_for("personas"))
		form.usuario.errors.append("Nombre de usuario ya existe.")
	return render_template("usuarios/registro.html",form=form)


@app.route('/perfil/editar', methods=['POST'])
@login_required
def perfil_editar():
	usuario = request.form.get('usuario', '').strip()
	nombre   = request.form.get('nombre', '').strip()
	email    = request.form.get('email', '').strip()
	pwd      = request.form.get('password', '').strip()
	if usuario:
		current_user.usuario = usuario
	current_user.nombre = nombre
	current_user.email  = email
	if pwd:
		current_user.password = pwd
	db.session.commit()
	return redirect(request.referrer or url_for('personas'))


@app.route('/usuarios/', methods=['GET'])
@login_required
def usuarios_list():
	if not current_user.is_admin():
		abort(403)
	f_usuario = request.args.get('usuario', '').strip().lower()
	f_nombre   = request.args.get('nombre', '').strip().lower()
	usuarios = Usuarios.query.order_by(Usuarios.usuario.asc()).all()
	if f_usuario:
		usuarios = [u for u in usuarios if f_usuario in u.usuario.lower()]
	if f_nombre:
		usuarios = [u for u in usuarios if f_nombre in (u.nombre or '').lower()]
	return render_template('usuarios/usuarios_list.html', usuarios=usuarios)


@app.route('/usuarios/new', methods=['POST'])
@login_required
def usuarios_new():
	if not current_user.is_admin():
		abort(403)
	usuario = request.form.get('usuario','').strip()
	nombre   = request.form.get('nombre','').strip()
	email    = request.form.get('email','').strip()
	password = request.form.get('password','').strip()
	if usuario and password:
		existe = Usuarios.query.filter_by(usuario=usuario).first()
		if not existe:
			user = Usuarios()
			user.usuario  = usuario
			user.nombre   = nombre
			user.email    = email
			user.password = password
			user.admin    = 'admin' in request.form
			db.session.add(user)
			db.session.commit()
	return redirect(url_for('usuarios_list'))


@app.route('/usuarios/<int:uid>/edit', methods=['POST'])
@login_required
def usuarios_edit(uid):
	if not current_user.is_admin():
		abort(403)
	user = Usuarios.query.get_or_404(uid)
	usuario = request.form.get('usuario','').strip()
	if usuario:
		user.usuario = usuario
	user.nombre = request.form.get('nombre', user.nombre or '')
	user.email  = request.form.get('email',  user.email  or '')
	pwd = request.form.get('password','').strip()
	if pwd:
		user.password = pwd
	user.admin = 'admin' in request.form
	db.session.commit()
	return redirect(url_for('usuarios_list'))


@app.route('/usuarios/<int:uid>/delete', methods=['POST'])
@login_required
def usuarios_delete(uid):
	if not current_user.is_admin():
		abort(403)
	if uid != current_user.id:
		user = Usuarios.query.get_or_404(uid)
		db.session.delete(user)
		db.session.commit()
	return redirect(url_for('usuarios_list'))
