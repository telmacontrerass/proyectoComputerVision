# detector.py
import cv2
import numpy as np

# Rangos ORIENTATIVOS (H en 0-179). Sustituidlos por los medidos con la herramienta.
RANGOS = {
    "rosa":     [((164, 73, 147), (175, 167, 255))],
    "azul":     [((94, 95, 101), (107, 187, 199))],
    "verde":    [((34, 57, 39), (91, 134, 214))],
    "amarillo": [((23, 47, 136), (35, 139, 250))],
}

# Colores para dibujar (BGR)
COLORES_BGR = {
    "rosa":     (180, 105, 255),
    "azul":     (255, 0, 0),
    "verde":    (0, 200, 0),
    "amarillo": (0, 255, 255),
}

KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
AREA_MIN = 150  # píxeles; descarta ruido pequeño


def mascara_color(hsv, nombre):
    """Máscara binaria de un color (une varios intervalos si hace falta)."""
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in RANGOS[nombre]:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, np.array(lo), np.array(hi)))
    # Apertura quita puntos sueltos; cierre rellena huecos dentro de la marca
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL)
    return mask


def centroide_mayor(mask):
    """Centroide del contorno más grande, o None si no hay marca."""
    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos = [c for c in contornos if cv2.contourArea(c) > AREA_MIN]
    if not contornos:
        return None
    c = max(contornos, key=cv2.contourArea)
    m = cv2.moments(c)
    return (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))


def detectar_marcas(frame):
    """Devuelve ({color: (x, y) | None}, {color: máscara}) para los 4 colores."""
    blur = cv2.GaussianBlur(frame, (5, 5), 0)          # Lab 3: reduce ruido
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    centros, mascaras = {}, {}
    for nombre in RANGOS:
        mascaras[nombre] = mascara_color(hsv, nombre)
        centros[nombre] = centroide_mayor(mascaras[nombre])
    return centros, mascaras


def dibujar_marcas(frame, centros):
    for nombre, p in centros.items():
        if p is not None:
            cv2.circle(frame, p, 10, COLORES_BGR[nombre], 2)
            cv2.putText(frame, nombre, (p[0] + 12, p[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORES_BGR[nombre], 1)