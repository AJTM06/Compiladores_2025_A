import pandas as pd
import os

from graphviz import Digraph
from lexico import Error
from lexico import lista_errores_lexicos
from lexico import mostrar_resultado_lexico
from lexico import lista_de_tokens
from lexico import archivo
from lexico import Token

# Ingresar datos de la tabla en formato .csv
directorio = os.path.dirname(__file__)
archivo_ll1 = 'tabla_ll1.csv' # Ingresar el nombre de la tabla.
ruta_archivo_ll1 = os.path.join(directorio, '..', 'tabla-ll1', archivo_ll1)

# Agregar el $ a la lista de tokens.
lista_de_tokens.append(Token("$", "$", None, None))

# Subclase identificar un error sintáctico.
class ErrorSintactico(Error):
    def __init__(self, esperado, encontrado, linea, columna):
        mensaje = f"se esperaba {esperado}, pero se encontró {encontrado}"
        super().__init__(mensaje, linea, columna)

# Función encargada de cargar una tabla ll1.
def cargar_tabla_ll1(direccion):
    df = pd.read_csv(direccion, index_col = 0)
    df = df.fillna('')
    return df

# Clase Nodo para crear el árbol sintáctico.
class Nodo:
    def __init__(self, id, tipo, valor=None, linea=None, columna=None, terminal=False):
        self.id = id
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
        self.terminal = terminal
        self.hijos = []
        self.padre = None
    
    def añadir_hijo(self, hijo):
        hijo.padre = self  
        self.hijos.append(hijo)

# Funcion para generar el Digraph().
def arbolSintactico(raiz, contorno_hojas=False, opcion="tipo"):
    graph = Digraph()
    def generar_nodos(node):
        if opcion == "tipo":
            label = f"{node.tipo}"
        elif opcion == "linea":
            label = f"{node.linea}"
        elif opcion == "columna":
            label = f"{node.columna}"
        elif opcion == "valor":
            label = f"{node.valor}"
        elif opcion == "id":
            label = f"{node.id}"
        elif opcion == "terminal":
            label = f"{node.terminal}"
        else:
            label = f"{node.tipo}"
        if not node.hijos and contorno_hojas:
            graph.node(str(node.id), label, style = "filled", fillcolor = 'lightgrey', peripheries = '2')
        else:
            graph.node(str(node.id), label, style = "filled", fillcolor = 'white')
        for hijo in node.hijos:
            graph.edge(str(node.id), str(hijo.id))
            generar_nodos(hijo)
    generar_nodos(raiz)
    return graph

# Función que realiza en algoritmo analizador sintáctico.
def analizador_sintactico(lista_de_tokens, tabla_ll1):
    '''
    if lista_de_tokens[-1].tipo == "$":
        entrada = " ".join([token.tipo for token in lista_de_tokens[:-1]])
    else:
        entrada = " ".join([token.tipo for token in lista_de_tokens])
    print(f"\nEntrada a procesar: {entrada}")
    '''
    errores_sintacticos = []
    pila = []
    inicial = tabla_ll1.index[0]
    contador = 0
    nodo_dolar = Nodo(contador, "$", None, None, None, True)
    nodo_inicio = Nodo(contador + 1, inicial, None, None, None, False)
    pila.append(nodo_dolar)
    pila.append(nodo_inicio)
    nodoPadre = nodo_inicio
    arbol = nodoPadre
    contador += 2
    indice = 0
    while pila:
        #print(f"{[s.tipo for s in pila]}")
        #print(f"{[s.tipo for s in pila[::-1]]}") # Pila inversa
        cima = pila.pop()
        if cima.terminal and indice < len(lista_de_tokens) and lista_de_tokens[indice].tipo == cima.tipo:
            token_actual = lista_de_tokens[indice]
            cima.valor = token_actual.valor
            cima.linea = token_actual.linea
            cima.columna = token_actual.columna
            indice += 1
        elif cima.terminal:
            return False, None
        elif cima.tipo in tabla_ll1.index:
            if indice < len(lista_de_tokens):
                token_actual = lista_de_tokens[indice].tipo
                try:
                    produccion = tabla_ll1.at[cima.tipo, token_actual]
                    if produccion:
                        if produccion == 'e':
                            nodo_e = Nodo(contador, "e", "e", None, None, True)
                            cima.añadir_hijo(nodo_e)
                            contador += 1
                        else:
                            simbolos = produccion.split()
                            nuevos_hijos = []
                            for simbolo in simbolos:
                                es_terminal = simbolo in [token.tipo for token in lista_de_tokens]
                                nodo_hijo = Nodo(contador, simbolo, None, None, None, es_terminal)
                                nuevos_hijos.append(nodo_hijo)
                                contador += 1
                            for hijo in reversed(nuevos_hijos):
                                pila.append(hijo)
                            for hijo in nuevos_hijos:
                                cima.añadir_hijo(hijo)
                    else:
                        token_error = lista_de_tokens[indice]
                        error = ErrorSintactico(cima.tipo, "e", token_error.linea, token_error.columna)
                        errores_sintacticos.append(error)
                        return False, None, errores_sintacticos
                except KeyError:
                    token_error = lista_de_tokens[indice]
                    error = ErrorSintactico(cima.tipo, "", token_error.linea, token_error.columna)
                    errores_sintacticos.append(error)
                    return False, None, errores_sintacticos
            else:
                token_error = lista_de_tokens[indice]
                error = ErrorSintactico("", "", token_error.linea, token_error.columna)
                errores_sintacticos.append(error)
                return False, None, errores_sintacticos
        else:
            token_error = lista_de_tokens[indice]
            error = ErrorSintactico(cima.tipo, "", token_error.linea, token_error.columna)
            errores_sintacticos.append(error)
            return False, None, errores_sintacticos
    exito = indice == len(lista_de_tokens)
    return exito, arbol, errores_sintacticos if exito else None

# Cargamos la tabla LL1.
tabla_ll1 = cargar_tabla_ll1(ruta_archivo_ll1)

# Llamada al analizador sintáctico.
respuesta, arbol_sintactico, errores_sintacticos = analizador_sintactico(lista_de_tokens, tabla_ll1)

# Definimos nombre del arbol y del atributo que deseamos mostrar en el .dot.
nombre_arbol = f"arbol-{os.path.splitext(archivo)[0]}"
atributo_arbol = "tipo" # Evaluar el atributo del nodo que se quiere ver

# Mostrar el resultado del análisis léxico.
mostrar_resultado_lexico(lista_errores_lexicos)

# Verificamos el análisis sintáctico.
if respuesta:
    output_folder = 'salida-arboles'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    graph = arbolSintactico(arbol_sintactico, True, atributo_arbol) 
    dot_contenido = graph.source
    salida_arbol_directorio = os.path.join(output_folder, nombre_arbol + ".dot")
    with open(salida_arbol_directorio, 'w') as f:
        f.write(dot_contenido)
    with open(salida_arbol_directorio, 'r+') as file:
        content = file.read()
        if content.endswith(('\n', '\r')):
            content = content.rstrip('\n\r')
            file.seek(0)
            file.write(content)
            file.truncate()
    print("\nAnálisis sintáctico exitoso ✅✅\n")
    print(f"Generador del arbol sintáctico: {nombre_arbol}.dot creado en: {salida_arbol_directorio}\n")
else:
    print("\n❌❌❌ Análisis sintáctico fallido ❌❌❌\n")
    print("Error sintáctico reconocido:")
    for error in errores_sintacticos:
        print(error)
    print()