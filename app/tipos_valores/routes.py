import unicodedata
from flask import render_template, redirect, url_for, abort, request
from flask_login import login_required, current_user

from app.app import app, db
from .models import Tipos, TiposValores


def sin_tildes(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()


# ─── LISTA TIPOS ───────────────────────────────────────────────────────────────
@app.route('/tipos/')
@login_required
def tipos():
    f_nombre = request.args.get('nombre', '').strip()
    f_desc   = request.args.get('descripcion', '').strip()

    tipos_list = Tipos.query.order_by(Tipos.nombre.asc()).all()

    if f_nombre:
        busq = sin_tildes(f_nombre)
        tipos_list = [t for t in tipos_list if busq in sin_tildes(t.nombre or '')]
    if f_desc:
        busq = sin_tildes(f_desc)
        tipos_list = [t for t in tipos_list if busq in sin_tildes(t.descripcion or '')]

    tipo_sel_id = request.args.get('tipo_sel', type=int)
    tipo_sel    = None
    valores     = []
    f_valor     = request.args.get('valor', '').strip()

    if tipo_sel_id:
        tipo_sel = Tipos.query.get(tipo_sel_id)
        if tipo_sel:
            valores = TiposValores.query.filter_by(TipoId=tipo_sel_id)\
                                        .order_by(TiposValores.nombre.asc()).all()
            if f_valor:
                busq = sin_tildes(f_valor)
                valores = [v for v in valores if busq in sin_tildes(v.nombre or '')]

    return render_template(
        "tipos_valores/tipos.html",
        tipos=tipos_list,
        tipo_sel=tipo_sel,
        tipo_sel_id=tipo_sel_id,
        valores=valores,
    )


# ─── NUEVO / EDITAR TIPO ───────────────────────────────────────────────────────
@app.route('/tipo/new', methods=['GET', 'POST'])
@app.route('/tipo/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def tipo_edit(id=None):
    if not current_user.is_admin():
        abort(404)

    if id is None:
        tipo = Tipos()
    else:
        tipo = Tipos.query.get(id)
        if tipo is None:
            abort(404)

    if request.method == 'POST':
        nombre      = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        if nombre:
            tipo.nombre      = nombre
            tipo.descripcion = descripcion
            if id is None:
                db.session.add(tipo)
            db.session.commit()
        return redirect(url_for('tipos'))

    return redirect(url_for('tipos'))


# ─── BORRAR TIPO ───────────────────────────────────────────────────────────────
@app.route('/tipo/<int:id>/delete', methods=['POST'])
@login_required
def tipo_delete(id):
    if not current_user.is_admin():
        abort(404)
    tipo = Tipos.query.get(id)
    if tipo is None:
        abort(404)
    db.session.delete(tipo)
    db.session.commit()
    return redirect(url_for('tipos'))


# ─── NUEVO / EDITAR VALOR ──────────────────────────────────────────────────────
@app.route('/tipo/<int:tipo_id>/valor/new', methods=['POST'])
@app.route('/tipo/<int:tipo_id>/valor/<int:id>/edit', methods=['POST'])
@login_required
def tipo_valor_edit(tipo_id, id=None):
    if not current_user.is_admin():
        abort(404)
    tipo = Tipos.query.get(tipo_id)
    if tipo is None:
        abort(404)

    if id is None:
        valor = TiposValores(TipoId=tipo_id)
    else:
        valor = TiposValores.query.get(id)
        if valor is None or valor.TipoId != tipo_id:
            abort(404)

    nombre = request.form.get('nombre', '').strip()
    if nombre:
        valor.nombre = nombre
        if id is None:
            db.session.add(valor)
        db.session.commit()

    return redirect(url_for('tipos', tipo_sel=tipo_id))


# ─── BORRAR VALOR ──────────────────────────────────────────────────────────────
@app.route('/tipo/<int:tipo_id>/valor/<int:id>/delete', methods=['POST'])
@login_required
def tipo_valor_delete(tipo_id, id):
    if not current_user.is_admin():
        abort(404)
    valor = TiposValores.query.get(id)
    if valor is None or valor.TipoId != tipo_id:
        abort(404)
    db.session.delete(valor)
    db.session.commit()
    return redirect(url_for('tipos', tipo_sel=tipo_id))
