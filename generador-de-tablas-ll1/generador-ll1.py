import os
import csv
import sys

# Módulo para crear diccionarios con valores por defecto.
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compilador.lexico import tokens

# Cargar la gramática desde el archivo.
directorio = os.path.dirname(__file__)
gramatica_archivo = 'gramatica.txt'
archivo_gramatica = os.path.join(directorio, '..', 'gramatica', gramatica_archivo)

# Guardar la tabla en un archivo CSV.
csv_filename = 'tabla_ll1.csv'
carpeta_salida = 'tabla-ll1'

# Función que lee la gramática desde un archivo.
def leer_archivo_gramatica(nombre_archivo):
    gramatica = {}
    with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            # Filtra las líneas vacías o comentarios.
            if not linea or linea.startswith('#'):
                continue
            # Separa las producciones usando '->' o '::='
            if '->' in linea:
                lado_izquierdo, lado_derecho = linea.split('->', 1)
            elif '::=' in linea:
                lado_izquierdo, lado_derecho = linea.split('::=', 1)
            else:
                continue
            # Limpiar y procesar los símbolos.
            lado_izquierdo = lado_izquierdo.strip()
            lado_derecho = lado_derecho.strip()
            simbolos = lado_derecho.split()
            simbolos = ['e' if simbolo == "''" else simbolo for simbolo in simbolos]
            if lado_izquierdo not in gramatica:
                gramatica[lado_izquierdo] = []
            gramatica[lado_izquierdo].append(simbolos)
    return gramatica

# Función para calcular el conjunto de primeros de un símbolo.
def compute_first(symbol):
    # Si el conjunto FIRST ya está calculado, lo retorna.
    if symbol in FIRST and FIRST[symbol]:
        return FIRST[symbol]
    # Si es un terminal, agrega el símbolo a su conjunto FIRST.
    if symbol in tokens:
        FIRST[symbol] = set([symbol])
        return FIRST[symbol]
    first = set()
    # Para cada producción del símbolo no terminal, calcular el FIRST.
    for production in gramatica_general[symbol]:
        if production[0] == 'e':
            first.add('e')
        else:
            for sym in production:
                sym_first = compute_first(sym)
                first.update(sym_first - set(['e']))
                # Si no contiene la 'e', se termina.
                if 'e' not in sym_first:
                    break
            else:
                first.add('e')
    FIRST[symbol] = first
    return first

# Función para calcular el conjunto de siguientes de un símbolo.
def compute_follow(symbol):
    # El primer símbolo tiene '$' como símbolo de fin de entrada.
    if symbol == list(gramatica_general.keys())[0]:
        FOLLOW[symbol].add('$')
    # Recorre la gramática y calcula los conjuntos FOLLOW.
    for lhs in gramatica_general:
        for production in gramatica_general[lhs]:
            for i, sym in enumerate(production):
                if sym == symbol:
                    # Si hay un símbolo siguiente en la producción, se agrega su FIRST.
                    if i + 1 < len(production):
                        next_sym = production[i + 1]
                        next_first = compute_first(next_sym)
                        FOLLOW[symbol].update(next_first - set(['e']))
                        if 'e' in next_first:
                            FOLLOW[symbol].update(FOLLOW[lhs])
                    else:
                        # Si es el último, se agregan los FOLLOW del lado izquierdo.
                        if lhs != symbol:
                            FOLLOW[symbol].update(FOLLOW[lhs])

gramatica_general = leer_archivo_gramatica(archivo_gramatica)

# Agregar el símbolo de fin de entrada al conjunto de tokens.
tokens.append('$')

# Obtiene todos los no terminales de la gramática.
non_terminals = list(gramatica_general.keys())

# Inicializar el conjunto de primeros y siguientes (FIRST y FOLLOW).
FIRST = defaultdict(set)
FOLLOW = defaultdict(set)

# Calcular FIRST para todos los no terminales.
for non_terminal in non_terminals:
    compute_first(non_terminal)

# Inicializar FOLLOW para todos los no terminales.
for non_terminal in non_terminals:
    FOLLOW[non_terminal] = set()

# Recalcular FOLLOW hasta que no haya cambios.
changed = True
while changed:
    changed = False
    for non_terminal in non_terminals:
        before = len(FOLLOW[non_terminal])
        compute_follow(non_terminal)
        after = len(FOLLOW[non_terminal])
        if before != after:
            changed = True

# Crear la tabla LL(1).
ll1_table = defaultdict(dict)

# Rellenar la tabla LL(1) con las producciones correspondientes.
for lhs in gramatica_general:
    for production in gramatica_general[lhs]:
        firsts = set()
        if production[0] == 'e':
            firsts.add('e')
        else:
            for sym in production:
                sym_first = compute_first(sym)
                firsts.update(sym_first - set(['e']))
                if 'e' not in sym_first:
                    break
            else:
                firsts.add('e')
        # Llenar la tabla para cada terminal en FIRST.
        for terminal in firsts - set(['e']):
            ll1_table[lhs][terminal] = ' '.join(production)
        # Si 'e' está en FIRST, se rellena también para los terminales en FOLLOW.
        if 'e' in firsts:
            for terminal in FOLLOW[lhs]:
                ll1_table[lhs][terminal] = 'e'

# Crear la carpeta si no existe.
if not os.path.exists(carpeta_salida):
    os.makedirs(carpeta_salida)

# Definir la ruta del archivo CSV de salida.
archivo_salida = os.path.join(carpeta_salida, csv_filename)

# Abrir el archivo CSV para escribir los datos.
with open(archivo_salida, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Escribir las cabeceras (tokens).
    headers = [''] + tokens
    csvwriter.writerow(headers)
    # Escribir cada fila correspondiente a un no terminal.
    for idx, nt in enumerate(non_terminals):
        row = [nt]
        for t in tokens:
            action = ll1_table[nt].get(t, '')
            row.append(action)
        csvwriter.writerow(row)

# Eliminar saltos de línea innecesarios al final del archivo CSV.
with open(archivo_salida, 'rb+') as csvfile:
    csvfile.seek(-2, os.SEEK_END)
    while csvfile.tell() > 0 and csvfile.read(1) in [b'\n', b'\r']:
        csvfile.seek(-2, os.SEEK_CUR)
    if csvfile.tell() > 0:
        csvfile.truncate()

# Después de calcular FIRST y FOLLOW para todos los no terminales
print("\nConjunto de primeros:")
for non_terminal in non_terminals:
    print(f"Primeros de {non_terminal} -> {FIRST[non_terminal]}")

print("\nConjunto de siguientes:")
for non_terminal in non_terminals:
    print(f"Siguientes de {non_terminal} -> {FOLLOW[non_terminal]}")

# Imprimir mensaje final.
print(f"\nTabla LL(1) exportada a {archivo_salida}\n")