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
archivo_ll1 = 'tabla_ll1.csv'  # Ingresar el nombre de la tabla.
ruta_archivo_ll1 = os.path.join(directorio, '..', 'tabla-ll1', archivo_ll1)

# Agregar el $ a la lista de tokens.
lista_de_tokens.append(Token("$", "$", None, None))

# Subclase para identificar un error sintáctico.
class ErrorSintactico(Error):
    def __init__(self, esperado, encontrado, linea, columna):
        mensaje = f"se esperaba {esperado}, pero se encontró {encontrado}"
        super().__init__(mensaje, linea, columna)

# Clase para la Tabla de Símbolos
class TablaSimbolos:
    def __init__(self, padre=None):
        self.simbolos = {}  # Diccionario de símbolos: nombre -> {tipo, categoria, parámetros, retorno}
        self.padre = padre  # Ámbito padre
        self.hijos = []  # Lista de ámbitos hijos (para funciones)

    def agregar_simbolo(self, nombre, tipo=None, categoria=None, parámetros=None, retorno=None):
        """Añade un símbolo al ámbito actual."""
        if nombre in self.simbolos:
            #print(f"Advertencia: Símbolo {nombre} ya definido en este ámbito, se sobrescribirá")
            errores_semanticos.append(f"❌ Error semántico: La variable '{nombre}' ya fue declarada.")
            #se usa return para ignorar la nueva declaracion
            return
        self.simbolos[nombre] = {
            'tipo': tipo,
            'categoria': categoria,
            'parámetros': parámetros if parámetros is not None else [],
            'retorno': retorno
        }
        print(f"Símbolo agregado: {nombre}, categoria: {categoria}, tipo: {tipo}, parámetros: {parámetros}, retorno: {retorno}")

    def buscar_simbolo(self, nombre):
        """Busca un símbolo en el ámbito actual o en los padres."""
        if nombre in self.simbolos:
            return self.simbolos[nombre]
        elif self.padre:
            return self.padre.buscar_simbolo(nombre)
        return None

    def entrar_ambito(self):
        """Crea un nuevo ámbito hijo y lo retorna."""
        nuevo_ambito = TablaSimbolos(padre=self)
        self.hijos.append(nuevo_ambito)
        print(f"Entrando a un nuevo ámbito. Total de hijos: {len(self.hijos)}")
        return nuevo_ambito

    def salir_ambito(self):
        """Retorna al ámbito padre."""
        print("Saliendo del ámbito")
        return self.padre if self.padre else self

# Función encargada de cargar una tabla LL1.
def cargar_tabla_ll1(direccion):
    df = pd.read_csv(direccion, index_col=0)
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

# Función para generar el Digraph del árbol sintáctico.
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
            graph.node(str(node.id), label, style="filled", fillcolor='lightgrey', peripheries='2')
        else:
            graph.node(str(node.id), label, style="filled", fillcolor='white')
        for hijo in node.hijos:
            graph.edge(str(node.id), str(hijo.id))
            generar_nodos(hijo)
    generar_nodos(raiz)
    return graph

#Lista de errores semanticos
errores_semanticos = []

#Verificar que las variables esten declaradas 
def verificar_variable(nodo, ambito_actual):
    if nodo.tipo == 'restofuncn' or nodo.tipo == 'restomain':
        ambito_actual = ambito_actual.hijos.pop(0)

    if nodo.tipo == 'id' and nodo.valor:
        simbolo = ambito_actual.buscar_simbolo(nodo.valor)
        if not simbolo:
            mensaje = f"❌ Error semántico: La variable '{nodo.valor}' no está declarada en la línea {nodo.linea}, columna {nodo.columna}"
            errores_semanticos.append(mensaje)
    for hijo in nodo.hijos:
        verificar_variable(hijo, ambito_actual)


# Función para generar el Digraph de la tabla de símbolos.
def generar_diagrama_tabla_simbolos(tabla_simbolos, graph=None, id_padre=None):
    if graph is None:
        graph = Digraph()
    id_nodo = str(id(tabla_simbolos))
    # Construir la etiqueta con los símbolos del ámbito
    lista_simbolos = []
    for nombre, attrs in tabla_simbolos.simbolos.items():
        if attrs['categoria'] == 'function':
            params_str = ', '.join([f"{p['nombre']}: {p['tipo']}" for p in attrs['parámetros']])
            lista_simbolos.append(f"{nombre} (parámetros: [{params_str}], retorno: {attrs['retorno']})")
        else:
            lista_simbolos.append(f"{nombre}: {attrs['tipo']}")
    etiqueta = f"Ámbito\n[{', '.join(lista_simbolos) if lista_simbolos else 'Sin símbolos'}]"
    graph.node(id_nodo, etiqueta, shape='box')
    if id_padre:
        graph.edge(id_padre, id_nodo)
    for hijo in tabla_simbolos.hijos:
        generar_diagrama_tabla_simbolos(hijo, graph, id_nodo)
    return graph

