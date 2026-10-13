import os
import glob
import cv2
import mss
import numpy as np

# Coordenadas calibradas para la matriz completa de 12x8
REGION_JUGABLE = {"top": 350, "left": 554, "width": 429, "height": 643}
FILAS = 12
COLUMNAS = 8

# Constantes numéricas de elementos del juego
ID_VACIO = 0
ID_PARED = 1
ID_DIAMANTE = 2
ID_RELIQUIA = 2           # Trato idéntico a diamante en la recolección
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

class VisionGrid:
    def __init__(self, ruta_templates=None):
        if ruta_templates is None:
            # Obtiene la ruta exacta de la carpeta donde reside vision.py
            dir_actual = os.path.dirname(os.path.abspath(__file__))
            self.ruta_templates = os.path.join(dir_actual, "templates")
        else:
            self.ruta_templates = ruta_templates
            
        self.templates = {}
        self.posiciones_plataformas = set()
        self.posiciones_puertas_verdes = set()
        self.posiciones_puertas_metalicas = set()
        # Una plataforma puede controlar una o varias puertas.
        self.relaciones_plataforma_puerta = {}
        self.posiciones_puas = set()
        self.cargar_templates()

    def reset_memoria(self):
        """Reinicia la memoria de elementos fijos al cambiar o reiniciar nivel."""
        self.posiciones_plataformas.clear()
        self.posiciones_puertas_verdes.clear()
        self.posiciones_puertas_metalicas.clear()
        self.relaciones_plataforma_puerta.clear()
        self.posiciones_puas.clear()

    def cargar_templates(self):
        """Carga en memoria todas las plantillas PNG disponibles."""
        archivos = glob.glob(os.path.join(self.ruta_templates, "*.png"))
        for archivo in archivos:
            nombre = os.path.basename(archivo)
            img = cv2.imread(archivo)
            if img is not None:
                self.templates[nombre] = img
        print(f"✅ Cargadas {len(self.templates)} plantillas para 12x8.")

    def limpiar_texto_hud(self, bgr_frame):
        """Suprime los caracteres blancos del HUD superior rellenándolos con café de fondo."""
        frame_limpio = bgr_frame.copy()
        zona_hud = frame_limpio[0:int(frame_limpio.shape[0] * 0.12), :]
        
        mascara_texto = cv2.inRange(zona_hud, np.array([210, 210, 210]), np.array([255, 255, 255]))
        color_fondo = np.array([32, 45, 65], dtype=np.uint8)
        zona_hud[mascara_texto > 0] = color_fondo
        frame_limpio[0:int(frame_limpio.shape[0] * 0.12), :] = zona_hud
        return frame_limpio

    def encontrar_jugador(self, bgr_frame, w_celda, h_celda):
        """Ubica al jugador rastreando torso y base de apoyo para operar incluso bajo el HUD."""
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        mejor_val = -1
        mejor_loc = None
        mejor_shape = (0, 0)
        tiene_llave = False

        for nombre, tmpl_bgr in self.templates.items():
            if nombre.startswith("jugador"):
                tmpl_gray = cv2.cvtColor(tmpl_bgr, cv2.COLOR_BGR2GRAY)
                th, tw = tmpl_gray.shape
                if th > gray.shape[0] or tw > gray.shape[1]:
                    continue

                res = cv2.matchTemplate(gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val > mejor_val:
                    mejor_val = max_val
                    mejor_loc = max_loc
                    mejor_shape = tmpl_gray.shape
                    tiene_llave = nombre.startswith("jugador_llave")

        if mejor_val >= 0.50 and mejor_loc is not None:
            x_pies = mejor_loc[0] + (mejor_shape[1] / 2.0)
            y_pies = mejor_loc[1] + (mejor_shape[0] * 0.82)

            col = int(x_pies // w_celda)
            fila = int(y_pies // h_celda)

            col = max(0, min(COLUMNAS - 1, col))
            fila = max(0, min(FILAS - 1, fila))
            return (fila, col), tiene_llave

        return None, False

    def clasificar_celda(self, recorte_bgr):
        h_rec, w_rec = recorte_bgr.shape[:2]
        recorte_gray = cv2.cvtColor(recorte_bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(recorte_bgr, cv2.COLOR_BGR2HSV)
        area_total = h_rec * w_rec
        brillo_medio = np.mean(recorte_gray)

        # 1. COLOR HSV PRIORITARIO
        # Diamante celeste
        mask_cyan = cv2.inRange(hsv, np.array([85, 90, 140]), np.array([105, 255, 255]))
        if np.sum(mask_cyan > 0) > (area_total * 0.03):
            return ID_DIAMANTE

        # Llave o Puerta Verde
        mask_verde = cv2.inRange(hsv, np.array([75, 120, 100]), np.array([95, 255, 255]))
        cant_verde = np.sum(mask_verde > 0)
        if cant_verde > (area_total * 0.04):
            return ID_PUERTA_VERDE if cant_verde > (area_total * 0.14) else ID_LLAVE

        # LAVA: Fuego puro (alta saturación S >= 185 y brillo V >= 175) con textura de magma
        mask_fuego = cv2.inRange(hsv, np.array([2, 185, 175]), np.array([25, 255, 255]))
        puntos_negros_magma = recorte_gray < 50
        if np.sum(mask_fuego > 0) > (area_total * 0.05) and np.sum(puntos_negros_magma) > (area_total * 0.08):
            return ID_LAVA

        # Puerta metálica (reja gris de barrotes)
        mask_gris = cv2.inRange(hsv, np.array([0, 0, 70]), np.array([180, 45, 180]))
        if np.sum(mask_gris > 0) > (area_total * 0.18):
            return ID_PUERTA_METALICA

        # 2. TEMPLATE MATCHING JERÁRQUICO
        mejor_score = -1
        mejor_id = ID_VACIO

        mapeo = [
            ("puerta_metalica_abierta", ID_PUERTA_METALICA_ABIERTA, 0.45),
            ("escalera_abierta", ID_ESCALERA_ABIERTA, 0.52),
            ("escalera_sellada", ID_ESCALERA_SELLADA, 0.52),
            ("reliquia", ID_RELIQUIA, 0.50),
            ("plataforma", ID_PLATAFORMA, 0.48),
            ("puas_activas", ID_PUAS_ACTIVAS, 0.45),      # Umbral calibrado a 0.45 para capturar variantes con sombras
            ("piedra", ID_PIEDRA, 0.46),
            ("hueco_lleno", ID_HUECO_LLENO, 0.48),
            ("hueco", ID_HUECO, 0.48),
            ("pared", ID_PARED, 0.52),
            ("puas_inactivas", ID_PUAS_INACTIVAS, 0.52)
        ]

        for prefijo, id_elem, umbral in mapeo:
            for nombre, tmpl_bgr in self.templates.items():
                if nombre.startswith(prefijo):
                    tmpl_gray = cv2.cvtColor(tmpl_bgr, cv2.COLOR_BGR2GRAY)
                    th, tw = tmpl_gray.shape

                    if th > h_rec or tw > w_rec:
                        escala = min(h_rec / th, w_rec / tw) * 0.95
                        tmpl_gray = cv2.resize(tmpl_gray, (0, 0), fx=escala, fy=escala)
                        th, tw = tmpl_gray.shape

                    if th <= h_rec and tw <= w_rec:
                        res = cv2.matchTemplate(recorte_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        if max_val > umbral and max_val > mejor_score:
                            mejor_score = max_val
                            mejor_id = id_elem

        # 3. FILTRO DE BRILLO: Las paredes reales son claras; el suelo café o grietas son oscuras
        if mejor_id == ID_PARED and brillo_medio < 70:
            mejor_id = ID_VACIO

        # 4. VERIFICACIÓN ESTRUCTURAL DE PÚAS INACTIVAS
        if mejor_id == ID_PUAS_INACTIVAS:
            orificios_oscuros = np.sum(recorte_gray < 40)
            if orificios_oscuros < 25:
                mejor_id = ID_VACIO

        return mejor_id

    def obtener_matriz_y_estado(self, sct):
        screenshot = np.array(sct.grab(REGION_JUGABLE))
        bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

        w_celda = REGION_JUGABLE["width"] / COLUMNAS
        h_celda = REGION_JUGABLE["height"] / FILAS

        # Localizar al explorador
        pos_jugador, tiene_llave = self.encontrar_jugador(bgr, w_celda, h_celda)

        # Quitar texto blanco para no perjudicar la lectura del suelo y diamantes
        bgr_sin_hud = self.limpiar_texto_hud(bgr)

        matriz = np.zeros((FILAS, COLUMNAS), dtype=int)
        puertas_abiertas_captura = set()
        plataformas_ocupadas_captura = set()

        for r in range(FILAS):
            for c in range(COLUMNAS):
                if pos_jugador is not None and (r, c) == pos_jugador:
                    matriz[r, c] = ID_VACIO
                    if (r, c) in self.posiciones_plataformas:
                        plataformas_ocupadas_captura.add((r, c))
                    continue

                x1 = int(c * w_celda)
                x2 = int((c + 1) * w_celda)
                y1 = int(r * h_celda)
                y2 = int((r + 1) * h_celda)

                recorte = bgr_sin_hud[y1:y2, x1:x2]
                id_celda = self.clasificar_celda(recorte)

                # Persistencia de memoria para plataformas fijas
                if id_celda == ID_PLATAFORMA:
                    self.posiciones_plataformas.add((r, c))
                elif (r, c) in self.posiciones_plataformas and id_celda == ID_PIEDRA:
                    id_celda = ID_PLATAFORMA_PIEDRA

                # Persistencia de memoria para puertas verdes
                if id_celda == ID_PUERTA_VERDE:
                    self.posiciones_puertas_verdes.add((r, c))
                elif (r, c) in self.posiciones_puertas_verdes:
                    if id_celda == ID_LLAVE:
                        id_celda = ID_PUERTA_VERDE

                # Una puerta metálica abierta sigue siendo una puerta:
                # su estado depende de que una piedra permanezca en la plataforma.
                if id_celda in (ID_PUERTA_METALICA, ID_PUERTA_METALICA_ABIERTA):
                    self.posiciones_puertas_metalicas.add((r, c))
                    if id_celda == ID_PUERTA_METALICA_ABIERTA:
                        puertas_abiertas_captura.add((r, c))
                elif (r, c) in self.posiciones_puertas_metalicas and id_celda == ID_VACIO:
                    id_celda = ID_PUERTA_METALICA_ABIERTA
                    puertas_abiertas_captura.add((r, c))

                if id_celda == ID_PLATAFORMA_PIEDRA:
                    plataformas_ocupadas_captura.add((r, c))

                # Persistencia de memoria para púas (inactivas y activas)
                if id_celda in (ID_PUAS_INACTIVAS, ID_PUAS_ACTIVAS):
                    self.posiciones_puas.add((r, c))
                elif (r, c) in self.posiciones_puas:
                    # Si era una púa conocida y cae a piso libre, se trata de una púa activa con variación visual
                    if id_celda == ID_VACIO:
                        id_celda = ID_PUAS_ACTIVAS

                matriz[r, c] = id_celda

        if len(plataformas_ocupadas_captura) == 1 and puertas_abiertas_captura:
            plataforma = next(iter(plataformas_ocupadas_captura))
            puertas_ya_asignadas = {
                puerta
                for puertas in self.relaciones_plataforma_puerta.values()
                for puerta in puertas
            }
            puertas_nuevas = puertas_abiertas_captura - puertas_ya_asignadas
            if puertas_nuevas:
                self.relaciones_plataforma_puerta.setdefault(
                    plataforma, set()
                ).update(puertas_nuevas)

        return matriz, pos_jugador, tiene_llave, bgr