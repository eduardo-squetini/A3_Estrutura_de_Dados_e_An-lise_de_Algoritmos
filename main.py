import heapq
import math
import time
import tracemalloc
from typing import List, Dict

# --------------------------------------------------------------------------------
# Classes e Estruturas de Dados
# --------------------------------------------------------------------------------

class Entrega:
    def __init__(self, id_entrega, destino, peso, prazo):
        self.id_entrega = id_entrega
        self.destino = destino    # nó do grafo
        self.peso = peso
        self.prazo = prazo

class Caminhao:
    def __init__(self, id_caminhao, centro_base, capacidade_maxima, horas_operacao_dia):
        self.id_caminhao = id_caminhao
        self.centro_base = centro_base
        self.capacidade_maxima = capacidade_maxima
        self.horas_operacao_dia = horas_operacao_dia

class Aresta:
    def __init__(self, destino, distancia):
        self.destino = destino
        self.distancia = distancia

class Grafo:
    def __init__(self, numero_de_nos):
        self.numero_de_nos = numero_de_nos
        self.adj = [[] for _ in range(numero_de_nos)]
    
    def adicionar_aresta(self, u, v, distancia):
        # Grafo não-direcionado
        self.adj[u].append(Aresta(v, distancia))
        self.adj[v].append(Aresta(u, distancia))

# --------------------------------------------------------------------------------
# Funções de Suporte
# --------------------------------------------------------------------------------

def dijkstra(grafo: Grafo, origem: int) -> List[float]:
    dist = [math.inf] * grafo.numero_de_nos
    dist[origem] = 0.0
    heap = [(0.0, origem)]
    
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for aresta in grafo.adj[u]:
            v = aresta.destino
            nd = d + aresta.distancia
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist

def velocidade_media():
    return 60.0

def calcular_tempo(distancia_total: float) -> float:
    return distancia_total / velocidade_media()

def atribuir_entregas_a_centros(grafo: Grafo, entregas: List[Entrega], centros: List[int]) -> Dict[int, List[Entrega]]:
    dist_centros = {}
    for c in centros:
        dist_centros[c] = dijkstra(grafo, c)
    
    alocacao_centros = {c: [] for c in centros}
    for entrega in entregas:
        if entrega.destino >= grafo.numero_de_nos:
            # Destino inválido
            print(f"Entrega {entrega.id_entrega} tem destino {entrega.destino} fora do range do grafo.")
            continue

        melhor_centro = None
        melhor_dist = math.inf
        for c in centros:
            dist_destino = dist_centros[c][entrega.destino]
            if dist_destino < melhor_dist:
                melhor_dist = dist_destino
                melhor_centro = c

        # Verifica acessibilidade
        if melhor_centro is None or math.isinf(melhor_dist):
            print(f"Entrega {entrega.id_entrega} (destino {entrega.destino}) é inacessível a partir de todos os centros.")
            continue

        alocacao_centros[melhor_centro].append(entrega)
    return alocacao_centros

def distancia_minima_entre_nos(grafo: Grafo, origem: int, destino: int) -> float:
    dist = dijkstra(grafo, origem)
    return dist[destino]

def roteamento_entregas(grafo: Grafo, entregas: List[Entrega], caminhoes: List[Caminhao], centros: List[int]):
    alocacao = atribuir_entregas_a_centros(grafo, entregas, centros)
    caminhoes_por_centro = {c: [] for c in centros}
    for cam in caminhoes:
        caminhoes_por_centro[cam.centro_base].append(cam)
    
    rotas_resultado = []

    for c in centros:
        entregas_centro = alocacao[c]
        entregas_centro.sort(key=lambda e: e.destino)
        
        caminhoes_c = caminhoes_por_centro[c]
        if not caminhoes_c and entregas_centro:
            print(f"Sem caminhões no centro {c}, não é possível atender essas entregas.")
            continue
        
        def fechar_rota(rota_corrente_entregas, destinos_correntes, cam_atual):
            if not rota_corrente_entregas:
                return None
            distancia_total = 0.0
            no_atual = c
            for ddd in destinos_correntes:
                distancia_total += distancia_minima_entre_nos(grafo, no_atual, ddd)
                no_atual = ddd
            distancia_total += distancia_minima_entre_nos(grafo, no_atual, c)
            tempo_total = calcular_tempo(distancia_total)
            return {
                "id_caminhao": cam_atual.id_caminhao,
                "centro_base": c,
                "entregas": [e.id_entrega for e in rota_corrente_entregas],
                "rota": [c] + destinos_correntes + [c],
                "distancia_total": distancia_total,
                "tempo_total_horas": tempo_total
            }
        
        rota_corrente_entregas = []
        destinos_correntes = []
        carga_corrente = 0.0
        cam_index = 0
        
        for e in entregas_centro:
            if cam_index >= len(caminhoes_c):
                print(f"Centro {c}: Ficaram entregas não alocadas por falta de caminhões suficientes.")
                break
            cam_atual = caminhoes_c[cam_index]
            
            potencial_destinos = destinos_correntes + [e.destino]
            distancia_test = 0.0
            no_atual = c
            for ddd in potencial_destinos:
                distancia_test += distancia_minima_entre_nos(grafo, no_atual, ddd)
                no_atual = ddd
            distancia_test += distancia_minima_entre_nos(grafo, no_atual, c)
            
            tempo_test = calcular_tempo(distancia_test)
            potencial_carga = carga_corrente + e.peso
            
            if potencial_carga <= cam_atual.capacidade_maxima and tempo_test <= cam_atual.horas_operacao_dia:
                rota_corrente_entregas.append(e)
                carga_corrente = potencial_carga
                destinos_correntes.append(e.destino)
            else:
                rota_final = fechar_rota(rota_corrente_entregas, destinos_correntes, cam_atual)
                if rota_final:
                    rotas_resultado.append(rota_final)
                
                cam_index += 1
                if cam_index >= len(caminhoes_c):
                    print(f"Centro {c}: Sem caminhões adicionais, entregas restantes não serão atendidas.")
                    break
                rota_corrente_entregas = [e]
                destinos_correntes = [e.destino]
                carga_corrente = e.peso
        
        if rota_corrente_entregas and cam_index < len(caminhoes_c):
            rota_final = fechar_rota(rota_corrente_entregas, destinos_correntes, caminhoes_c[cam_index])
            if rota_final:
                rotas_resultado.append(rota_final)
    
    return rotas_resultado