# Nueva función para generar una tabla de símbolos en formato CSV
def generar_tabla_simbolos_csv(tabla_simbolos, nombre_archivo, output_folder):
    """Genera una tabla de símbolos en formato CSV que indica el ámbito de cada símbolo."""
    datos_tabla = []
    
    def recorrer_ambitos(ambito_actual, nombre_ambito="Global"):
        # Procesar símbolos del ámbito actual
        for nombre, attrs in ambito_actual.simbolos.items():
            if attrs['categoria'] == 'function':
                params_str = ', '.join([f"{p['nombre']}: {p['tipo']}" for p in attrs['parámetros']]) if attrs['parámetros'] else '-'
                datos_tabla.append({
                    'Símbolo': nombre,
                    'Categoría': 'función',
                    'Tipo': '-',
                    'Ámbito': nombre_ambito,
                    'Parámetros': params_str,
                    'Retorno': attrs['retorno']
                })
            else:
                datos_tabla.append({
                    'Símbolo': nombre,
                    'Categoría': attrs['categoria'],
                    'Tipo': attrs['tipo'] if attrs['tipo'] else '-',
                    'Ámbito': nombre_ambito,
                    'Parámetros': '-',
                    'Retorno': '-'
                })
        # Procesar ámbitos hijos (ámbitos locales de funciones)
        for i, hijo in enumerate(ambito_actual.hijos):
            # Determinar el nombre del ámbito hijo (basado en la función padre)
            nombre_funcion = list(ambito_actual.simbolos.keys())[i] if i < len(ambito_actual.simbolos) else f"Ámbito_{i}"
            recorrer_ambitos(hijo, nombre_funcion)

    # Recorrer todos los ámbitos desde el global
    recorrer_ambitos(tabla_simbolos)

    # Crear un DataFrame con los datos
    df = pd.DataFrame(datos_tabla, columns=['Símbolo', 'Categoría', 'Tipo', 'Ámbito', 'Parámetros', 'Retorno'])
    
    # Guardar la tabla en un archivo CSV
    ruta_csv = os.path.join(output_folder, f"{nombre_archivo}-tabla-simbolos.csv")
    df.to_csv(ruta_csv, index=False, encoding='utf-8')
    print(f"Tabla de símbolos generada: {ruta_csv}")

# Funciones para construir la tabla de símbolos recorriendo el árbol sintáctico
def buscar_hijo(nodo, tipo):
    """Encuentra un hijo con el tipo especificado."""
    for hijo in nodo.hijos:
        if hijo.tipo == tipo:
            return hijo
    return None

def extraer_parametros(nodo_parametrosf):
    """Extrae los parámetros de un nodo 'parametrosf'."""
    parámetros = []
    if not nodo_parametrosf:
        return parámetros
    print(f"Extrayendo parámetros del nodo: {nodo_parametrosf.tipo}")
    # 'parametrosf' -> 'id tipodato masparametrosf' o vacío
    if not nodo_parametrosf.hijos:
        return parámetros  # Producción vacía
    nodo_id = buscar_hijo(nodo_parametrosf, 'id')
    nodo_tipodato = buscar_hijo(nodo_parametrosf, 'tipodato')
    nodo_masparametrosf = buscar_hijo(nodo_parametrosf, 'masparametrosf')
    if nodo_id and nodo_id.valor and nodo_tipodato and nodo_tipodato.hijos:
        tipo_param = nodo_tipodato.hijos[0].tipo
        parámetros.append({'nombre': nodo_id.valor, 'tipo': tipo_param})
        print(f"Parámetro encontrado: {nodo_id.valor}, tipo: {tipo_param}")
    else:
        print("No se encontró un parámetro en este nodo")
    if nodo_masparametrosf and nodo_masparametrosf.hijos:
        # 'masparametrosf' -> 'coma parametrosf' o vacío
        siguientes_params = buscar_hijo(nodo_masparametrosf, 'parametrosf')
        if siguientes_params:
            parámetros.extend(extraer_parametros(siguientes_params))
    return parámetros

