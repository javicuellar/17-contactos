import re
import pandas as pd

from app.comunes.logger import get_logger



log = get_logger('comunes.utilidades')


# ── Mapeo de columnas simples Google → clave interna ─────────────────────────
TRANSF_DIRECTO = {
    'First Name':         'nombre',
    'Last Name':          'sufijo_nombre',
    'Middle Name':        'nombre_medio',
    'Notes':              'notas',
    'Birthday':           'Cumpleaños',
    'Organization Name':  'empresa',
    'Organization Title': 'puesto_empresa',
}

# ── Prefijos de 6 chars que generan contactos ────────────────────────────────
# None = tratamiento especial o ignorar
PREFIJO_A_TIPO_CONTACTO = {
    'Phone ':  'Teléfono',
    'E-mail':  'Email',
    'Websit':  'Web',
    'Event ':  '__evento__',
    'Addres':  'Dirección',   # Address 1, Address 2… de Google
    'Relati':  None,          # relaciones del CSV: ignorar
}

# ── Etiquetas de sistema de Google que deben ignorarse al importar ────────────
ETIQUETAS_IGNORAR = {
    '* mycontacts',
    'mycontacts',
    '* starred',
    'starred',
}

# ── Mapeo lugar Google → nombre canónico de 'Lugar Contacto' ─────────────────
LUGAR_GOOGLE = {
    'work':               'Trabajo',
    '* work':             'Trabajo',
    'home':               'Casa',
    '* home':             'Casa',
    'mobile':             'Móvil',
    'móvil':              'Móvil',
    'personal':           'Personal',
    '* personal':         'Personal',
    'whatsapp':           'WhatsApp',
    'other':              'Otro',
    '* other':            'Otro',
    'main':               'Principal',
    '* main':             'Principal',
    'atención cliente':   'Atención Cliente',
    '* atención cliente': 'Atención Cliente',
    'antiguo':            'Antiguo',
    '* antiguo':          'Antiguo',
    'antigua':            'Antiguo',
    'home page':          'Web',
    'google+':            'Google+',
    'facebook':           'Facebook',
    'linkedin':           'LinkedIn',
    'twitter':            'Twitter',
    'profile':            'Perfil',
}

# ── Mapeo tipo evento Google → nombre canónico de TiposValores 'Eventos' ─────
EVENTO_GOOGLE = {
    'birthday':           'Cumpleaños',
    '* birthday':         'Cumpleaños',
    'fecha de nacimiento':'Cumpleaños',   # Google Contacts en español
    '* fecha de nacimiento': 'Cumpleaños',
    'anniversary':        'Aniversario',
    '* anniversary':      'Aniversario',
    'aniversary':         'Aniversario',  # typo habitual en CSV de Google
    '* aniversary':       'Aniversario',
    'other':              'Otro',
    '* other':            'Otro',
}


def normalizar_telefono(valor):
    """
    Si el valor parece un número de teléfono (solo dígitos, espacios, +, -, paréntesis),
    devuelve los dígitos sin espacios. Si no lo parece, devuelve el valor sin cambios.
    """
    solo_digitos_y_separadores = re.fullmatch(r'[\d\s\+\-\(\)\.]+', valor)
    if solo_digitos_y_separadores:
        # Conservar el + inicial si existe (prefijo internacional)
        prefijo = '+' if valor.lstrip().startswith('+') else ''
        digitos = re.sub(r'\D', '', valor)
        return prefijo + digitos
    return valor


def formatear_telefono(valor):
    """
    Formatea un número de teléfono guardado sin espacios.
    - 9 dígitos exactos               → 'nnn nnn nnn'
    - Más de 9 dígitos (ej. prefijo)  → los dígitos sobrantes sin formatear
                                        + espacio + últimos 9 en 'nnn nnn nnn'
    Ejemplos:
        '612345678'    → '612 345 678'
        '34612345678'  → '34 612 345 678'
        '+34612345678' → '+34 612 345 678'
    """
    if not valor:
        return valor

    # Separar el + inicial si existe
    tiene_plus = valor.startswith('+')
    digitos = re.sub(r'\D', '', valor)   # solo dígitos

    if len(digitos) <= 9:
        # Formatear todos en bloques de 3
        grupos = [digitos[i:i+3] for i in range(0, len(digitos), 3)]
        return ' '.join(grupos)
    else:
        # Los 9 últimos → 'nnn nnn nnn'; el resto va delante sin formatear
        cola   = digitos[-9:]
        cabeza = digitos[:-9]
        formato_cola = ' '.join([cola[i:i+3] for i in range(0, 9, 3)])
        prefijo_str = ('+' if tiene_plus else '') + cabeza
        return prefijo_str + ' ' + formato_cola


