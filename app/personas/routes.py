from flask import render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from datetime import datetime
import unicodedata

from app.app import app, db
from .models import Personas, Rel_persona_etiqueta, Eventos, Relaciones, Contactos
from .forms import formImportar
from app.etiquetas.models import Etiquetas
from app.tipos_valores.models import Tipos, TiposValores
from app.comunes.utilidades import procesar_archivo, normalizar_telefono
from app.comunes.logger import get_logger

log = get_logger('personas.routes')




def sin_tildes(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()


# ── LISTA DE PERSONAS (solo las del usuario logado) ──────────────────────────
@app.route('/personas/')
@login_required
def personas():
    etiquetas = Etiquetas.query.order_by(Etiquetas.nombre.asc()).all()

    f_apodo    = request.args.get('apodo', '').strip()
    f_etiqueta = request.args.get('etiqueta_id', '').strip()
    f_contacto = request.args.get('contacto', '').strip()

    # Solo personas del usuario logado, sin fecha de baja
    query = Personas.query.filter_by(UsuarioId=current_user.id)\
                          .filter(Personas.fecha_baja == None)

    if f_etiqueta == '__sin_etiqueta__':
        # Personas que NO tienen ninguna relación de etiqueta activa
        con_etiqueta_ids = [r.PersonaId for r in
                            Rel_persona_etiqueta.query
                            .filter(Rel_persona_etiqueta.fecha_baja == None).all()]
        query = query.filter(Personas.id.notin_(con_etiqueta_ids))
    elif f_etiqueta:
        ids = [r.PersonaId for r in
               Rel_persona_etiqueta.query.filter_by(EtiquetaId=f_etiqueta)
               .filter(Rel_persona_etiqueta.fecha_baja == None).all()]
        query = query.filter(Personas.id.in_(ids))

    personas = query.order_by(Personas.apodo.asc()).all()

    if f_apodo:
        busq = sin_tildes(f_apodo)
        personas = [p for p in personas
                    if busq in sin_tildes(p.apodo or '')
                    or busq in sin_tildes(p.nombre or '')
                    or busq in sin_tildes(p.notas or '')]

    if f_contacto:
        import re as _re
        # Si el término parece un número (solo dígitos y separadores), quitamos
        # los espacios para buscar contra el valor guardado sin espacios.
        # Si es alfanumérico, buscamos tal cual (sin tildes) como subcadena.
        if _re.fullmatch(r'[\d\s\+\-\(\)\.]+', f_contacto):
            busq = _re.sub(r'\D', '', f_contacto)   # solo dígitos
        else:
            busq = sin_tildes(f_contacto)
        contactos_ids = {c.PersonaId for c in
                         Contactos.query.filter(Contactos.fecha_baja == None).all()
                         if busq in sin_tildes(c.valor or '')}
        personas = [p for p in personas if p.id in contactos_ids]

    # Resolver etiquetas activas de cada persona
    for p in personas:
        rels = Rel_persona_etiqueta.query\
               .filter_by(PersonaId=p.id)\
               .filter(Rel_persona_etiqueta.fecha_baja == None).all()
        p.etiquetas_obj = [Etiquetas.query.get(r.EtiquetaId)
                           for r in rels if Etiquetas.query.get(r.EtiquetaId)]

    # Resolver eventos activos de cada persona (resumen texto + JSON para modal)
    import json
    for p in personas:
        eventos_activos = Eventos.query\
               .filter_by(PersonaId=p.id)\
               .filter(Eventos.fecha_baja == None).all()
        p.eventos_resumen = ', '.join(
            f"{ev.tipo_valor.nombre} {ev.fecha.strftime('%d/%m/%Y')}"
            for ev in eventos_activos
            if ev.tipo_valor
        )
        p.eventos_json = json.dumps([
            {'id': ev.id,
             'TiposValoresId': ev.TiposValoresId,
             'fecha': ev.fecha.strftime('%Y-%m-%d')}
            for ev in eventos_activos
        ])

    # Resolver relaciones activas de cada persona (JSON para modal)
    for p in personas:
        relaciones_activas = Relaciones.query\
               .filter_by(PersonaId=p.id)\
               .filter(Relaciones.fecha_baja == None).all()
        p.relaciones_json = json.dumps([
            {'id': r.id,
             'TiposValoresId': r.TiposValoresId,
             'PersonaRelacionadaId': r.PersonaRelacionadaId}
            for r in relaciones_activas
        ])

    # Resolver contactos activos de cada persona (JSON para modal + lista para tabla)
    for p in personas:
        contactos_activos = Contactos.query\
               .filter_by(PersonaId=p.id)\
               .filter(Contactos.fecha_baja == None).all()
        p.contactos_json = json.dumps([
            {'id': c.id,
             'TipoContactoId': c.TipoContactoId,
             'TipoLugarId':    c.TipoLugarId,
             'valor':          c.valor}
            for c in contactos_activos
        ])
        # Lista con nombres resueltos para mostrar en la columna de la tabla
        p.contactos_lista = []
        for c in contactos_activos:
            tv_tipo  = TiposValores.query.get(c.TipoContactoId)
            tv_lugar = TiposValores.query.get(c.TipoLugarId)
            nombre_tipo  = tv_tipo.nombre  if tv_tipo  else ''
            nombre_lugar = tv_lugar.nombre if tv_lugar else ''
            # Formatear teléfonos para mostrar
            from app.comunes.utilidades import formatear_telefono
            valor_display = formatear_telefono(c.valor) if nombre_tipo == 'Teléfono' else c.valor
            p.contactos_lista.append({
                'tipo':  nombre_tipo,
                'lugar': nombre_lugar,
                'valor': valor_display,
            })

    filtro_qs = request.query_string.decode('utf-8')

    # TiposValores para el select de eventos
    tipo_eventos = Tipos.query.filter_by(nombre='Eventos').first()
    tipos_valores_eventos = []
    if tipo_eventos:
        tipos_valores_eventos = TiposValores.query\
            .filter_by(TipoId=tipo_eventos.id)\
            .order_by(TiposValores.nombre.asc()).all()

    # TiposValores para el select de relaciones
    tipo_relaciones = Tipos.query.filter_by(nombre='Relaciones').first()
    tipos_valores_relaciones = []
    if tipo_relaciones:
        tipos_valores_relaciones = TiposValores.query\
            .filter_by(TipoId=tipo_relaciones.id)\
            .order_by(TiposValores.nombre.asc()).all()

    # TiposValores para los selectores de contactos
    tipo_contacto_t = Tipos.query.filter_by(nombre='Contacto').first()
    tipos_valores_contacto = []
    if tipo_contacto_t:
        tipos_valores_contacto = TiposValores.query\
            .filter_by(TipoId=tipo_contacto_t.id)\
            .order_by(TiposValores.nombre.asc()).all()

    tipo_lugar_t = Tipos.query.filter_by(nombre='Lugar Contacto').first()
    tipos_valores_lugar = []
    if tipo_lugar_t:
        tipos_valores_lugar = TiposValores.query\
            .filter_by(TipoId=tipo_lugar_t.id)\
            .order_by(TiposValores.nombre.asc()).all()

    # Lista de todas las personas del usuario (select persona relacionada)
    todas_personas = Personas.query\
        .filter_by(UsuarioId=current_user.id)\
        .filter(Personas.fecha_baja == None)\
        .order_by(Personas.apodo.asc()).all()

    return render_template('personas/personas.html',
                           personas=personas,
                           etiquetas=etiquetas,
                           etiqueta=None,
                           tipos_valores_eventos=tipos_valores_eventos,
                           tipos_valores_relaciones=tipos_valores_relaciones,
                           tipos_valores_contacto=tipos_valores_contacto,
                           tipos_valores_lugar=tipos_valores_lugar,
                           todas_personas=todas_personas,
                           filtro_qs=filtro_qs)


# ── ALTA ─────────────────────────────────────────────────────────────────────
@app.route('/personas/new', methods=['post'])
@login_required
def personas_new():
    apodo   = request.form.get('apodo', '').strip()
    nombre  = request.form.get('nombre', '').strip()
    notas   = request.form.get('notas', '').strip()
    eti_ids = request.form.getlist('Etiquetas')

    if apodo:
        now = datetime.now()
        log.info('ALTA persona: apodo=%r nombre=%r usuario=%s',
                 apodo, nombre, current_user.usuario)
        p = Personas()
        p.UsuarioId    = current_user.id
        p.apodo        = apodo
        p.nombre       = nombre or apodo   # nombre nunca puede ser NULL
        p.notas        = notas
        p.usuario_alta = current_user.usuario
        p.fecha_alta   = now
        db.session.add(p)
        db.session.flush()

        for eti_id in eti_ids:
            try:
                eid = int(eti_id)
                if eid:
                    rel = Rel_persona_etiqueta()
                    rel.PersonaId    = p.id
                    rel.EtiquetaId   = eid
                    rel.usuario_alta = current_user.usuario
                    rel.fecha_alta   = now
                    db.session.add(rel)
            except ValueError:
                pass

        # Procesar eventos del formulario
        ev_tipos  = request.form.getlist('evento_tipo[]')
        ev_fechas = request.form.getlist('evento_fecha[]')
        for tv_id, fecha_str in zip(ev_tipos, ev_fechas):
            try:
                tv_id_int = int(tv_id)
                fecha_ev  = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                if tv_id_int and fecha_str:
                    ev = Eventos()
                    ev.PersonaId      = p.id
                    ev.TiposValoresId = tv_id_int
                    ev.fecha          = fecha_ev
                    ev.usuario_alta   = current_user.usuario
                    ev.fecha_alta     = now
                    db.session.add(ev)
            except (ValueError, TypeError):
                pass

        # Procesar relaciones del formulario
        rel_tipos    = request.form.getlist('relacion_tipo[]')
        rel_personas = request.form.getlist('relacion_persona[]')
        for tv_id, per_id in zip(rel_tipos, rel_personas):
            try:
                tv_id_int  = int(tv_id)
                per_id_int = int(per_id)
                if tv_id_int and per_id_int:
                    rel = Relaciones()
                    rel.PersonaId            = p.id
                    rel.TiposValoresId       = tv_id_int
                    rel.PersonaRelacionadaId = per_id_int
                    rel.usuario_alta         = current_user.usuario
                    rel.fecha_alta           = now
                    db.session.add(rel)
            except (ValueError, TypeError):
                pass

        # Procesar contactos del formulario
        con_tipos  = request.form.getlist('contacto_tipo[]')
        con_lugares = request.form.getlist('contacto_lugar[]')
        con_valores = request.form.getlist('contacto_valor[]')
        for tc_id, tl_id, valor in zip(con_tipos, con_lugares, con_valores):
            try:
                tc_id_int = int(tc_id)
                tl_id_int = int(tl_id)
                valor = valor.strip()
                if tc_id_int and tl_id_int and valor:
                    # Normalizar teléfonos: guardar sin espacios
                    tv = TiposValores.query.get(tc_id_int)
                    if tv and tv.nombre == 'Teléfono':
                        valor = normalizar_telefono(valor)
                    con = Contactos()
                    con.PersonaId      = p.id
                    con.TipoContactoId = tc_id_int
                    con.TipoLugarId    = tl_id_int
                    con.valor          = valor
                    con.usuario_alta   = current_user.usuario
                    con.fecha_alta     = now
                    db.session.add(con)
            except (ValueError, TypeError):
                pass

        db.session.commit()

    filtro_qs = request.args.get('filtro_qs', '')
    return redirect(url_for('personas') + ('?' + filtro_qs if filtro_qs else ''))


# ── EDICIÓN ───────────────────────────────────────────────────────────────────
@app.route('/personas/<int:id>/edit', methods=['post'])
@login_required
def personas_edit(id):
    p = Personas.query.get_or_404(id)
    if p.UsuarioId != current_user.id and not current_user.is_admin():
        abort(403)

    now = datetime.now()
    apodo_ant  = p.apodo
    nombre_ant = p.nombre
    notas_ant  = p.notas

    p.apodo       = request.form.get('apodo', p.apodo).strip()
    p.nombre      = request.form.get('nombre', p.nombre or '').strip() or p.apodo
    p.notas       = request.form.get('notas', '').strip()
    p.usuario_mod = current_user.usuario
    p.fecha_mod   = now

    cambios = []
    if p.apodo  != apodo_ant:  cambios.append(f'apodo: {apodo_ant!r}→{p.apodo!r}')
    if p.nombre != nombre_ant: cambios.append(f'nombre: {nombre_ant!r}→{p.nombre!r}')
    if p.notas  != notas_ant:  cambios.append(f'notas: {notas_ant!r}→{p.notas!r}')
    if cambios:
        log.info('EDICIÓN persona id=%d %r: %s', id, apodo_ant, ' | '.join(cambios))
    else:
        log.debug('EDICIÓN persona id=%d %r: sin cambios en campos principales', id, apodo_ant)

    # ── Etiquetas: baja las que desaparecen, alta las nuevas ─────────────────
    eti_ids_nuevos = set()
    for eti_id in request.form.getlist('Etiquetas'):
        try:
            eti_ids_nuevos.add(int(eti_id))
        except ValueError:
            pass

    rels_activas = Rel_persona_etiqueta.query\
                   .filter_by(PersonaId=id)\
                   .filter(Rel_persona_etiqueta.fecha_baja == None).all()
    eti_ids_actuales = {rel.EtiquetaId: rel for rel in rels_activas}

    for eid, rel in eti_ids_actuales.items():
        if eid not in eti_ids_nuevos:                  # ya no está → baja
            log.info('  etiqueta BAJA id=%d persona=%r', eid, apodo_ant)
            rel.usuario_baja = current_user.usuario
            rel.fecha_baja   = now

    for eid in eti_ids_nuevos:
        if eid not in eti_ids_actuales:                # es nueva → alta
            log.info('  etiqueta ALTA id=%d persona=%r', eid, apodo_ant)
            rel = Rel_persona_etiqueta()
            rel.PersonaId    = p.id
            rel.EtiquetaId   = eid
            rel.usuario_alta = current_user.usuario
            rel.fecha_alta   = now
            db.session.add(rel)

    # ── Eventos: UPDATE si tiene id, INSERT si no, baja si desaparece ────────
    ev_ids     = request.form.getlist('evento_id[]')
    ev_tipos   = request.form.getlist('evento_tipo[]')
    ev_fechas  = request.form.getlist('evento_fecha[]')

    ids_vistos_ev = set()
    for row_id, tv_id, fecha_str in zip(ev_ids, ev_tipos, ev_fechas):
        try:
            tv_id_int = int(tv_id)
            fecha_ev  = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            if not tv_id_int or not fecha_str:
                continue
            if row_id:                                  # fila existente → UPDATE
                ev = Eventos.query.get(int(row_id))
                if ev and ev.PersonaId == id and ev.fecha_baja is None:
                    log.debug('  evento UPDATE id=%d tipo=%s fecha=%s', ev.id, tv_id_int, fecha_ev)
                    ev.TiposValoresId = tv_id_int
                    ev.fecha          = fecha_ev
                    ev.usuario_mod    = current_user.usuario
                    ev.fecha_mod      = now
                    ids_vistos_ev.add(ev.id)
            else:                                       # fila nueva → INSERT
                log.info('  evento INSERT tipo=%s fecha=%s', tv_id_int, fecha_ev)
                ev = Eventos()
                ev.PersonaId      = p.id
                ev.TiposValoresId = tv_id_int
                ev.fecha          = fecha_ev
                ev.usuario_alta   = current_user.usuario
                ev.fecha_alta     = now
                db.session.add(ev)
                db.session.flush()          # obtener id antes del bucle de bajas
                ids_vistos_ev.add(ev.id)
        except (ValueError, TypeError):
            pass

    for ev in Eventos.query.filter_by(PersonaId=id)\
                           .filter(Eventos.fecha_baja == None).all():
        if ev.id not in ids_vistos_ev:                 # eliminada en el form → baja
            log.info('  evento BAJA id=%d', ev.id)
            ev.usuario_baja = current_user.usuario
            ev.fecha_baja   = now

    # ── Relaciones: UPDATE si tiene id, INSERT si no, baja si desaparece ─────
    rel_ids      = request.form.getlist('relacion_id[]')
    rel_tipos    = request.form.getlist('relacion_tipo[]')
    rel_personas = request.form.getlist('relacion_persona[]')

    ids_vistos_rel = set()
    for row_id, tv_id, per_id in zip(rel_ids, rel_tipos, rel_personas):
        try:
            tv_id_int  = int(tv_id)
            per_id_int = int(per_id)
            if not tv_id_int or not per_id_int:
                continue
            if row_id:                                  # fila existente → UPDATE
                rel = Relaciones.query.get(int(row_id))
                if rel and rel.PersonaId == id and rel.fecha_baja is None:
                    log.debug('  relacion UPDATE id=%d', rel.id)
                    rel.TiposValoresId       = tv_id_int
                    rel.PersonaRelacionadaId = per_id_int
                    rel.usuario_mod          = current_user.usuario
                    rel.fecha_mod            = now
                    ids_vistos_rel.add(rel.id)
            else:                                       # fila nueva → INSERT
                log.info('  relacion INSERT tipo=%s persona=%s', tv_id_int, per_id_int)
                rel = Relaciones()
                rel.PersonaId            = p.id
                rel.TiposValoresId       = tv_id_int
                rel.PersonaRelacionadaId = per_id_int
                rel.usuario_alta         = current_user.usuario
                rel.fecha_alta           = now
                db.session.add(rel)
                db.session.flush()          # obtener id antes del bucle de bajas
                ids_vistos_rel.add(rel.id)
        except (ValueError, TypeError):
            pass

    for rel in Relaciones.query.filter_by(PersonaId=id)\
                               .filter(Relaciones.fecha_baja == None).all():
        if rel.id not in ids_vistos_rel:               # eliminada en el form → baja
            rel.usuario_baja = current_user.usuario
            rel.fecha_baja   = now

    # ── Contactos: UPDATE si tiene id, INSERT si no, baja si desaparece ──────
    con_ids     = request.form.getlist('contacto_id[]')
    con_tipos   = request.form.getlist('contacto_tipo[]')
    con_lugares = request.form.getlist('contacto_lugar[]')
    con_valores = request.form.getlist('contacto_valor[]')

    ids_vistos_con = set()
    for row_id, tc_id, tl_id, valor in zip(con_ids, con_tipos, con_lugares, con_valores):
        try:
            tc_id_int = int(tc_id)
            tl_id_int = int(tl_id)
            valor = valor.strip()
            if not tc_id_int or not tl_id_int or not valor:
                continue
            # Normalizar teléfonos: guardar sin espacios
            tv = TiposValores.query.get(tc_id_int)
            if tv and tv.nombre == 'Teléfono':
                valor = normalizar_telefono(valor)
            if row_id:                                  # fila existente → UPDATE
                con = Contactos.query.get(int(row_id))
                if con and con.PersonaId == id and con.fecha_baja is None:
                    log.debug('  contacto UPDATE id=%d valor=%r→%r', con.id, con.valor, valor)
                    con.TipoContactoId = tc_id_int
                    con.TipoLugarId    = tl_id_int
                    con.valor          = valor
                    con.usuario_mod    = current_user.usuario
                    con.fecha_mod      = now
                    ids_vistos_con.add(con.id)
            else:                                       # fila nueva → INSERT
                log.info('  contacto INSERT tipo=%s lugar=%s valor=%r', tc_id_int, tl_id_int, valor)
                con = Contactos()
                con.PersonaId      = p.id
                con.TipoContactoId = tc_id_int
                con.TipoLugarId    = tl_id_int
                con.valor          = valor
                con.usuario_alta   = current_user.usuario
                con.fecha_alta     = now
                db.session.add(con)
                db.session.flush()          # obtener id antes del bucle de bajas
                ids_vistos_con.add(con.id)
        except (ValueError, TypeError):
            pass

    for con in Contactos.query.filter_by(PersonaId=id)\
                              .filter(Contactos.fecha_baja == None).all():
        if con.id not in ids_vistos_con:               # eliminada en el form → baja
            con.usuario_baja = current_user.usuario
            con.fecha_baja   = now

    db.session.commit()

    filtro_qs = request.args.get('filtro_qs', '')
    return redirect(url_for('personas') + ('?' + filtro_qs if filtro_qs else ''))


# ── BAJA LÓGICA ───────────────────────────────────────────────────────────────
@app.route('/personas/<int:id>/delete', methods=['post'])
@login_required
def personas_delete(id):
    p = Personas.query.get_or_404(id)
    if p.UsuarioId != current_user.id and not current_user.is_admin():
        abort(403)

    now = datetime.now()
    p.usuario_baja = current_user.usuario
    p.fecha_baja   = now

    # Baja lógica en relaciones
    rels = Rel_persona_etiqueta.query\
           .filter_by(PersonaId=id)\
           .filter(Rel_persona_etiqueta.fecha_baja == None).all()
    for rel in rels:
        rel.usuario_baja = current_user.usuario
        rel.fecha_baja   = now

    db.session.commit()

    filtro_qs = request.args.get('filtro_qs', '')
    return redirect(url_for('personas') + ('?' + filtro_qs if filtro_qs else ''))


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
            log.info('=== INICIO importación CSV: archivo=%r usuario=%s ===',
                     archivo.filename, current_user.usuario)
            contactos_csv = procesar_archivo(archivo)
            nuevos, actualizados, errores = 0, 0, []
            now = datetime.now()

            # Precargar catálogos de TiposValores
            tipo_contacto_t = Tipos.query.filter_by(nombre='Contacto').first()
            tipo_lugar_t    = Tipos.query.filter_by(nombre='Lugar Contacto').first()
            tipo_eventos_t  = Tipos.query.filter_by(nombre='Eventos').first()

            if not tipo_contacto_t:
                log.warning('No existe Tipo "Contacto" en BD — los contactos no se importarán')
            if not tipo_lugar_t:
                log.warning('No existe Tipo "Lugar Contacto" en BD — los contactos no se importarán')
            if not tipo_eventos_t:
                log.warning('No existe Tipo "Eventos" en BD — los eventos no se importarán')

            cache_tv_contacto  = {}
            cache_tv_lugar     = {}
            cache_tv_evento    = {}

            def _get_tv(cache, tipo_padre, nombre_valor):
                """Devuelve el TiposValores por nombre, creándolo si no existe."""
                if nombre_valor in cache:
                    return cache[nombre_valor]
                if tipo_padre is None:
                    return None
                tv = TiposValores.query.filter_by(
                    TipoId=tipo_padre.id, nombre=nombre_valor).first()
                if tv is None:
                    log.info('    TiposValores creado automáticamente: tipo=%r nombre=%r',
                             tipo_padre.nombre, nombre_valor)
                    tv = TiposValores(TipoId=tipo_padre.id, nombre=nombre_valor)
                    db.session.add(tv)
                    db.session.flush()
                cache[nombre_valor] = tv
                return tv

            for contacto in contactos_csv:
                if 'nombre' not in contacto:
                    continue
                try:
                    nombre_completo = contacto['nombre'].strip()
                    sufijo = contacto.get('sufijo_nombre', '').strip()
                    if sufijo:
                        nombre_completo = (nombre_completo + ' ' + sufijo).strip()

                    # ── Alta o localización de la persona ─────────────────────
                    persona = Personas.query\
                              .filter_by(UsuarioId=current_user.id,
                                         apodo=nombre_completo)\
                              .filter(Personas.fecha_baja == None).first()

                    if persona is None:
                        log.info('IMPORTAR NUEVA persona: %r', nombre_completo)
                        persona = Personas()
                        persona.UsuarioId    = current_user.id
                        persona.apodo        = nombre_completo
                        # nombre es NOT NULL: usar nombre_completo si no hay nombre separado
                        persona.nombre       = ''  # nombre_completo
                        persona.notas        = contacto.get('notas', '')
                        persona.usuario_alta = current_user.usuario
                        persona.fecha_alta   = now
                        db.session.add(persona)
                        db.session.flush()
                        nuevos += 1
                    else:
                        log.info('IMPORTAR ACTUALIZAR persona: %r (id=%d)', nombre_completo, persona.id)
                        cambios_persona = []
                        if contacto.get('notas') and contacto['notas'] != persona.notas:
                            cambios_persona.append(f'notas: {persona.notas!r}→{contacto["notas"]!r}')
                            persona.notas = contacto['notas']
                        if cambios_persona:
                            log.info('  campos actualizados: %s', ' | '.join(cambios_persona))
                        else:
                            log.debug('  sin cambios en campos principales')
                        persona.usuario_mod = current_user.usuario
                        persona.fecha_mod   = now
                        actualizados += 1

                    # ── Etiquetas ─────────────────────────────────────────────
                    nombres_nuevos = set(contacto.get('etiquetas', []))
                    rels_activas   = Rel_persona_etiqueta.query\
                                     .filter_by(PersonaId=persona.id)\
                                     .filter(Rel_persona_etiqueta.fecha_baja == None).all()
                    etis_actuales = {}
                    for rel in rels_activas:
                        eti = Etiquetas.query.get(rel.EtiquetaId)
                        if eti:
                            etis_actuales[eti.nombre] = rel

                    for nombre_eti, rel in etis_actuales.items():
                        if nombre_eti not in nombres_nuevos:
                            log.info('  etiqueta BAJA: %r persona=%r', nombre_eti, nombre_completo)
                            rel.usuario_baja = current_user.usuario
                            rel.fecha_baja   = now

                    for nombre_eti in nombres_nuevos:
                        eti = Etiquetas.query.filter_by(nombre=nombre_eti).first()
                        if eti is None:
                            log.info('  etiqueta NUEVA creada: %r', nombre_eti)
                            eti = Etiquetas(nombre=nombre_eti, descripcion='')
                            db.session.add(eti)
                            db.session.flush()
                        if nombre_eti not in etis_actuales:
                            log.info('  etiqueta ALTA: %r persona=%r', nombre_eti, nombre_completo)
                            rel = Rel_persona_etiqueta()
                            rel.PersonaId    = persona.id
                            rel.EtiquetaId   = eti.id
                            rel.usuario_alta = current_user.usuario
                            rel.fecha_alta   = now
                            db.session.add(rel)
                        else:
                            log.debug('  etiqueta ya existente: %r (sin cambios)', nombre_eti)

                    # ── Contactos ─────────────────────────────────────────────
                    cons_anteriores = Contactos.query\
                                     .filter_by(PersonaId=persona.id)\
                                     .filter(Contactos.fecha_baja == None).all()
                    if cons_anteriores:
                        log.debug('  dando de baja %d contactos anteriores', len(cons_anteriores))
                    for con in cons_anteriores:
                        con.usuario_baja = current_user.usuario
                        con.fecha_baja   = now

                    for con_csv in contacto.get('contactos', []):
                        tv_tipo  = _get_tv(cache_tv_contacto, tipo_contacto_t, con_csv['tipo'])
                        tv_lugar = _get_tv(cache_tv_lugar,    tipo_lugar_t,    con_csv['lugar'])
                        if tv_tipo and tv_lugar:
                            con = Contactos()
                            con.PersonaId      = persona.id
                            con.TipoContactoId = tv_tipo.id
                            con.TipoLugarId    = tv_lugar.id
                            con.valor          = con_csv['valor']
                            con.usuario_alta   = current_user.usuario
                            con.fecha_alta     = now
                            db.session.add(con)
                            log.debug('  contacto INSERT: %s/%s = %r',
                                      con_csv['tipo'], con_csv['lugar'], con_csv['valor'])
                        else:
                            log.warning('  contacto OMITIDO (tipo o lugar no resuelto): %s', con_csv)

                    # ── Eventos del CSV ───────────────────────────────────────
                    evs_anteriores = Eventos.query\
                                    .filter_by(PersonaId=persona.id)\
                                    .filter(Eventos.fecha_baja == None).all()
                    if evs_anteriores:
                        log.debug('  dando de baja %d eventos anteriores', len(evs_anteriores))
                    for ev in evs_anteriores:
                        ev.usuario_baja = current_user.usuario
                        ev.fecha_baja   = now

                    for ev_csv in contacto.get('eventos_csv', []):
                        tv_ev = _get_tv(cache_tv_evento, tipo_eventos_t, ev_csv['tipo'])
                        if tv_ev:
                            try:
                                from datetime import date as _date
                                fecha_ev = _date.fromisoformat(ev_csv['fecha'])
                            except (ValueError, TypeError) as e:
                                log.warning('  evento OMITIDO fecha inválida %r: %s',
                                            ev_csv['fecha'], e)
                                continue
                            ev = Eventos()
                            ev.PersonaId      = persona.id
                            ev.TiposValoresId = tv_ev.id
                            ev.fecha          = fecha_ev
                            ev.usuario_alta   = current_user.usuario
                            ev.fecha_alta     = now
                            db.session.add(ev)
                            log.debug('  evento INSERT: %s = %s', ev_csv['tipo'], fecha_ev)
                        else:
                            log.warning('  evento OMITIDO (tipo no resuelto): %s', ev_csv)

                    db.session.commit()
                    log.debug('  commit OK persona=%r', nombre_completo)

                except Exception as e:
                    log.error('ERROR procesando %r: %s', contacto.get('nombre', '?'), e,
                              exc_info=True)
                    errores.append(f"{contacto.get('nombre','?')}: {str(e)}")
                    db.session.rollback()

            log.info('=== FIN importación: nuevos=%d actualizados=%d errores=%d ===',
                     nuevos, actualizados, len(errores))
            resultado = {'nuevos': nuevos, 'actualizados': actualizados,
                         'errores': errores}

    return render_template('personas/importar.html', form=form, resultado=resultado)
