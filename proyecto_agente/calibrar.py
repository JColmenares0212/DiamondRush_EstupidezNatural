import cv2
import mss
import numpy as np

FILAS = 12
COLUMNAS = 8

# Valores iniciales de referencia
init_top = 350
init_left = 500
init_w = 400
init_h = 550

cv2.namedWindow("Calibracion 11x8", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Calibracion 11x8", 500, 300)

def nothing(x):
    pass

# Controles deslizantes para ajustar coordenadas y tamaño
cv2.createTrackbar("Top (Y)", "Calibracion 11x8", init_top, 1200, nothing)
cv2.createTrackbar("Left (X)", "Calibracion 11x8", init_left, 1920, nothing)
cv2.createTrackbar("Ancho (W)", "Calibracion 11x8", init_w, 800, nothing)
cv2.createTrackbar("Alto (H)", "Calibracion 11x8", init_h, 900, nothing)

print("Abre Brave al 80% con Diamond Rush en pantalla.")
print("Ajusta las barras deslizantes hasta que las lineas verdes calcen exactamente sobre las 11x8 casillas.")
print("Presiona la tecla 's' en la ventana de vista previa para guardar y salir, o 'q' para cancelar.")

with mss.mss() as sct:
    while True:
        top = cv2.getTrackbarPos("Top (Y)", "Calibracion 11x8")
        left = cv2.getTrackbarPos("Left (X)", "Calibracion 11x8")
        width = max(16, cv2.getTrackbarPos("Ancho (W)", "Calibracion 11x8"))
        height = max(22, cv2.getTrackbarPos("Alto (H)", "Calibracion 11x8"))

        region = {"top": top, "left": left, "width": width, "height": height}
        
        try:
            screenshot = np.array(sct.grab(region))
            frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        except Exception:
            continue

        h_celda = height / FILAS
        w_celda = width / COLUMNAS

        # Dibujar líneas horizontales (11 filas)
        for r in range(FILAS + 1):
            y = int(r * h_celda)
            cv2.line(frame, (0, y), (width, y), (0, 255, 0), 1)

        # Dibujar líneas verticales (8 columnas)
        for c in range(COLUMNAS + 1):
            x = int(c * w_celda)
            cv2.line(frame, (x, 0), (x, height), (0, 255, 0), 1)

        cv2.imshow("Vista Previa Grilla", frame)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('s'):
            print("\n" + "=" * 50)
            print("Coordenadas calibradas con exito:")
            print(f'REGION_JUGABLE = {{"top": {top}, "left": {left}, "width": {width}, "height": {height}}}')
            print("=" * 50 + "\n")
            break
        elif key == ord('q'):
            print("\nCalibracion cancelada.")
            break

cv2.destroyAllWindows()