def _normalizar_lugar(raw):
    normalizado = LUGAR_GOOGLE.get(raw.strip().lower(), raw.strip())
    print("  > Lugar de contacto normalizado:", raw.strip().lower(), "→", repr(normalizado))
    log.debug('Lugar de contacto normalizado: %r → %r', raw, normalizado)
    if normalizado == raw.strip():
        log.warning('Lugar de contacto no reconocido: %r — se usará tal cual', raw)
    return normalizado


def _normalizar_evento_tipo(raw):
    normalizado = EVENTO_GOOGLE.get(raw.strip().lower(), raw.strip())
    if normalizado == raw.strip():
        log.warning('Tipo de evento no reconocido: %r — se usará tal cual', raw)
    return normalizado



# ── Función principal para procesar el CSV de Google Contacts ─────────────────
def procesar_archivo(archivo):
    """
    Lee un CSV de Google Contacts y devuelve lista de dicts con:
        nombre, sufijo_nombre, notas, etiquetas, contactos, eventos_csv
    """
    log.info('=== INICIO lectura CSV ===')

    try:
        df = pd.read_csv(archivo)
        log.info('CSV leído correctamente: %d filas, %d columnas', len(df), len(df.columns))
        log.debug('Columnas del CSV: %s', list(df.columns))
    except FileNotFoundError:
        log.error('Archivo CSV no encontrado')
        return []
    except pd.errors.ParserError as e:
        log.error('Error al analizar el CSV: %s', e)
        return []
    except Exception as e:
        log.error('Error inesperado leyendo CSV: %s', e)
        return []

    lista_contactos = []
    filas_sin_nombre = 0

    for idx, row in df.iterrows():
        contacto       = {}
        contactos_fila = []
        eventos_fila   = []

        tipo_pendiente  = None
        lugar_pendiente = None

        for col, value in row.items():
            if pd.isna(value):
                continue
            value = str(value).strip()
            if not value:
                continue

            prefijo6 = col[:6]

            # 1. Transformación directa
            if col in TRANSF_DIRECTO:
                if col == 'Birthday':
                    fecha_str = value
                    if fecha_str.startswith('--'):
                        fecha_str = '2000' + fecha_str[1:]
                    eventos_fila.append({'tipo': TRANSF_DIRECTO[col], 'fecha': fecha_str})
                    log.debug('  Evento: tipo=%r fecha=%r', TRANSF_DIRECTO[col], fecha_str)
                else:
                    contacto[TRANSF_DIRECTO[col]] = value
                    log.debug('  Transformación directa: %r → %r', col, value)
                continue

            # 2. Etiquetas desde Labels (ignorar etiquetas de sistema de Google)
            if col == 'Labels':
                etiquetas = [
                    e.strip()
                    for e in re.split(r'\s*:::\s*', value)
                    if e.strip() and e.strip().lower() not in ETIQUETAS_IGNORAR
                ]
                if etiquetas:
                    contacto['etiquetas'] = etiquetas
                    log.debug('  Etiquetas encontradas: %s', etiquetas)
                continue

            # 3. Columnas con prefijo conocido
            if prefijo6 not in PREFIJO_A_TIPO_CONTACTO:
                continue

            tipo_contacto = PREFIJO_A_TIPO_CONTACTO[prefijo6]

            if tipo_contacto is None:
                continue  # relaciones, ignorar

            # 3a. Eventos (Birthday, Anniversary…)
            if tipo_contacto == '__evento__':
                if '- Type' in col or '- Label' in col:
                    tipo_pendiente = _normalizar_evento_tipo(value)
                elif '- Value' in col:
                    tipo_ev = tipo_pendiente or 'Otro'
                    fecha_str = value
                    if fecha_str.startswith('--'):
                        fecha_str = '2000' + fecha_str[1:]
                    eventos_fila.append({'tipo': tipo_ev, 'fecha': fecha_str})
                    log.debug('  Evento: tipo=%r fecha=%r', tipo_ev, fecha_str)
                    tipo_pendiente = None
                continue

            # 3b. Contactos (Phone, E-mail, Website, Dirección)
            if '- Type' in col or '- Label' in col:
                lugar_pendiente = _normalizar_lugar(value)
                tipo_pendiente  = tipo_contacto
            elif tipo_contacto == 'Dirección' and '- Formatted' in col:
                # Las direcciones de Google llevan el valor en la columna Formatted
                lugar = lugar_pendiente or 'Trabajo'
                tipo  = tipo_pendiente  or tipo_contacto
                contactos_fila.append({'tipo': tipo, 'lugar': lugar, 'valor': value.replace('\n', '. ')})
                log.debug('  Dirección: tipo=%r lugar=%r valor=%r', tipo, lugar, value.replace('\n', '. '))
                lugar_pendiente = None
                tipo_pendiente  = None
            elif '- Value' in col:
                lugar = lugar_pendiente or 'Trabajo'
                tipo  = tipo_pendiente  or tipo_contacto
                # Limpiar sufijo .0 que pandas añade a números leídos como float
                if value.endswith('.0') and value[:-2].lstrip('-').isdigit():
                    value = value[:-2]
                # Normalizar teléfonos: guardar sin espacios
                if tipo == 'Teléfono':
                    value = normalizar_telefono(value)
                contactos_fila.append({'tipo': tipo, 'lugar': lugar, 'valor': value})
                log.debug('  Contacto: tipo=%r lugar=%r valor=%r', tipo, lugar, value)
                lugar_pendiente = None
                tipo_pendiente  = None

        # Ignorar filas sin nombre
        if 'nombre' not in contacto:
            filas_sin_nombre += 1
            log.debug('Fila %d ignorada: sin nombre (datos: %s)', idx, dict(row.dropna()))
            continue

        nombre_completo = contacto['nombre']
        if contacto.get('sufijo_nombre'):
            nombre_completo += ' ' + contacto['sufijo_nombre']

        # Componer empresa como contacto de tipo Empresa – Trabajo
        empresa_nombre = contacto.get('empresa', '').strip()
        empresa_puesto = contacto.get('puesto_empresa', '').strip()
        if empresa_nombre:
            valor_empresa = empresa_nombre
            if empresa_puesto:
                valor_empresa = f'{empresa_nombre} – {empresa_puesto}'
            contactos_fila.append({'tipo': 'Empresa', 'lugar': 'Trabajo', 'valor': valor_empresa})
            log.info('  empresa → contacto: tipo=Empresa lugar=Trabajo valor=%r', valor_empresa)

        log.info('PERSONA LEÍDA [fila %d]: %r', idx, nombre_completo)
        log.debug('  datos contacto: %s', contacto)
        if contacto.get('notas'):
            log.debug('  notas: %r', contacto['notas'])
        if contacto.get('etiquetas'):
            log.info('  etiquetas: %s', contacto['etiquetas'])
        if contactos_fila:
            log.info('  contactos (%d): %s', len(contactos_fila),
                     [(c['tipo'], c['lugar'], c['valor']) for c in contactos_fila])
        if eventos_fila:
            log.info('  eventos (%d): %s', len(eventos_fila),
                     [(e['tipo'], e['fecha']) for e in eventos_fila])

        if contactos_fila:
            contacto['contactos'] = contactos_fila
        if eventos_fila:
            contacto['eventos_csv'] = eventos_fila

        lista_contactos.append(contacto)

    log.info('=== FIN lectura CSV: %d personas procesadas, %d filas sin nombre ignoradas ===',
             len(lista_contactos), filas_sin_nombre)
    return lista_contactos
