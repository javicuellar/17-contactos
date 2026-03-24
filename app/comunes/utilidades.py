
import pandas as pd





# Definimos las etiquetas de Google y las etiquetas de la tabla
transf = {'First Name': 'nombre',
        'Notes':      'notas',
        'Birthday':   'cumpleaños',
        'Last Name':  'sufijo_nombre',
        'Middle Name':'nombre_medio',
        'Organization Name': 'empresa',
        'Organization Title': 'puesto_empresa',
        }

doble = {'Phone '   :'telefono',
        'E-mail'   :'email',
        'Addres'   :'direccion',
        'Websit'   :'web',
        'Custom'   :'personalizado',
        'Street'   :'calle',
        'City'     :'ciudad',
        'Region'   :'provincia',
        'Postal'   :'cp',
        'Countr'   :'pais',
        'PO Box'   :'pd_box',
        'Extend'   :'extend',
        'Event '   :'evento',
        'Relati'   :'relacion',
        }

labels = {'Work':   'trabajo',
        'Mobile':  'movil',
        'Móvil':   'movil',
        'Home':    'casa',
        '* Home':  'casa',
        '* Work':  'trabajo',
        '* Personal': 'personal',
        '* Antiguo': 'antiguo',
        'Antigua': 'antiguo',
        '* ':     'vacio',
        '* null': 'vacio',
        'Profile':'perfil',
        'Other':  'otro',
        '* Other':'otro',
        'Photo':  'foto',
        'Anniversary': 'aniversario',
        'Personal': 'personal',
        'Nueva': 'nueva',
        'Google+': 'google',
        'Home Page': 'home_page',
        'Facebook': 'facebook',
        'Main': 'principal',
        '* Atención Cliente': 'atencion_cliente',
        'Atención Cliente': 'atencion_cliente',
        'WhatsApp': 'whatsapp',
        'LinkedIn': 'linkedin',
        'Twitter': 'twitter',
        'Domestic Partner': 'domestic_partner'
        }

etiquetas = ['Madrid Digital', 'Narval', 'Narval Ski', 'Enrique', 'Sofía', 'Mar Rojo', 'Servicios', 'Familia', 'Alcorcón']




def procesar_archivo(archivo):
	try:
		df = pd.read_csv(archivo)
		# print(df.info())
	except FileNotFoundError:
		print(f"Error: Archivo no encontrado en {archivo}")
	except pd.errors.ParserError:
		print(f"Error: No se pudo analizar el archivo CSV en {archivo}")
	except Exception as e:
		print(f"Error inesperado: {e}")


	lista_contactos =[]

	for index, row in df.iterrows():
		print(f"Fila {index}:")
		contacto = {}
		for col, value in row.items():
			if pd.notna(value):         # Verificar si el valor no es NaN
				# print(f"  {col}: {value}")

				# Transformación directa, una etiqueta en Google, una etiqueta en tabla
				if col in transf:
					contacto[transf[col]] = value
					# print(f"    -> Transformado a {transf[col]}: {value}")

				# Transformación de dos filas en una etiqueta tabla, ejemplo Phone y E-mail
				elif col[:6] in doble and 'Label' in col:
					if value in labels:
						etiqueta = labels[value]
						# print(f"    -> Etiqueta identificada {value}")
					else:
						etiqueta = f'No identificada {col}: {value}'
						print(f"    * Etiqueta no identificada -> {col[:6]}: {value}, {len(value)}")


				# Transformación de la segunda fia, etiqueta creada de la primera fila + valor de la segunda fila
				elif col[:6] in doble and ('Value' in col or col[:6] == 'Addres'):
					if col[:6] == 'Addres':
						# Cogemos la información de dirección a partir de la columna 12 (Street, city, ...)
						# print(f"  cambio {col} -> {col[12:]} -> {col[:6]}")
						col = col[12:]
						# Nos saltamos la columna Formatted que contiene la dirección formateada
						if col == 'Formatted':
							continue

					if etiqueta == '':
						# print(f"  {col}: {value}")
						etiqueta = doble[col[:6]]
					else:
						etiqueta = doble[col[:6]] + '_' + etiqueta

					contacto[etiqueta] = value
					etiqueta = ''
					# print(f"    -> Transformado a {etiqueta}: {value}")

				# Transformación de etiquetas, 'Labels'
				elif col == 'Labels':
					eti = []
					for etiqueta in etiquetas:
						if etiqueta in value:
							eti.append(etiqueta)
					if eti != []:
						contacto['etiquetas'] = eti
					# print(f"    -> Transformado a Etiquetas: {eti}")

				# Sino, todavía no transformada
				else:
					print(f"    -> No transformado.- {col}: {value}")

		# Guardamos el contacto en la lista de contactos
		lista_contactos.append(contacto)
		print("Seprador", "-" * 30)

	# print("***  Información recopilada de contactos  ***")
	# for contacto in contactos:
	# 	print(contacto)
	
	return lista_contactos