# --------------------------------------------------------------------------------
# Cenário de Teste Ajustado
# --------------------------------------------------------------------------------

def cenario_pequeno_garantido():
    """
    Cenário simples e garantido:
    - 4 centros (0,1,2,3)
    - 10 nós adicionais para destinos (4 a 13)
    - Cada centro conecta a alguns destinos próximos.
    - 8 caminhões, 2 por centro, capacidade folgada.
    - 10 entregas distribuídas nesses destinos.
    """
    centros = [0, 1, 2, 3]
    numero_nos = 14  # 0-3 centros, 4-13 destinos
    grafo = Grafo(numero_nos)
    
    # Conexões garantidas: cada centro liga a pelo menos dois destinos
    grafo.adicionar_aresta(0, 4, 50.0)
    grafo.adicionar_aresta(0, 5, 60.0)
    grafo.adicionar_aresta(1, 6, 70.0)
    grafo.adicionar_aresta(1, 7, 80.0)
    grafo.adicionar_aresta(2, 8, 90.0)
    grafo.adicionar_aresta(2, 9, 100.0)
    grafo.adicionar_aresta(3, 10,110.0)
    grafo.adicionar_aresta(3, 11,120.0)
    
    # Adicionar algumas conexões extras entre destinos para diversificar
    grafo.adicionar_aresta(5, 12, 50.0)
    grafo.adicionar_aresta(6, 13, 60.0)

    # Entregas (todas em destinos existentes e conectados)
    entregas = [
        Entrega(1, 4, 100, 1625000000),
        Entrega(2, 5, 100, 1625100000),
        Entrega(3, 6, 50, 1625200000),
        Entrega(4, 7, 80, 1625300000),
        Entrega(5, 8, 90, 1625400000),
        Entrega(6, 9, 70, 1625500000),
        Entrega(7, 10,60, 1625600000),
        Entrega(8, 11,50, 1625700000),
        Entrega(9, 12,40, 1625800000),
        Entrega(10,13,30,1625900000)
    ]
    
    caminhoes = [
        Caminhao(1, 0, 1000, 8),
        Caminhao(2, 0, 1000, 8),
        Caminhao(3, 1, 1000, 8),
        Caminhao(4, 1, 1000, 8),
        Caminhao(5, 2, 1000, 8),
        Caminhao(6, 2, 1000, 8),
        Caminhao(7, 3, 1000, 8),
        Caminhao(8, 3, 1000, 8),
    ]
    
    return grafo, entregas, caminhoes, centros


def cenario_medio():
    centros = [0, 1, 2, 3]
    numero_nos = 200
    grafo = Grafo(numero_nos)
    
    # Conectividade: criar um "caminho" linear conectando cada centro a um conjunto de nós
    # Centro 0 conecta nós 4 a 50
    for i in range(4, 50):
        grafo.adicionar_aresta(i, i+1, 10.0)  # caminho linear
    
    # Centro 0 -> nó 4
    grafo.adicionar_aresta(0, 4, 20.0)
    
    # Centro 1 -> nó 60, daí 60 a 100 linear
    grafo.adicionar_aresta(1, 60, 20.0)
    for i in range(60,100):
        grafo.adicionar_aresta(i, i+1, 15.0)
    
    # Centro 2 -> nó 110, daí 110 a 140 linear
    grafo.adicionar_aresta(2, 110, 25.0)
    for i in range(110,140):
        grafo.adicionar_aresta(i, i+1, 10.0)
    
    # Centro 3 -> nó 150, daí 150 a 180 linear
    grafo.adicionar_aresta(3, 150, 20.0)
    for i in range(150,180):
        grafo.adicionar_aresta(i, i+1, 12.0)
    
    # Entregas: 100 entregas distribuídas entre esses intervalos
    entregas = []
    for i in range(1, 101):
        # Alternar destinos entre as faixas conectadas a cada centro
        if i <= 25:
            destino = 4 + (i % 46)  # Algo entre 4 e 50
        elif i <= 50:
            destino = 60 + (i % 41) # Algo entre 60 e 100
        elif i <= 75:
            destino = 110 + (i % 31) # Algo entre 110 e 140
        else:
            destino = 150 + (i % 31) # Algo entre 150 e 180
        peso = 50 + (i % 20)
        prazo = 1625000000 + i*1000
        entregas.append(Entrega(i, destino, peso, prazo))
    
    caminhoes = []
    # 5 caminhões por centro (20 total)
    for c in centros:
        for k in range(5):
            capacidade = 500+(k*50)
            caminhoes.append(Caminhao(len(caminhoes)+1, c, capacidade, 8))
    
    return grafo, entregas, caminhoes, centros

