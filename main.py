import math
import copy
import heapq
import json

INF = math.inf

# Matriz original asimétrica
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

def calcular_cota_ingenua(matriz_base, path):
    # Suma costo acumulado
    costo_acumulado = sum(matriz_base[path[i]][path[i+1]] for i in range(len(path)-1))
    
    # Mínimos absolutos salientes para ciudades que aún no han partido
    N = len(matriz_base)
    ciudades_que_partieron = path[:-1]
    ciudades_restantes = [i for i in range(N) if i not in ciudades_que_partieron]
    
    suma_minimos = 0
    for i in ciudades_restantes:
        m = min(matriz_base[i])
        if m != INF:
            suma_minimos += m
            
    return costo_acumulado + suma_minimos

def generar_hijo(padre, destino, generador_id, tipo_cota="robusta", matriz_base=None):
    nuevo_path = padre.path + [destino]
    nueva_matriz = copy.deepcopy(padre.matrix)
    N = len(nueva_matriz)
    
    origen = padre.path[-1]
    costo_arista = nueva_matriz[origen][destino]
    
    for k in range(N):
        nueva_matriz[origen][k] = INF
        nueva_matriz[k][destino] = INF
        
    nueva_matriz[destino][padre.path[0]] = INF
    
    if tipo_cota == "robusta":
        costo_reduccion = reducir_matriz(nueva_matriz)
        nuevo_bound = padre.bound + costo_arista + costo_reduccion
    else:
        nuevo_bound = calcular_cota_ingenua(matriz_base, nuevo_path)
    
    return Nodo(generador_id(), nuevo_path, nueva_matriz, nuevo_bound, padre.level + 1)

def exportar_graphviz(nodos_historicos, filename):
    with open(filename, 'w') as f:
        f.write('digraph TSP_Tree {\n')
        f.write('    node [shape=box, fontname="Arial"];\n')
        for nodo in nodos_historicos:
            camino_str = "[" + "->".join([nombres_ciudades[i] for i in nodo.path]) + "]"
            color = "black"
            if nodo.estado == "Solucion Completa": color = "green"
            elif "Podado" in nodo.estado: color = "red"
            elif nodo.estado == "Expandido": color = "blue"
            
            label = f'ID: {nodo.id}\\nCamino: {camino_str}\\nCota: {nodo.bound}\\nEstado: {nodo.estado}'
            f.write(f'    Node{nodo.id} [label="{label}", color={color}];\n')
            for hijo_id in nodo.hijos:
                f.write(f'    Node{nodo.id} -> Node{hijo_id};\n')
        f.write('}\n')

def exportar_json(nodos_historicos, filename):
    data = [{
        "id": n.id,
        "camino": [nombres_ciudades[i] for i in n.path],
        "cota": n.bound,
        "estado": n.estado
    } for n in nodos_historicos]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def ejecutar_tsp(nombre_escenario, estrategia="best-first", matriz=matriz_original, tipo_cota="robusta"):
    N = len(matriz)
    matriz_raiz = copy.deepcopy(matriz)
    
    if tipo_cota == "robusta":
        cota_raiz = reducir_matriz(matriz_raiz)
    else:
        cota_raiz = calcular_cota_ingenua(matriz, [0])
    
    id_counter = 0
    def get_id():
        nonlocal id_counter
        id_counter += 1
        return id_counter
        
    raiz = Nodo(0, [0], matriz_raiz, cota_raiz, 0)
    frontera = [raiz]
    nodos_historicos = [raiz]
    
    mejor_costo = INF
    mejor_camino = None
    
    while frontera:
        nodo_actual = heapq.heappop(frontera) if estrategia == "best-first" else frontera.pop()
            
        if nodo_actual.bound >= mejor_costo:
            nodo_actual.estado = "Podado por Cota"
            continue
            
        if nodo_actual.level == N - 1:
            nodo_actual.estado = "Solucion Completa"
            if mejor_costo == INF:
                print(f"[{nombre_escenario}] 1ra Incumbente -> NODO ID: {nodo_actual.id} | Costo: {nodo_actual.bound}")
            if nodo_actual.bound < mejor_costo:
                mejor_costo = nodo_actual.bound
                mejor_camino = nodo_actual.path
            continue
            
        nodo_actual.estado = "Expandido"
        
        hijos_temporales = []
        for destino in range(N):
            if destino not in nodo_actual.path:
                nuevo_hijo = generar_hijo(nodo_actual, destino, get_id, tipo_cota, matriz)
                nodo_actual.hijos.append(nuevo_hijo.id)
                hijos_temporales.append(nuevo_hijo)
                nodos_historicos.append(nuevo_hijo)
                
        if estrategia == "lifo":
            hijos_temporales.sort(key=lambda x: x.bound, reverse=True)
            frontera.extend(hijos_temporales)
        else:
            for h in hijos_temporales:
                heapq.heappush(frontera, h)
                
    exportar_graphviz(nodos_historicos, f"grafo_{nombre_escenario}.dot")
    exportar_json(nodos_historicos, f"datos_{nombre_escenario}.json")
    print(f"[{nombre_escenario}] Completado. Nodos en memoria: {len(nodos_historicos)}. Costo Óptimo: {mejor_costo}\n")

# --- EJECUCIÓN DE LOS 4 ESCENARIOS ---

# 1. Pregunta 4.1: Base LIFO
ejecutar_tsp("Base_LIFO", estrategia="lifo")

# 2. Pregunta 4.1: Base Best-First
ejecutar_tsp("Base_BestFirst", estrategia="best-first")

# 3. Pregunta 4.2: Acotación Ingenua
ejecutar_tsp("Cota_Ingenua_BestFirst", estrategia="best-first", tipo_cota="ingenua")

# 4. Pregunta 4.3: Matriz Perturbada (Efecto Espejismo)
matriz_perturbada = copy.deepcopy(matriz_original)
matriz_perturbada[2][4] = 99  # C -> E = 99
ejecutar_tsp("Matriz_Perturbada_BestFirst", estrategia="best-first", matriz=matriz_perturbada)