def procesar_asignaciones(nodo_asignaciones, ambito):
    """Procesa un nodo 'asignaciones' para registrar variables."""
    print(f"Procesando nodo asignaciones: {nodo_asignaciones.tipo}")
    nodo_id = buscar_hijo(nodo_asignaciones, 'id')
    nodo_ext = buscar_hijo(nodo_asignaciones, 'ext')
    if nodo_id and nodo_id.valor and nodo_ext and nodo_ext.hijos:
        hijo_ext = nodo_ext.hijos[0]
        if hijo_ext.tipo == 'tipodato' and hijo_ext.hijos:
            tipo_var = hijo_ext.hijos[0].tipo
            ambito.agregar_simbolo(nodo_id.valor, tipo=tipo_var, categoria='variable')
            print(f"Variable registrada: {nodo_id.valor}, tipo: {tipo_var}")
        else:
            print("No se encontró tipo para la variable")
    else:
        print("No se encontró variable en asignaciones")

def procesar_instrucciones(nodo_masinstrucciones, ambito):
    """Procesa las instrucciones dentro de un nodo 'masinstrucciones'."""
    if not nodo_masinstrucciones:
        return
    print(f"Procesando nodo masinstrucciones: {nodo_masinstrucciones.tipo}")
    for hijo in nodo_masinstrucciones.hijos:
        print(f"Nodo hijo: {hijo.tipo}")
        if hijo.tipo == 'instruccion':
            hijo_instruccion = hijo.hijos[0] if hijo.hijos else None
            if hijo_instruccion and hijo_instruccion.tipo == 'asignaciones':
                procesar_asignaciones(hijo_instruccion, ambito)
        elif hijo.tipo == 'masinstrucciones':
            procesar_instrucciones(hijo, ambito)

def procesar_funcion(nodo_func, ambito):
    """Procesa un nodo 'restofuncn' o 'restomain' para registrar una función y su ámbito."""
    print(f"Procesando nodo función: {nodo_func.tipo}")
    if nodo_func.tipo == 'restomain':
        nombre_func = 'main'
        parámetros = []
        retorno = 'tentero'
        print("Función main encontrada")
    elif nodo_func.tipo == 'restofuncn':
        nodo_id = buscar_hijo(nodo_func, 'id')
        nombre_func = nodo_id.valor if nodo_id and nodo_id.valor else None
        if not nombre_func:
            print("Nombre de función no encontrado")
            return
        nodo_param = buscar_hijo(nodo_func, 'parametrosf')
        parámetros = extraer_parametros(nodo_param) if nodo_param else []
        nodo_opciondato = buscar_hijo(nodo_func, 'opciondato')
        retorno = 'tvacio'  # Valor por defecto
        if nodo_opciondato and nodo_opciondato.hijos:
            nodo_tipodato = buscar_hijo(nodo_opciondato, 'tipodato')
            if nodo_tipodato and nodo_tipodato.hijos:
                retorno = nodo_tipodato.hijos[0].tipo  # Extraer el tipo real (tentero, tflotante, etc.)
        print(f"Función encontrada: {nombre_func}, parámetros: {parámetros}, retorno: {retorno}")
    else:
        print("No es un nodo de función")
        return

    # Registrar la función en el ámbito actual
    ambito.agregar_simbolo(nombre_func, categoria='function', parámetros=parámetros, retorno=retorno)
    # Crear un nuevo ámbito para la función
    ambito_func = ambito.entrar_ambito()
    # Registrar los parámetros en el ámbito de la función
    for param in parámetros:
        ambito_func.agregar_simbolo(param['nombre'], tipo=param['tipo'], categoria='parametro')
    # Procesar las instrucciones dentro de la función para encontrar variables
    nodo_masinstrucciones = buscar_hijo(nodo_func, 'masinstrucciones')
    if nodo_masinstrucciones:
        procesar_instrucciones(nodo_masinstrucciones, ambito_func)

