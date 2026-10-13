import heapq
from estado_juego import EstadoJuego, MOVIMIENTOS

def distancia_manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

class Planificador:
    def __init__(self):
        pass

    def calcular_heuristica(self, estado):
        if estado.es_victoria():
            return 0

        costo_h = 0
        jugador = estado.pos_jugador

        # 1. Si quedan diamantes: perseguir la gema más cercana
        if estado.diamantes:
            dist_min_diamante = min(distancia_manhattan(jugador, d) for d in estado.diamantes)
            costo_h += dist_min_diamante
            costo_h += len(estado.diamantes) * 12

            # Si hay puertas verdes cerradas y no tiene llave, buscar la llave
            if estado.puertas_verdes and not estado.tiene_llave and estado.llaves:
                dist_llave = min(distancia_manhattan(jugador, k) for k in estado.llaves)
                costo_h += dist_llave * 3
        elif estado.escalera:
            # 2. Con 0 diamantes: correr a la escalera
            costo_h += distancia_manhattan(jugador, estado.escalera)

        return costo_h

    def resolver(self, estado_inicial, max_nodos=1000000):
        """
        A* optimizado para mapas densos en rocas.
        Permite empujes tácticos a rincones sin podas falsas.
        """
        contador_nodos = 0
        frontera = []
        
        h_ini = self.calcular_heuristica(estado_inicial)
        heapq.heappush(frontera, (h_ini, 0, contador_nodos, estado_inicial, []))

        mejores_costos = {
            estado_inicial.clave_estado(): 0
        }

        while frontera:
            f, g, _, estado_actual, acciones = heapq.heappop(frontera)

            clave_actual = estado_actual.clave_estado()
            if g > mejores_costos.get(clave_actual, float("inf")):
                continue

            if estado_actual.es_victoria():
                print(f"🎯 ¡Solución encontrada en {len(acciones)} pasos! Nodos explorados: {contador_nodos}")
                return acciones

            if contador_nodos >= max_nodos:
                print(f"⚠️ Límite de búsqueda alcanzado ({max_nodos} nodos).")
                return None

            for accion, nuevo_estado in estado_actual.obtener_acciones_validas():
                nuevo_g = g + 1
                clave = nuevo_estado.clave_estado()
                mejor_g_conocido = mejores_costos.get(clave, float("inf"))

                if nuevo_g >= mejor_g_conocido:
                    continue

                mejores_costos[clave] = nuevo_g
                contador_nodos += 1
                nuevo_h = self.calcular_heuristica(nuevo_estado)
                nuevo_f = nuevo_g + nuevo_h

                nuevo_camino = list(acciones)
                nuevo_camino.append(accion)

                heapq.heappush(frontera, (nuevo_f, nuevo_g, contador_nodos, nuevo_estado, nuevo_camino))

        print("❌ No se encontró camino hacia la victoria.")
        return None