import time
import mss
import keyboard
import numpy as np

from vision import VisionGrid, ID_PARED, ID_DIAMANTE
from estado_juego import EstadoJuego
from planificador import Planificador
from controlador import ControladorJuego

def esperar_nuevo_nivel(vision, sct, mascara_paredes_anterior, timeout=12.0):
    """
    Monitorea la pantalla hasta que termine la animación de salida
    y se cargue el nuevo mapa de forma estable.
    """
    print("⏳ Esperando transición al siguiente nivel...")
    inicio = time.time()
    
    while time.time() - inicio < timeout:
        if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
            return None, None, None

        time.sleep(0.35)
        matriz, pos_jugador, tiene_llave, _ = vision.obtener_matriz_y_estado(sct)

        if pos_jugador is None:
            continue

        mascara_actual = (matriz == ID_PARED)
        diferencias = np.sum(mascara_actual != mascara_paredes_anterior)
        
        # Si la estructura de paredes cambió o el mapa se reinició/avanzó
        if diferencias > 8:
            time.sleep(0.4)
            return matriz, pos_jugador, tiene_llave

    return None, None, None

def main():
    print("==================================================")
    print("🤖 AGENTE AUTÓNOMO CERRADO - DIAMOND RUSH (12x8)")
    print("==================================================")
    print("Controles:")
    print(" [ESPACIO] -> Inicia el agente en bucle continuo.")
    print(" [ESC]     -> Pausa o cancela la marcha de inmediato.")
    print(" [q]       -> Salir definitivamente del programa.")
    print("==================================================\n")

    vision = VisionGrid()
    planificador = Planificador()
    controlador = ControladorJuego(duracion_tecla=0.09, espera_entre_pasos=0.13)

    agente_activo = False
    mascara_paredes_actual = None

    with mss.MSS() as sct:
        while True:
            # 1. Monitoreo de teclas de control general
            if keyboard.is_pressed('q'):
                print("\n🛑 Saliendo del programa...")
                break

            if keyboard.is_pressed('esc'):
                if agente_activo:
                    print("\n⏸️ AGENTE PAUSADO con ESC. Presiona ESPACIO para reactivar.")
                    agente_activo = False
                time.sleep(0.3)

            if not agente_activo and keyboard.is_pressed('space'):
                print("\n🚀 ¡Bucle continuo activado! Resolviendo niveles...")
                agente_activo = True
                mascara_paredes_actual = None
                time.sleep(0.4)

            # 2. Ciclo principal del agente
            if agente_activo:
                print("\n" + "="*48)
                print("📸 [1/4] Capturando estado del nivel...")

                # Escaneo con memoria limpia al inicio de cada iteración de nivel
                matriz, pos_jugador, tiene_llave, _ = vision.obtener_matriz_y_estado(sct)

                if pos_jugador is None:
                    print("⚠️ Jugador no detectado en el encuadre. Reintentando...")
                    time.sleep(0.5)
                    continue

                mascara_paredes_actual = (matriz == ID_PARED).copy()

                # Construcción del estado lógico
                print(f"🧩 [2/4] Estado: Jugador en {pos_jugador}, Llave={tiene_llave}")
                estado_inicial = EstadoJuego.desde_matriz_vision(
                    matriz,
                    pos_jugador,
                    tiene_llave,
                    vision.relaciones_plataforma_puerta
                )
                if vision.relaciones_plataforma_puerta:
                    print(
                        "    - Relación plataforma/puerta conocida: "
                        f"{vision.relaciones_plataforma_puerta}"
                    )

                print(f"    - Diamantes pendientes: {len(estado_inicial.diamantes)}")
                print(f"    - Piedras en mapa: {len(estado_inicial.piedras)}")
                print(f"    - Escalera de salida: {estado_inicial.escalera}")

                # Planificación con A*
                print("🧠 [3/4] Calculando ruta óptima con A*...")
                t_inicio = time.time()
                plan = planificador.resolver(estado_inicial)
                t_calculo = time.time() - t_inicio

                if not plan:
                    print("❌ No se encontró ruta. Pausando por seguridad.")
                    agente_activo = False
                    continue

                print(f"⚡ Solución calculada en {t_calculo:.3f}s ({len(plan)} pasos).")

                # Ejecución física sincronizada con detección de empujes
                print("🕹️ [4/4] Ejecutando secuencia de comandos...")
                time.sleep(0.2)

                def abortar():
                    return keyboard.is_pressed('esc') or keyboard.is_pressed('q')

                def verificar_ejecucion(estado_esperado):
                    time.sleep(0.12)
                    matriz_verificacion, pos_verificacion, _, _ = (
                        vision.obtener_matriz_y_estado(sct)
                    )

                    if pos_verificacion is None:
                        print(
                            "⚠️ Verificación: jugador no detectado "
                            f"(se esperaba {estado_esperado.pos_jugador})."
                        )
                        return False

                    diamantes_esperados = len(estado_esperado.diamantes)
                    diamantes_visibles = int(np.sum(matriz_verificacion == ID_DIAMANTE))

                    sincronizada = (
                        pos_verificacion == estado_esperado.pos_jugador
                        and diamantes_visibles <= diamantes_esperados
                    )
                    if not sincronizada:
                        print(
                            "⚠️ Verificación: "
                            f"posición esperada {estado_esperado.pos_jugador}, "
                            f"real {pos_verificacion}; "
                            f"diamantes esperados como máximo {diamantes_esperados}, "
                            f"visibles {diamantes_visibles}."
                        )
                    return sincronizada

                ejecucion_sincronizada = controlador.ejecutar_secuencia_con_estado(
                    plan,
                    estado_inicial,
                    callback_abortar=abortar,
                    callback_verificar=verificar_ejecucion,
                    pasos_por_verificacion=8
                )

                if abortar():
                    print("\n⏸️ Movimiento abortado con ESC.")
                    agente_activo = False
                    continue

                if not ejecucion_sincronizada:
                    time.sleep(0.2)
                    continue

                # Verificación visual real de victoria (Closed-Loop)
                time.sleep(0.5)
                matriz_post, pos_post, _, _ = vision.obtener_matriz_y_estado(sct)
                diamantes_restantes = np.sum(matriz_post == ID_DIAMANTE)

                # Si no se cumplió la meta, no canta victoria ni espera nivel; re-planifica de inmediato
                if diamantes_restantes > 0 or pos_post != estado_inicial.escalera:
                    print(f"⚠️ Nivel no completado aún (quedan {diamantes_restantes} diamantes, jugador en {pos_post}).")
                    print("🔄 Re-sincronizando y ejecutando plan correctivo...")
                    time.sleep(0.2)
                    continue

                print("🎉 ¡Nivel verificado y completado al 100%!")

                # Esperar a que el juego abra el siguiente nivel
                time.sleep(0.8)
                matriz_sig, pos_sig, _ = esperar_nuevo_nivel(
                    vision, sct, mascara_paredes_actual, timeout=10.0
                )

                if pos_sig is None:
                    print("⚠️ No se detectó cambio de nivel o se pulsó ESC. Agente en pausa.")
                    agente_activo = False
                else:
                    # Nivel nuevo confirmado -> Limpiar memoria estática de visión
                    vision.reset_memoria()

            time.sleep(0.05)

    print("Programa cerrado correctamente.")

if __name__ == "__main__":
    main()