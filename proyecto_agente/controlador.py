import time

try:
    import pydirectinput as input_engine
    USANDO_DIRECTINPUT = True
except ImportError:
    import pyautogui as input_engine
    USANDO_DIRECTINPUT = False

class ControladorJuego:
    def __init__(self, duracion_tecla=0.09, espera_entre_pasos=0.13):
        self.duracion_tecla = duracion_tecla
        self.espera_entre_pasos = espera_entre_pasos
        
        self.mapa_teclas = {
            'ARRIBA': 'up',
            'ABAJO': 'down',
            'IZQUIERDA': 'left',
            'DERECHA': 'right'
        }
        motor = "DirectInput (pydirectinput)" if USANDO_DIRECTINPUT else "PyAutoGUI"
        print(f"🎮 Controlador Minijuegos inicializado ({motor}).")

    def presionar_accion(self, accion, es_empuje=False):
        """
        Ejecuta la pulsación. Si el movimiento empuja una roca,
        extiende el tiempo de pulsación y la espera para sincronizar con la física.
        """
        tecla = self.mapa_teclas.get(accion)
        if not tecla:
            return

        # Ajuste dinámico de tiempo para animaciones pesadas de empuje
        t_pulsacion = 0.15 if es_empuje else self.duracion_tecla
        t_espera = 0.22 if es_empuje else self.espera_entre_pasos

        input_engine.keyDown(tecla)
        time.sleep(t_pulsacion)
        input_engine.keyUp(tecla)
        time.sleep(t_espera)

    def ejecutar_secuencia_con_estado(
        self,
        lista_acciones,
        estado_inicial,
        callback_abortar=None,
        callback_verificar=None,
        pasos_por_verificacion=8
    ):
        """
        Ejecuta la secuencia determinando paso a paso si cada acción implica
        empujar una piedra según la simulación de EstadoJuego.
        """
        total = len(lista_acciones)
        print(f"🚀 Ejecutando {total} pasos en Minijuegos...")

        estado_sim = estado_inicial.copiar()

        for idx, accion in enumerate(lista_acciones, 1):
            if callback_abortar and callback_abortar():
                print("🛑 Ejecución detenida.")
                break

            # Determinar si en la casilla destino inmediata hay una piedra
            dr, dc = {"ARRIBA": (-1, 0), "ABAJO": (1, 0), "IZQUIERDA": (0, -1), "DERECHA": (0, 1)}[accion]
            dest = (estado_sim.pos_jugador[0] + dr, estado_sim.pos_jugador[1] + dc)
            es_empuje = dest in estado_sim.piedras

            print(f"[{idx}/{total}] Moviendo: {accion} {'(Empujando roca)' if es_empuje else ''}")
            self.presionar_accion(accion, es_empuje=es_empuje)

            # Avanzar la simulación interna para mantener el rastro de las piedras
            estado_sim = estado_sim.ejecutar_movimiento(accion)

            if (
                callback_verificar
                and (idx % pasos_por_verificacion == 0 or idx == total)
                and not callback_verificar(estado_sim)
            ):
                print("⚠️ Verificación intermedia fallida. Replanificando.")
                return False

        print("🏁 Fin de la secuencia de comandos.")
        return True