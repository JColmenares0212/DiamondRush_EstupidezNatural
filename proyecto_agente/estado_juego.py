import numpy as np

# Constantes sincronizadas con vision.py
ID_VACIO = 0
ID_PARED = 1
ID_DIAMANTE = 2
ID_RELIQUIA = 2
ID_PIEDRA = 3
ID_HUECO = 4
ID_HUECO_LLENO = 5
ID_PUAS_INACTIVAS = 6
ID_PUAS_ACTIVAS = 7
ID_LAVA = 8
ID_LLAVE = 9
ID_PUERTA_VERDE = 10
ID_PLATAFORMA = 11
ID_PUERTA_METALICA = 12
ID_ESCALERA_SELLADA = 13
ID_ESCALERA_ABIERTA = 14
ID_PUERTA_METALICA_ABIERTA = 15
ID_PLATAFORMA_PIEDRA = 16

MOVIMIENTOS = {
    'ARRIBA': (-1, 0),
    'ABAJO': (1, 0),
    'IZQUIERDA': (0, -1),
    'DERECHA': (0, 1)
}

class EstadoJuego:
    def __init__(self, filas=12, columnas=8):
        self.filas = filas
        self.columnas = columnas
        
        # Posición del jugador (r, c)
        self.pos_jugador = None
        self.tiene_llave = False
        
        # Elementos dinámicos
        self.piedras = set()
        self.diamantes = set()
        self.llaves = set()
        
        # Elementos estructurales
        self.paredes = set()
        self.huecos = set()
        self.huecos_llenos = set()
        self.lava = set()
        self.puas_activas = set()
        self.puas_inactivas = set()
        self.puertas_verdes = set()
        self.plataformas = set()
        self.puertas_metalicas = set()
        self.puertas_metalicas_abiertas_visuales = set()
        self.relaciones_plataforma_puerta = {}
        self.escalera = None
        
        self.total_gemas_objetivo = 0

    @classmethod
    def desde_matriz_vision(
        cls,
        matriz,
        pos_jugador,
        tiene_llave=False,
        relaciones_plataforma_puerta=None
    ):
        estado = cls(filas=matriz.shape[0], columnas=matriz.shape[1])
        estado.pos_jugador = pos_jugador
        estado.tiene_llave = tiene_llave
        estado.relaciones_plataforma_puerta = {
            plataforma: (
                {puertas}
                if isinstance(puertas, tuple)
                and len(puertas) == 2
                and all(isinstance(valor, int) for valor in puertas)
                else set(puertas)
            )
            for plataforma, puertas in (relaciones_plataforma_puerta or {}).items()
        }

        for r in range(estado.filas):
            for c in range(estado.columnas):
                val = matriz[r, c]
                coord = (r, c)

                if val == ID_PARED:
                    estado.paredes.add(coord)
                elif val == ID_DIAMANTE:
                    estado.diamantes.add(coord)
                elif val == ID_PIEDRA:
                    estado.piedras.add(coord)
                elif val == ID_HUECO:
                    estado.huecos.add(coord)
                elif val == ID_HUECO_LLENO:
                    estado.huecos_llenos.add(coord)
                elif val == ID_PUAS_INACTIVAS:
                    estado.puas_inactivas.add(coord)
                elif val == ID_PUAS_ACTIVAS:
                    estado.puas_activas.add(coord)
                elif val == ID_LAVA:
                    estado.lava.add(coord)
                elif val == ID_LLAVE:
                    estado.llaves.add(coord)
                elif val == ID_PUERTA_VERDE:
                    estado.puertas_verdes.add(coord)
                elif val == ID_PLATAFORMA:
                    estado.plataformas.add(coord)
                elif val == ID_PUERTA_METALICA:
                    estado.puertas_metalicas.add(coord)
                elif val == ID_PUERTA_METALICA_ABIERTA:
                    estado.puertas_metalicas.add(coord)
                    estado.puertas_metalicas_abiertas_visuales.add(coord)
                elif val in (ID_ESCALERA_SELLADA, ID_ESCALERA_ABIERTA):
                    estado.escalera = coord
                elif val == ID_PLATAFORMA_PIEDRA:
                    estado.plataformas.add(coord)
                    estado.piedras.add(coord)

        estado.total_gemas_objetivo = len(estado.diamantes)
        return estado

    def copiar(self):
        """Copia rápida del estado para simulación sin colisiones de memoria."""
        nuevo = EstadoJuego(self.filas, self.columnas)
        nuevo.pos_jugador = self.pos_jugador
        nuevo.tiene_llave = self.tiene_llave
        nuevo.escalera = self.escalera
        nuevo.total_gemas_objetivo = self.total_gemas_objetivo

        # Elementos dinámicos se copian
        nuevo.piedras = set(self.piedras)
        nuevo.diamantes = set(self.diamantes)
        nuevo.llaves = set(self.llaves)
        nuevo.huecos = set(self.huecos)
        nuevo.huecos_llenos = set(self.huecos_llenos)
        nuevo.puas_activas = set(self.puas_activas)
        nuevo.puas_inactivas = set(self.puas_inactivas)
        nuevo.puertas_verdes = set(self.puertas_verdes)

        # Referencias directas para elementos invariables
        nuevo.paredes = self.paredes
        nuevo.lava = self.lava
        nuevo.plataformas = self.plataformas
        nuevo.puertas_metalicas = self.puertas_metalicas
        nuevo.puertas_metalicas_abiertas_visuales = set(
            self.puertas_metalicas_abiertas_visuales
        )
        nuevo.relaciones_plataforma_puerta = {
            plataforma: set(puertas)
            for plataforma, puertas in self.relaciones_plataforma_puerta.items()
        }
        return nuevo

    def puerta_metalica_abierta(self, posicion):
        """Indica si una puerta concreta está abierta en este estado."""
        return (
            posicion not in self.puertas_metalicas
            or posicion in self.puertas_metalicas_abiertas_visuales
        )

    def actualizar_puertas_metalicas(self):
        """Actualiza la apertura después de mover al jugador o una piedra."""
        if not self.puertas_metalicas:
            return

        plataformas_ocupadas = set(self.piedras).intersection(self.plataformas)
        if self.pos_jugador in self.plataformas:
            plataformas_ocupadas.add(self.pos_jugador)

        puertas_asociadas = {
            puerta
            for plataforma in plataformas_ocupadas
            for puerta in self.relaciones_plataforma_puerta.get(plataforma, ())
        }
        if self.relaciones_plataforma_puerta:
            plataformas_sin_pareja = (
                plataformas_ocupadas
                - set(self.relaciones_plataforma_puerta.keys())
            )
            puertas_sin_pareja = (
                set(self.puertas_metalicas)
                - {
                    puerta
                    for puertas in self.relaciones_plataforma_puerta.values()
                    for puerta in puertas
                }
            )
            self.puertas_metalicas_abiertas_visuales = (
                puertas_asociadas
                | (puertas_sin_pareja if plataformas_sin_pareja else set())
            )
        elif plataformas_ocupadas:
            # Fase de exploración: todavía no se conoce la correspondencia.
            self.puertas_metalicas_abiertas_visuales = set(self.puertas_metalicas)

    def es_posicion_valida(self, r, c):
        return 0 <= r < self.filas and 0 <= c < self.columnas

    def ejecutar_movimiento(self, direccion):
        """
        Aplica un movimiento ('ARRIBA', 'ABAJO', 'IZQUIERDA', 'DERECHA').
        Retorna el nuevo EstadoJuego si es legal, o None si está bloqueado.
        """
        dr, dc = MOVIMIENTOS[direccion]
        origen = self.pos_jugador
        dest_r = origen[0] + dr
        dest_c = origen[1] + dc
        dest = (dest_r, dest_c)

        if not self.es_posicion_valida(dest_r, dest_c):
            return None

        # 1. Bloqueos estáticos infranqueables para el jugador
        if dest in self.paredes or dest in self.lava or dest in self.puas_activas or dest in self.huecos:
            return None

        # 2. La escalera con reja es impenetrable si quedan diamantes
        if dest == self.escalera and len(self.diamantes) > 0:
            return None

        # 3. Puerta metálica cerrada
        if dest in self.puertas_metalicas and not self.puerta_metalica_abierta(dest):
            return None

        # 4. Puerta verde sin llave en mano
        if dest in self.puertas_verdes and not self.tiene_llave:
            return None

        # Clonar estado para aplicar la física
        siguiente = self.copiar()

        # CASO 1: EMPUJAR UNA ROCA
        if dest in siguiente.piedras:
            tras_r = dest_r + dr
            tras_c = dest_c + dc
            tras = (tras_r, tras_c)

            if not self.es_posicion_valida(tras_r, tras_c):
                return None

            # FÍSICA: Prohibido empujar si detrás hay pared, lava, puas, escalera
            if tras in self.paredes or tras in self.lava or tras in self.puas_activas or tras == self.escalera:
                return None

            # FÍSICA: Prohibido empujar DOS rocas al tiempo
            if tras in siguiente.piedras:
                return None

            # FÍSICA: Prohibido empujar roca a través de puertas
            if tras in siguiente.puertas_verdes:
                return None
            if (
                tras in siguiente.puertas_metalicas
                and not siguiente.puerta_metalica_abierta(tras)
            ):
                return None

            # Mover la piedra
            siguiente.piedras.remove(dest)

            # Si detrás hay un foso, la roca lo sella
            if tras in siguiente.huecos:
                siguiente.huecos.remove(tras)
                siguiente.huecos_llenos.add(tras)
            else:
                # La piedra rueda al suelo (puede ser suelo vacío o suelo con llave)
                siguiente.piedras.add(tras)

        # CASO 2: EL JUGADOR AVANZA
        siguiente.pos_jugador = dest
        siguiente.actualizar_puertas_metalicas()

        # Recoger diamante
        if dest in siguiente.diamantes:
            siguiente.diamantes.remove(dest)

        # Recoger llave (solo si no hay una roca encima)
        if dest in siguiente.llaves and dest not in siguiente.piedras:
            siguiente.llaves.remove(dest)
            siguiente.tiene_llave = True

        # Abrir y cruzar puerta verde
        if dest in siguiente.puertas_verdes and self.tiene_llave:
            siguiente.puertas_verdes.remove(dest)
            siguiente.tiene_llave = False  # Se consume la llave al desbloquearla

        # Púas inactivas
        if dest in siguiente.puas_inactivas:
            siguiente.puas_inactivas.remove(dest)
            siguiente.puas_activas.add(dest)

        return siguiente

    def obtener_acciones_validas(self):
        """Retorna lista de tuplas (direccion, nuevo_estado) para cada movimiento legal."""
        validas = []
        for accion in MOVIMIENTOS:
            nuevo_estado = self.ejecutar_movimiento(accion)
            if nuevo_estado is not None:
                validas.append((accion, nuevo_estado))
        return validas

    def es_victoria(self):
        """Condición de éxito: 0 diamantes pendientes y estar sobre la escalera."""
        return len(self.diamantes) == 0 and self.pos_jugador == self.escalera

    def clave_estado(self):
        return (
            self.pos_jugador,
            self.tiene_llave,
            frozenset(self.piedras),
            frozenset(self.diamantes),
            frozenset(self.llaves),
            frozenset(self.huecos),
            frozenset(self.huecos_llenos),
            frozenset(self.puas_activas),
            frozenset(self.puas_inactivas),
            frozenset(self.puertas_verdes),
            frozenset(
                (
                    plataforma,
                    frozenset(puertas)
                )
                for plataforma, puertas in self.relaciones_plataforma_puerta.items()
            )
        )