def cenario_grande():
    centros = [0, 1, 2, 3]
    numero_nos = 1000
    grafo = Grafo(numero_nos)
    
    # Criar um "grid" simples: 20 linhas x 50 colunas (1000 nós)
    # Conectar centros a diferentes partes do grid.
    # Suponha centros: 
    # 0 -> canto superior esquerdo (nós 4 a 200)
    # 1 -> canto superior direito (nós 201 a 400)
    # 2 -> canto inferior esquerdo (nós 401 a 600)
    # 3 -> canto inferior direito (nós 601 a 800)
    # Criamos algumas linhas horizontais e verticais
    
    # Ligando centro 0 ao nó 4
    grafo.adicionar_aresta(0, 4, 30.0)
    # Conexões lineares da região 4 a 200
    for i in range(4,200):
        if i+1 < 200:
            grafo.adicionar_aresta(i, i+1, 10.0)
    
    # Centro 1 -> nó 201
    grafo.adicionar_aresta(1, 201, 25.0)
    for i in range(201,400):
        if i+1 <= 400:
            grafo.adicionar_aresta(i, i+1, 10.0)
    
    # Centro 2 -> nó 401
    grafo.adicionar_aresta(2, 401, 25.0)
    for i in range(401,600):
        if i+1 <= 600:
            grafo.adicionar_aresta(i, i+1, 11.0)
    
    # Centro 3 -> nó 601
    grafo.adicionar_aresta(3, 601, 25.0)
    for i in range(601,800):
        if i+1 <= 800:
            grafo.adicionar_aresta(i, i+1, 12.0)
    
    # Conectar as "regiões" com alguns corredores
    # Ex: conectar da região do centro 0 para a região do centro 1
    grafo.adicionar_aresta(100, 300, 50.0)
    grafo.adicionar_aresta(200, 500, 60.0)
    grafo.adicionar_aresta(400, 700, 70.0)
    
    # 500 entregas espalhadas:
    entregas = []
    for i in range(1, 501):
        # Alternar entre as faixas: vamos pegar destinos ao longo do range 4 a 800
        destino = 4 + (i % 796) # Entre 4 e 799
        peso = 50 + (i % 100)
        prazo = 1625000000 + i * 1000
        entregas.append(Entrega(i, destino, peso, prazo))
    
    caminhoes = []
    # 10 caminhões por centro (40 total)
    for c in centros:
        for k in range(10):
            capacidade = 300 + k*50
            horas = 8 if k < 5 else 10
            caminhoes.append(Caminhao(len(caminhoes)+1, c, capacidade, horas))
    
    return grafo, entregas, caminhoes, centros


def executar_cenario(nome_cenario, func_cenario):
    print(f"========== Executando {nome_cenario} ==========")
    grafo, entregas, caminhoes, centros = func_cenario()

    tracemalloc.start()
    start = time.time()
    rotas = roteamento_entregas(grafo, entregas, caminhoes, centros)
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Tempo de execução ({nome_cenario}):", end - start, "segundos")
    print(f"Consumo de memória ({nome_cenario}): Atual: {current/1024/1024:.2f} MB; Pico: {peak/1024/1024:.2f} MB")
    
    if rotas:
        print(f"Rotas obtidas ({nome_cenario}):")
        for r in rotas:
            print("-------------------------------------------------")
            print(f"Caminhão {r['id_caminhao']} (Base {r['centro_base']}):")
            print(f"  Rota: {r['rota']}")
            print(f"  Entregas: {r['entregas']}")
            print(f"  Distância Total: {r['distancia_total']:.2f} km")
            print(f"  Tempo Total: {r['tempo_total_horas']:.2f} h")
    else:
        print(f"Nenhuma rota encontrada em {nome_cenario} (pode indicar limitações no cenário).")
    print("==============================================\n")

if __name__ == "__main__":
    executar_cenario("Cenário Pequeno", cenario_pequeno_garantido)
    executar_cenario("Cenário Médio", cenario_medio)
    executar_cenario("Cenário Grande", cenario_grande)