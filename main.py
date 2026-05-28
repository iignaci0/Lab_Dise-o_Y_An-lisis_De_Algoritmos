import math
import copy
import heapq
import json

INF = math.inf

# Matriz saneada y mapeo de vértices
# A=0, B=1, C=2, D=3, E=4
matriz_original = [
    [INF, 14,  4, 10, 20],
    [14, INF,  7,  8, 12],
    [ 4,  5, INF, 16,  3],
    [11,  7, 16, INF,  2],
    [18, 10,  4,  2, INF]
]
nombres_ciudades = ["A", "B", "C", "D", "E"]

class Nodo:
    def __init__(self, id_nodo, path, matrix, bound, level):
        self.id = id_nodo
        self.path = path
        self.matrix = matrix
        self.bound = bound
        self.level = level
        self.estado = "Creado"
        self.hijos = []

    def __lt__(self, otro):
        # Operador para la Cola de Prioridad (Best-First)
        # Desempate secundario por nivel (profundidad)
        if self.bound == otro.bound:
            return self.level > otro.level 
        return self.bound < otro.bound

def reducir_matriz(matriz):
    N = len(matriz)
    reduccion_total = 0
    
    # Reducción de Filas
    for i in range(N):
        min_fila = min(matriz[i])
        if min_fila != INF and min_fila > 0:
            reduccion_total += min_fila
            for j in range(N):
                if matriz[i][j] != INF:
                    matriz[i][j] -= min_fila
                    
    # Reducción de Columnas
    for j in range(N):
        min_col = min([matriz[i][j] for i in range(N)])
        if min_col != INF and min_col > 0:
            reduccion_total += min_col
            for i in range(N):
                if matriz[i][j] != INF:
                    matriz[i][j] -= min_col
                    
    return reduccion_total

def generar_hijo(padre, destino, generador_id):
    nuevo_path = padre.path + [destino]
    nueva_matriz = copy.deepcopy(padre.matrix)
    N = len(nueva_matriz)
    
    origen = padre.path[-1]
    costo_arista = nueva_matriz[origen][destino]
    
    # Inhabilitar fila de origen y columna de destino
    for k in range(N):
        nueva_matriz[origen][k] = INF
        nueva_matriz[k][destino] = INF
        
    # Prevenir ciclos prematuros inhabilitando el retorno a la raíz
    nueva_matriz[destino][padre.path[0]] = INF
    
    costo_reduccion = reducir_matriz(nueva_matriz)
    nuevo_bound = padre.bound + costo_arista + costo_reduccion
    
    return Nodo(generador_id(), nuevo_path, nueva_matriz, nuevo_bound, padre.level + 1)

def exportar_graphviz(nodos_historicos, incumbente_costo, filename="tsp_tree.dot"):
    with open(filename, 'w') as f:
        f.write('digraph TSP_Tree {\n')
        f.write('    node [shape=box, fontname="Arial"];\n')
        
        for nodo in nodos_historicos:
            # Parsear camino
            camino_str = "[" + "->".join([nombres_ciudades[i] for i in nodo.path]) + "]"
            
            # Asignación cromática y lógica de estado
            color = "black"
            if nodo.estado == "Solucion Completa":
                color = "green"
            elif "Podado" in nodo.estado:
                color = "red"
            elif nodo.estado == "Expandido":
                color = "blue"
            
            label = f'ID: {nodo.id}\\nCamino: {camino_str}\\nCota: {nodo.bound}\\nEstado: {nodo.estado}'
            f.write(f'    Node{nodo.id} [label="{label}", color={color}];\n')
            
            # Escribir aristas (relaciones topológicas)
            for hijo_id in nodo.hijos:
                f.write(f'    Node{nodo.id} -> Node{hijo_id};\n')
                
        f.write('}\n')

def ejecutar_tsp(estrategia="best-first"):
    N = len(matriz_original)
    matriz_raiz = copy.deepcopy(matriz_original)
    reduccion_raiz = reducir_matriz(matriz_raiz)
    
    id_counter = 0
    def get_id():
        nonlocal id_counter
        id_counter += 1
        return id_counter
        
    raiz = Nodo(0, [0], matriz_raiz, reduccion_raiz, 0)
    
    frontera = [raiz]
    nodos_historicos = [raiz]
    
    mejor_costo = INF
    mejor_camino = None
    
    while frontera:
        if estrategia == "best-first":
            nodo_actual = heapq.heappop(frontera)
        elif estrategia == "lifo":
            nodo_actual = frontera.pop() # Último en entrar, primero en salir
            
        if nodo_actual.bound >= mejor_costo:
            nodo_actual.estado = "Podado por Cota"
            continue
            
        if nodo_actual.level == N - 1:
            nodo_actual.estado = "Solucion Completa"
            
            if mejor_costo == INF:
                print(f"[AUDITORIA {estrategia.upper()}] Primera incumbente (hoja) procesada -> NODO ID: {nodo_actual.id} | Costo temporal: {nodo_actual.bound}")
            
            if nodo_actual.bound < mejor_costo:
                mejor_costo = nodo_actual.bound
                mejor_camino = nodo_actual.path
            continue
            
        nodo_actual.estado = "Expandido"
        
        # Generar ramificaciones
        hijos_temporales = []
        for destino in range(N):
            if destino not in nodo_actual.path:
                nuevo_hijo = generar_hijo(nodo_actual, destino, get_id)
                nodo_actual.hijos.append(nuevo_hijo.id)
                hijos_temporales.append(nuevo_hijo)
                nodos_historicos.append(nuevo_hijo)
                
        # Para LIFO, ordenar descendente por bound si se desea desempatar,
        # o simplemente inyectar en orden reverso para mantener coherencia lexicográfica.
        if estrategia == "lifo":
            hijos_temporales.sort(key=lambda x: x.bound, reverse=True)
            for h in hijos_temporales:
                frontera.append(h)
        else:
            for h in hijos_temporales:
                heapq.heappush(frontera, h)
                
    exportar_graphviz(nodos_historicos, mejor_costo, f"tsp_tree_{estrategia}.dot")
    # AQUI INVOCAS LA CREACION DEL JSON, USANDO EL NOMBRE DE LA ESTRATEGIA
    exportar_json(nodos_historicos, f"nodos_{estrategia}.json")
    print(f"Estrategia [{estrategia.upper()}]: Incumbente Final Costo {mejor_costo}, Camino {[nombres_ciudades[i] for i in mejor_camino]}")
def exportar_json(nodos_historicos, filename="nodos.json"):
    # Filtra y transforma los objetos nodo a diccionarios
    data = []
    for n in nodos_historicos:
        data.append({
            "id": n.id,
            "camino": [nombres_ciudades[i] for i in n.path],
            "cota": n.bound,
            "estado": n.estado
        })
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# Ejecución de ambos escenarios solicitados en Pregunta 4.1
ejecutar_tsp(estrategia="lifo")
ejecutar_tsp(estrategia="best-first")
