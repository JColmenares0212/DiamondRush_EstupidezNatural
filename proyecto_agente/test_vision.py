import os
import cv2
import mss
import numpy as np

# Importación protegida según el directorio de ejecución
try:
    from vision import VisionGrid, REGION_JUGABLE, FILAS, COLUMNAS
except ModuleNotFoundError:
    from proyecto_agente.vision import VisionGrid, REGION_JUGABLE, FILAS, COLUMNAS

def main():
    # Obtener la ruta absoluta exacta de la carpeta templates dentro de proyecto_agente
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_templates = os.path.join(dir_actual, "templates")

    # Inicializar la visión con la ruta física garantizada
    vision = VisionGrid(ruta_templates=ruta_templates)

    print("=== TEST VISION EN VIVO ===")
    print("Presiona 'r' para limpiar la memoria de elementos al reiniciar nivel.")
    print("Presiona 'q' para salir.")

    w_celda = REGION_JUGABLE["width"] / COLUMNAS
    h_celda = REGION_JUGABLE["height"] / FILAS

    # Usar mss.MSS() para evitar advertencias de depreciación
    with mss.MSS() as sct:
        while True:
            # 1. Obtener matriz y datos del estado actual
            matriz, pos_jugador, tiene_llave, frame = vision.obtener_matriz_y_estado(sct)

            # 2. Dibujar la cuadrícula y las etiquetas de depuración
            frame_debug = frame.copy()

            for r in range(FILAS):
                for c in range(COLUMNAS):
                    x1 = int(c * w_celda)
                    y1 = int(r * h_celda)
                    x2 = int((c + 1) * w_celda)
                    y2 = int((r + 1) * h_celda)

                    # Líneas de la grilla
                    cv2.rectangle(frame_debug, (x1, y1), (x2, y2), (50, 50, 50), 1)

                    val = matriz[r, c]

                    # Si es la posición detectada del jugador, marcarlo en azul claro
                    if pos_jugador is not None and (r, c) == pos_jugador:
                        cv2.rectangle(frame_debug, (x1, y1), (x2, y2), (255, 255, 0), 2)
                        texto = "P" if not tiene_llave else "P+K"
                        cv2.putText(frame_debug, texto, (x1 + 6, y1 + int(h_celda * 0.7)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)
                    else:
                        # Colorear según el tipo de elemento
                        color = (0, 255, 0)
                        if val == 1:       # Pared
                            color = (0, 200, 255)
                        elif val == 2:     # Diamante / Reliquia
                            color = (255, 255, 0)
                        elif val == 3:     # Piedra
                            color = (0, 140, 255)
                        elif val in (4, 5): # Hueco / Hueco lleno
                            color = (180, 105, 255)
                        elif val in (6, 7): # Púas
                            color = (0, 0, 255)
                        elif val == 8:     # Lava
                            color = (0, 69, 255)
                        elif val in (11, 16): # Plataformas
                            color = (255, 0, 255)

                        cv2.putText(frame_debug, str(val), (x1 + 10, y1 + int(h_celda * 0.7)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            # Mostrar ventana de visualización en tiempo real
            cv2.imshow("Verificacion Vision 12x8", frame_debug)

            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                vision.reset_memoria()
                print("🔄 Memoria de visión reiniciada.")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()