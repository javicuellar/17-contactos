#!/usr/bin/env python3
"""
Script de migración contactos_v21 → contactos_v22
--------------------------------------------------
- Añade la columna 'apellidos' a la tabla 'personas'
- Migra todos los registros de 'contactos' a 'personas' con UsuarioId del usuario indicado
- Migra todas las relaciones de 'rel_contacto_etiqueta' a 'rel_persona_etiqueta'

Uso: python migrar_v21_a_v22.py <ruta_bd> [usuario_alta] [usuario_id]
     Por defecto: usuario_alta='javi', usuario_id=2
"""

import sys
import sqlite3
from datetime import datetime, timezone



def migrar(db_path, db_path2, usuario_alta='javi', usuario_id=2):
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    conn2 = sqlite3.connect(db_path2)
    cur2 = conn2.cursor()
    ahora = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    # 1. Añadir columna apellidos a personas si no existe
    # try:
    #     cur.execute("ALTER TABLE personas ADD COLUMN apellidos VARCHAR(150)")
    #     print("[OK] Columna 'apellidos' añadida a la tabla 'personas'")
    # except sqlite3.OperationalError:
    #     print("[--] Columna 'apellidos' ya existe, se omite")
    # conn.commit()

    # 2. Migrar contactos → personas
    cur.execute("SELECT id, nombre, apellidos, notas FROM contactos")
    contactos = cur.fetchall()

    mapa_ids = {}
    for (c_id, nombre, apellidos, notas) in contactos:
        cur2.execute("""
            INSERT INTO personas (UsuarioId, apodo, nombre, notas, usuario_alta, fecha_alta)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, nombre or '', apellidos or '', notas or '', usuario_alta, ahora))
        mapa_ids[c_id] = cur2.lastrowid

    conn2.commit()
    print(f"[OK] {len(contactos)} contactos migrados → personas (UsuarioId={usuario_id}, usuario_alta='{usuario_alta}')")

    # 3. Migrar rel_contacto_etiqueta → rel_persona_etiqueta
    cur.execute("SELECT EtiquetaId, ContactoId FROM rel_contacto_etiqueta")
    rels = cur.fetchall()

    migradas = 0
    for (eti_id, c_id) in rels:
        p_id = mapa_ids.get(c_id)
        if p_id:
            cur2.execute("""
                INSERT INTO rel_persona_etiqueta (EtiquetaId, PersonaId, usuario_alta, fecha_alta)
                VALUES (?, ?, ?, ?)
            """, (eti_id, p_id, usuario_alta, ahora))
            migradas += 1

    conn2.commit()
    print(f"[OK] {migradas} relaciones migradas → rel_persona_etiqueta")

    # 4. Migrar etiquetas → etiquetas
    cur.execute("SELECT Id, nombre, descripcion FROM etiquetas")
    etis = cur.fetchall()

    migradas = 0
    for eti_id, nombre, descripcion in etis:
        cur2.execute("""
            INSERT INTO etiquetas (Id, nombre, descripcion)
            VALUES (?, ?, ?)
            """, (eti_id, nombre, descripcion))
        migradas += 1

    conn2.commit()
    print(f"[OK] {migradas} relaciones migradas → rel_persona_etiqueta")

    # Resumen
    cur.execute("SELECT COUNT(*) FROM personas")
    print(f"\nResumen final:")
    print(f"  Total personas:              {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM rel_persona_etiqueta")
    print(f"  Total rel_persona_etiqueta:  {cur.fetchone()[0]}")
    conn.close()
    print("\nMigración completada con éxito.")




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    db_path      = sys.argv[1]
    db_path2     = sys.argv[2] if len(sys.argv) > 1 else '.\\data\\contactos'
    usuario_alta = sys.argv[3] if len(sys.argv) > 2 else 'javi'
    usuario_id   = int(sys.argv[4]) if len(sys.argv) > 3 else 2
    migrar(db_path, db_path2, usuario_alta, usuario_id)
