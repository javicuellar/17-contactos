from flask import render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from datetime import datetime
import unicodedata

from app.app import app, db
from .models import Personas, Rel_persona_etiqueta
from .forms import formImportar
from app.etiquetas.models import Etiquetas
from app.comunes.utilidades import procesar_archivo


def sin_tildes(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()


# ── LISTA DE PERSONAS (solo las del usuario logado) ──────────────────────────
@app.route('/contactos/')
@login_required
def contactos():
    etiquetas = Etiquetas.query.order_by(Etiquetas.nombre.asc()).all()

    f_nombre   = request.args.get('nombre', '').strip()
    f_etiqueta = request.args.get('etiqueta_id', '').strip()

    # Solo personas del usuario logado, sin fecha de baja
    query = Personas.query.filter_by(UsuarioId=current_user.id)\
                          .filter(Personas.fecha_baja == None)

    if f_etiqueta:
        ids = [r.PersonaId for r in
               Rel_persona_etiqueta.query.filter_by(EtiquetaId=f_etiqueta)
               .filter(Rel_persona_etiqueta.fecha_baja == None).all()]
        query = query.filter(Personas.id.in_(ids))

    personas = query.order_by(Personas.nombre.asc()).all()

    if f_nombre:
        busq = sin_tildes(f_nombre)
        personas = [p for p in personas if busq in sin_tildes(p.nombre or '')]

    # Resolver etiquetas activas de cada persona
    for p in personas:
        rels = Rel_persona_etiqueta.query\
               .filter_by(PersonaId=p.id)\
               .filter(Rel_persona_etiqueta.fecha_baja == None).all()
        p.etiquetas_obj = [Etiquetas.query.get(r.EtiquetaId)
                           for r in rels if Etiquetas.query.get(r.EtiquetaId)]

    filtro_qs = request.query_string.decode('utf-8')
    return render_template('contactos/contactos.html',
                           contactos=personas,
                           etiquetas=etiquetas,
                           etiqueta=None,
                           filtro_qs=filtro_qs)


# ── ALTA ─────────────────────────────────────────────────────────────────────
@app.route('/contactos/new', methods=['post'])
@login_required
def contactos_new():
    nombre  = request.form.get('nombre', '').strip()
    notas   = request.form.get('notas', '').strip()
    eti_ids = request.form.getlist('Etiquetas')

    if nombre:
        now = datetime.now()
        p = Personas()
        p.UsuarioId    = current_user.id
        p.nombre       = nombre
        p.notas        = notas
        p.usuario_alta = current_user.username
        p.fecha_alta   = now
        db.session.add(p)
        db.session.flush()   # obtener p.id antes de commit

        for eti_id in eti_ids:
            try:
                eid = int(eti_id)
                if eid:
                    rel = Rel_persona_etiqueta()
                    rel.PersonaId    = p.id
                    rel.EtiquetaId   = eid
                    rel.usuario_alta = current_user.username
                    rel.fecha_alta   = now
                    db.session.add(rel)
            except ValueError:
                pass
        db.session.commit()

    filtro_qs = request.args.get('filtro_qs', '')
    return redirect(url_for('contactos') + ('?' + filtro_qs if filtro_qs else ''))


# ── EDICIÓN ───────────────────────────────────────────────────────────────────
@app.route('/contactos/<int:id>/edit', methods=['post'])
@login_required
def contactos_edit(id):
    p = Personas.query.get_or_404(id)
    if p.UsuarioId != current_user.id and not current_user.is_admin():
        abort(403)

    now = datetime.now()
    p.nombre      = request.form.get('nombre', p.nombre).strip()
    p.notas       = request.form.get('notas', '').strip()
    p.usuario_mod = current_user.username
    p.fecha_mod   = now

    # Dar de baja etiquetas anteriores y crear las nuevas
    rels_activas = Rel_persona_etiqueta.query\
                   .filter_by(PersonaId=id)\
                   .filter(Rel_persona_etiqueta.fecha_baja == None).all()
    for rel in rels_activas:
        rel.usuario_baja = current_user.username
        rel.fecha_baja   = now

    for eti_id in request.form.getlist('Etiquetas'):
        try:
            eid = int(eti_id)
            if eid:
                rel = Rel_persona_etiqueta()
                rel.PersonaId    = p.id
                rel.EtiquetaId   = eid
                rel.usuario_alta = current_user.username
                rel.fecha_alta   = now
                db.session.add(rel)
        except ValueError:
            pass

    db.session.commit()

    filtro_qs = request.args.get('filtro_qs', '')
    return redirect(url_for('contactos') + ('?' + filtro_qs if filtro_qs else ''))


# ── BAJA LÓGICA ───────────────────────────────────────────────────────────────
@app.route('/contactos/<int:id>/delete', methods=['post'])
@login_required
def contactos_delete(id):
    p = Personas.query.get_or_404(id)
    if p.UsuarioId != current_user.id and not current_user.is_admin():
        abort(403)

    now = datetime.now()
    p.usuario_baja = current_user.username
    p.fecha_baja   = now

    # Baja lógica en relaciones
    rels = Rel_persona_etiqueta.query\
           .filter_by(PersonaId=id)\
           .filter(Rel_persona_etiqueta.fecha_baja == None).all()
    for rel in rels:
        rel.usuario_baja = current_user.username
        rel.fecha_baja   = now

    db.session.commit()

    filtro_qs = request.args.get('filtro_qs', '')
    return redirect(url_for('contactos') + ('?' + filtro_qs if filtro_qs else ''))


# ── IMPORTAR CSV ──────────────────────────────────────────────────────────────
@app.route('/importar', methods=['GET', 'POST'])
@login_required
def importar():
    form = formImportar()
    resultado = None

    if form.validate_on_submit():
        archivo = request.files.get('archivo')
        if not archivo or archivo.filename == '':
            resultado = {'error': 'No se ha seleccionado ningún archivo.'}
        else:
            contactos_csv = procesar_archivo(archivo)
            nuevos, actualizados, errores = 0, 0, []
            now = datetime.now()

            for contacto in contactos_csv:
                if 'nombre' not in contacto:
                    continue
                try:
                    nombre_completo = contacto['nombre'].strip()
                    sufijo = contacto.get('sufijo_nombre', '').strip()
                    if sufijo:
                        nombre_completo = (nombre_completo + ' ' + sufijo).strip()

                    # Buscar persona existente del usuario actual
                    persona = Personas.query\
                              .filter_by(UsuarioId=current_user.id,
                                         nombre=nombre_completo)\
                              .filter(Personas.fecha_baja == None).first()

                    if persona is None:
                        persona = Personas()
                        persona.UsuarioId    = current_user.id
                        persona.nombre       = nombre_completo
                        persona.notas        = contacto.get('notas', '')
                        persona.usuario_alta = current_user.username
                        persona.fecha_alta   = now
                        db.session.add(persona)
                        db.session.flush()
                        nuevos += 1
                    else:
                        if contacto.get('notas'):
                            persona.notas = contacto['notas']
                        persona.usuario_mod = current_user.username
                        persona.fecha_mod   = now
                        actualizados += 1

                        # Dar de baja relaciones anteriores
                        rels = Rel_persona_etiqueta.query\
                               .filter_by(PersonaId=persona.id)\
                               .filter(Rel_persona_etiqueta.fecha_baja == None).all()
                        for rel in rels:
                            rel.usuario_baja = current_user.username
                            rel.fecha_baja   = now

                    # Asignar etiquetas
                    if 'etiquetas' in contacto:
                        for nombre_eti in contacto['etiquetas']:
                            eti = Etiquetas.query\
                                  .filter_by(nombre=nombre_eti).first()
                            if eti is None:
                                eti = Etiquetas()
                                eti.nombre      = nombre_eti
                                eti.descripcion = ''
                                db.session.add(eti)
                                db.session.flush()

                            rel = Rel_persona_etiqueta()
                            rel.PersonaId    = persona.id
                            rel.EtiquetaId   = eti.id
                            rel.usuario_alta = current_user.username
                            rel.fecha_alta   = now
                            db.session.add(rel)

                    db.session.commit()

                except Exception as e:
                    errores.append(f"{contacto.get('nombre','?')}: {str(e)}")
                    db.session.rollback()

            resultado = {'nuevos': nuevos, 'actualizados': actualizados,
                         'errores': errores}

    return render_template('contactos/importar.html', form=form, resultado=resultado)
