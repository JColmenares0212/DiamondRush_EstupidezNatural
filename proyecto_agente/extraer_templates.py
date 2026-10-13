import os
import cv2
import mss
import numpy as np

# Coordenadas calibradas para 12x8
REGION_JUGABLE = {"top": 350, "left": 554, "width": 429, "height": 643}
FILAS = 12
COLUMNAS = 8

os.makedirs("templates", exist_ok=True)

# Mapeo de teclas a prefijos de archivos
ASIGNACIONES = {
    ord('j'): ("jugador", "Jugador"),
    ord('y'): ("jugador_llave", "Jugador con Llave"),
    ord('p'): ("pared", "Pared fija"),
    ord('d'): ("diamante", "Diamante"),
    ord('g'): ("reliquia", "Reliquia Dorada"),
    ord('k'): ("llave_verde", "Llave Verde"),
    ord('l'): ("puerta_verde", "Puerta Verde"),
    ord('m'): ("puerta_metalica", "Puerta Metalica"),
    ord('a'): ("puerta_metalica_abierta", "Puerta Metalica Abierta"),
    ord('r'): ("piedra", "Piedra esferica"),
    ord('h'): ("hueco", "Piso sin fondo"),
    ord('u'): ("hueco_lleno", "Piso con piedra adentro"),
    ord('b'): ("plataforma", "Piso de plataforma"),
    ord('o'): ("plataforma_piedra", "Plataforma con Piedra Encima"),
    ord('v'): ("lava", "Lava"),
    ord('x'): ("puas_activas", "Piso con puas pisadas"),
    ord('z'): ("puas_inactivas", "Piso con puas sin pisar"),
    ord('e'): ("escalera_abierta", "Escalera abierta"),
    ord('w'): ("escalera_sellada", "Escalera sellada")
}

recorte_actual = None
seleccionando = False
punto_inicio = (0, 0)
punto_fin = (0, 0)

def obtener_siguiente_nombre(prefijo):
    """Calcula el siguiente indice consecutivo libre (ej: pared_11.png)."""
    i = 1
    while os.path.exists(os.path.join("templates", f"{prefijo}_{i}.png")):
        i += 1
    return f"{prefijo}_{i}.png"

def mouse_callback(event, x, y, flags, param):
    global seleccionando, punto_inicio, punto_fin, recorte_actual
    if event == cv2.EVENT_LBUTTONDOWN:
        seleccionando = True
        punto_inicio = (x, y)
        punto_fin = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and seleccionando:
        punto_fin = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        seleccionando = False
        punto_fin = (x, y)
        x1, x2 = min(punto_inicio[0], punto_fin[0]), max(punto_inicio[0], punto_fin[0])
        y1, y2 = min(punto_inicio[1], punto_fin[1]), max(punto_inicio[1], punto_fin[1])
        if x2 - x1 > 8 and y2 - y1 > 8:
            recorte_actual = frame[y1:y2, x1:x2].copy()
            cv2.imshow("Recorte", recorte_actual)

with mss.mss() as sct:
    screenshot = np.array(sct.grab(REGION_JUGABLE))
    frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

cv2.namedWindow("Extractor Templates 12x8", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Extractor Templates 12x8", 650, 750)
cv2.setMouseCallback("Extractor Templates 12x8", mouse_callback)

print("Extractor 12x8 Listo.")
print("Controles:")
print("  d: Diamante           |  g: Reliquia Dorada")
print("  k: Llave Verde        |  l: Puerta Verde")
print("  m: Puerta Metalica    |  a: Puerta Metalica Abierta")
print("  b: Plataforma         |  o: Plataforma con Piedra")
print("  r: Piedra             |  h: Hueco vacio")
print("  u: Hueco con piedra   |  v: Lava")
print("  z: Puas sin pisar     |  x: Puas pisadas")
print("  e: Escalera abierta   |  w: Escalera sellada")
print("  p: Pared              |  j: Jugador")
print("  y: Jugador con Llave  |  c: Refrescar pantalla")
print("  q: Salir")

with mss.mss() as sct:
    while True:
        display = frame.copy()
        if seleccionando:
            cv2.rectangle(display, punto_inicio, punto_fin, (0, 255, 255), 1)
        cv2.imshow("Extractor Templates 12x8", display)

        key = cv2.waitKey(20) & 0xFF
        if key == ord('c'):
            screenshot = np.array(sct.grab(REGION_JUGABLE))
            frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            print("🔄 Pantalla actualizada con el nivel actual.")
        elif key in ASIGNACIONES and recorte_actual is not None:
            prefijo, desc = ASIGNACIONES[key]
            nombre_archivo = obtener_siguiente_nombre(prefijo)
            ruta = os.path.join("templates", nombre_archivo)
            cv2.imwrite(ruta, recorte_actual)
            print(f"✅ Guardado [{desc}]: {ruta}")
        elif key == ord('q'):
            break

cv2.destroyAllWindows()