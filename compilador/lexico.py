import os
import ply.lex as lex
import sys

from tabulate import tabulate

# Ingresar datos del boceto de código.
directorio = os.path.dirname(__file__)
archivo = 'buclesanidados.txt' # Ingresar el nombre del boceto.
ruta_archivo = os.path.join(directorio, '..', 'codigos-bocetos', archivo)

# Clase Token para realizar la tokenización usando ply.
class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
    
    def __str__(self): return f"{self.tipo} {self.valor} {self.linea} {self.columna}"
    
    def __repr__(self): return self.__str__()

# Clase para representar errores.
class Error:
    def __init__(self, mensaje, linea, columna):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return f"Error en la línea {self.linea}, columna {self.columna}: {self.mensaje}"

# Subclase para identificar errores léxicos.
class ErrorLexico(Error):
    def __init__(self, caracter, linea, columna):
        mensaje = f"carácter ilegal {caracter}"
        super().__init__(mensaje, linea, columna)

# Lista para almacenar errores léxicos.
lista_errores_lexicos = []

# Función para mostrar el resultado de la evaluacion léxica.
def mostrar_resultado_lexico(lista_errores_lexicos):
    if not lista_errores_lexicos:
        print("\nAnálisis léxico exitoso ✅")
    else:
        print("\n❌❌❌ Análisis léxico fallido ❌❌❌\n")
        print("Errores léxicos detectados:")
        for error in lista_errores_lexicos:
            print(error)
        sys.exit()

# Función encargada de imprimir los Tokens existentes.
def imprimir_tokens(tokens):
    if not tokens:
        print("No hay tokens para imprimir")
        return
    headers = ["Tipo", "Valor", "Línea", "Columna"]
    data = [[token.tipo, token.valor, token.linea, token.columna] for token in tokens]
    # Centrar todos los textos en la tabla.
    table = tabulate(data, headers=headers, tablefmt="double_outline", stralign="center", numalign="center")
    print("\nLista de Tokens:")
    print(table)

# Función encargada de leer el código situado dentro del boceto seleccionado.
def generar_datos(archivo):
    try:
        with open(archivo, 'r') as file:
            datos = file.read()
    except FileNotFoundError:
        print(f"Error: el archivo {archivo} no se ha encontrado")
        datos = ''
    return datos 

# Función de prueba: probar los Tokens en las páginas https://jsmachines.sourceforge.net/machines/ll1.html o https://www.cs.princeton.edu/courses/archive/spring20/cos320/LL1/
def escribir_tokens_en_txt(lista_de_tokens, nombre_de_archivo):
    carpeta_de_salida = 'salida-tokens'
    if not os.path.exists(carpeta_de_salida):
        os.makedirs(carpeta_de_salida)   
    archivo_de_salida = os.path.join(carpeta_de_salida, nombre_de_archivo)
    try:
        with open(archivo_de_salida, 'w') as archivo:
            tokens = ' '.join([token.tipo for token in lista_de_tokens])
            archivo.write(tokens)
            print(f"Tokens escritos exitosamente en el archivo {archivo_de_salida}.\n")
    except Exception as error:
        print(f"Error al escribir los tokens en el archivo: {str(error)}") 

# Tokens de FucionCod.
tokens = [
    'funcion', 'principal', 'pabierto', 'pcerrado', 'imprimir', 'comillas', 'id', 'coma', 
    'fsentencia', 'devolver', 'detener', 'llaveabi', 'llavecerr', 'tentero', 
    'tflotante', 'tbooleano', 'tcadena', 'tvacio', 'si', 'y', 'o', 'sino', 'entonces', 
    'mientras', 'para', 'suma', 'resta', 'mul', 'div', 'residuo', 'menorque', 
    'mayorque', 'menorigualque', 'mayorigualque', 'igual', 'igualbool', 
    'diferentede', 'nentero', 'nflotante', 'ncadena', 'nbooleano', 'leer'
]
 
# Palabras reservadas de FusionCod.
palabras_reservadas = {
    'fn': 'funcion', 'main': 'principal', 'show': 'imprimir', 'return': 'devolver', 'stop': 'detener',
    'int': 'tentero', 'float': 'tflotante', 'text': 'tcadena', 'bool': 'tbooleano', 'void': 'tvacio', 'if': 'si',
    '&&': 'y', 'and': 'y', '||': 'o', 'or': 'o', 'elif': 'sino', 'else': 'entonces', 'while': 'mientras', 'for': 'para', 
    'true': 'nbooleano', 'false': 'nbooleano', 'read': 'leer'
}

# Expresiones regulares de FusionCod.
t_fsentencia = r';'
t_pabierto = r'\('
t_pcerrado = r'\)'
t_llaveabi = r'\{'
t_llavecerr= r'\}'
t_suma = r'\+'
t_resta = r'-'
t_mul = r'\*'
t_div = r'/'
t_residuo= r'%'
t_menorque = r'<'
t_mayorque = r'>'
t_menorigualque = r'<='
t_mayorigualque = r'>='
t_igual = r'='
t_igualbool = r'=='
t_diferentede = r'<>'
t_coma = r','

# Ignorar espacios y tabulaciones.
t_ignore = ' \t'

# Expresión regular para cadenas de texto.
def t_ncadena(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

# Expresión regular para identificadores.
def t_id(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = palabras_reservadas.get(t.value, 'id')
    return t

# Expresión regular para números flotantes.
def t_nflotante(t):
    r'-?\d+\.\d+'
    t.value = float(t.value)
    return t

# Expresión regular para números enteros.
def t_nentero(t):
    r'-?\d+'
    t.value = int(t.value)
    return t

# Expresión regular para comentarios.
def t_comentario(t):
    r'\#.*'
    pass # Ignorar los comentarios en el análisis.

# Manejo de saltos de líneas.
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Manejo de errores léxicos.
def t_error(t):
    columna = t.lexpos - t.lexer.lexdata.rfind('\n', 0, t.lexpos)
    error = ErrorLexico(t.value[0], t.lineno, columna)
    lista_errores_lexicos.append(error)
    t.lexer.skip(1)

print(f"\nCódigo a compilar: {archivo}")

# Inicializar el lexer.
lexer = lex.lex()
lexer.input(generar_datos(ruta_archivo)) # Cargar datos

# Función para generar la lista de tokens reconocidos en el código fuente.
def generar_tokens():
    lista_de_tokens = []
    while True:
        tok = lexer.token()
        if not tok: break
        token_obj = Token(tok.type, tok.value, tok.lineno, tok.lexpos)
        lista_de_tokens.append(token_obj)
    return lista_de_tokens

# Generar la lista de tokens llamando a la función generar_tokens.
lista_de_tokens = generar_tokens()

# Imprimir la lista de tokens obtenida.
imprimir_tokens(lista_de_tokens)

# Mostrar el resultado del análisis léxico.
mostrar_resultado_lexico(lista_errores_lexicos)

# Escribir los tokens para probar en un .txt.
salida_nombre_tokens = f"{os.path.splitext(archivo)[0]}-tokens"
escribir_tokens_en_txt(lista_de_tokens, salida_nombre_tokens)