def construir_tabla_simbolos(arbol, tabla_simbolos):
    """Construye la tabla de símbolos recorriendo el árbol sintáctico."""
    if arbol.tipo != 'programaprincipal':
        print(f"El nodo raíz no es 'programaprincipal', se encontró: {arbol.tipo}")
        return
    print("Construyendo tabla de símbolos desde programaprincipal")
    # Procesar funciones definidas en el programa
    nodo_actual = arbol
    while nodo_actual and nodo_actual.tipo == 'programaprincipal':
        print(f"Procesando nodo programaprincipal con hijos: {[hijo.tipo for hijo in nodo_actual.hijos]}")
        # Buscar 'funcion' -> 'restofuncn' o 'opcionprincipal' -> 'restomain'/'restofuncn'
        nodo_funcion = buscar_hijo(nodo_actual, 'funcion')
        nodo_opcionprincipal = buscar_hijo(nodo_actual, 'opcionprincipal')
        if nodo_funcion and nodo_funcion.hijos:
            nodo_func = nodo_funcion.hijos[0]  # funcion -> restofuncn
            procesar_funcion(nodo_func, tabla_simbolos)
        elif nodo_opcionprincipal and nodo_opcionprincipal.hijos:
            nodo_func = nodo_opcionprincipal.hijos[0]  # opcionprincipal -> restomain/restofuncn
            procesar_funcion(nodo_func, tabla_simbolos)
        nodo_masfuncn = buscar_hijo(nodo_actual, 'masfuncn')
        if nodo_masfuncn and nodo_masfuncn.hijos:
            nodo_actual = nodo_masfuncn.hijos[0]  # masfuncn -> programaprincipal
        else:
            break

# Función que realiza el algoritmo analizador sintáctico.
def analizador_sintactico(lista_de_tokens, tabla_ll1):
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
        cima = pila.pop()
        if cima.terminal and indice < len(lista_de_tokens) and lista_de_tokens[indice].tipo == cima.tipo:
            token_actual = lista_de_tokens[indice]
            cima.valor = token_actual.valor
            cima.linea = token_actual.linea
            cima.columna = token_actual.columna
            indice += 1
        elif cima.terminal:
            return False, None, errores_sintacticos
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
    return exito, arbol, errores_sintacticos

# Cargamos la tabla LL1.
tabla_ll1 = cargar_tabla_ll1(ruta_archivo_ll1)

# Llamada al analizador sintáctico.
respuesta, arbol_sintactico, errores_sintacticos = analizador_sintactico(lista_de_tokens, tabla_ll1)

# Definimos nombre del árbol y del atributo que deseamos mostrar en el .dot.
nombre_arbol = f"arbol-{os.path.splitext(archivo)[0]}"
atributo_arbol = "tipo"  # Evaluar el atributo del nodo que se quiere ver

# Mostrar el resultado del análisis léxico.
mostrar_resultado_lexico(lista_errores_lexicos)

# Verificamos el análisis sintáctico.
if respuesta:
    output_folder = 'salida-arboles'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Generar el árbol sintáctico
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
    
    # Construir la tabla de símbolos recorriendo el árbol sintáctico
    tabla_simbolos = TablaSimbolos()
    construir_tabla_simbolos(arbol_sintactico, tabla_simbolos)
    
    # Generar la tabla de símbolos en formato CSV
    generar_tabla_simbolos_csv(tabla_simbolos, nombre_arbol, output_folder)
    
    verificar_variable(arbol_sintactico, tabla_simbolos)
    if errores_semanticos:
        print("\n🚨 Errores semánticos encontrados:")
        for err in errores_semanticos:
            print(err)
    else:
        print("\n✅ Verificación semántica exitosa: todas las variables están declaradas.")

    # Generar el árbol de ámbitos de la tabla de símbolos
    grafo_tabla_simbolos = generar_diagrama_tabla_simbolos(tabla_simbolos)
    ruta_tabla_simbolos = os.path.join(output_folder, f"{nombre_arbol}-symbol-table.dot")
    try:
        grafo_tabla_simbolos.render(ruta_tabla_simbolos, format='png', cleanup=True)
    except Exception as e:
        print(f"Error al generar el diagrama de la tabla de símbolos: {str(e)}")
    
    print("\nAnálisis sintáctico exitoso ✅✅\n")
    print(f"Generador del árbol sintáctico: {nombre_arbol}.dot creado en: {salida_arbol_directorio}\n")
    print(f"Árbol de ámbitos generado: {nombre_arbol}-symbol-table.png en: {output_folder}\n")
else:
    print("\n❌❌❌ Análisis sintáctico fallido ❌❌❌\n")
    print("Error sintáctico reconocido:")
    for error in errores_sintacticos:
        print(error)
    print()