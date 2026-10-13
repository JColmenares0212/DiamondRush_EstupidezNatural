# DiamondRush_EstupidezNatural

Agente autónomo para jugar Diamond Rush mediante visión por computador,
reconocimiento de templates y planificación de movimientos.

## Estructura

- `proyecto_agente/`: código fuente del agente y templates visuales.
- `proyecto_agente/main_agente.py`: punto de entrada.
- `proyecto_agente/test_vision.py`: pruebas de detección visual.

## Requisitos

El proyecto utiliza Python y bibliotecas como OpenCV, NumPy, PyAutoGUI y
MSS. Instala las dependencias disponibles en tu entorno antes de ejecutar el
agente.

## Ejecución

Desde la raíz del repositorio:

```powershell
python proyecto_agente\main_agente.py
```

La calibración depende de la posición y resolución de la ventana del juego.
