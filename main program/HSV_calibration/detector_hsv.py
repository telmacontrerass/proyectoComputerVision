
import cv2
import numpy as np

# Default HSV ranges (H: 0-179).
# These are only used if no calibrated ranges are provided.
RANGOS = {
    "rosa": [((164, 73, 147), (175, 167, 255))],
    "azul": [((94, 95, 101), (107, 187, 199))],
    "morado": [((125, 50, 50), (160, 255, 255))],
    "amarillo": [((23, 47, 136), (35, 139, 250))]
}

# Colors used to draw the detected markers (BGR).
COLORES_BGR = {
    "rosa": (180, 105, 255),
    "azul": (255, 0, 0),
    "morado": (255, 0, 255),
    "amarillo": (0, 255, 255)
}

KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
AREA_MIN = 150


def mascara_color(hsv, nombre, rangos):
    """Create a binary mask for a color, combining multiple intervals if necessary."""
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

    for lo, hi in rangos:
        mask = cv2.bitwise_or(
            mask,
            cv2.inRange(hsv, np.array(lo), np.array(hi))
        )

    # Opening removes small noise; closing fills holes inside the marker.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL)

    return mask


def centroide_mayor(mask):
    """Return the centroid of the largest contour, or None if no marker is found."""
    contornos, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contornos = [
        c for c in contornos
        if cv2.contourArea(c) > AREA_MIN
    ]

    if not contornos:
        return None

    c = max(contornos, key=cv2.contourArea)
    m = cv2.moments(c)

    if m["m00"] == 0:
        return None

    return (
        int(m["m10"] / m["m00"]),
        int(m["m01"] / m["m00"])
    )


def preparar_rangos(color_ranges):
    """Convert calibrated ranges into the format expected by the detector."""
    rangos = {}

    for nombre, valor in color_ranges.items():
        # main.py provides a single pair: (lower, upper).
        # The detector internally uses a list of pairs.
        if (
            isinstance(valor, (tuple, list))
            and len(valor) == 2
            and len(valor[0]) == 3
            and len(valor[1]) == 3
            and all(np.isscalar(x) for x in valor[0])
            and all(np.isscalar(x) for x in valor[1])
        ):
            rangos[nombre] = [valor]

        else:
            # Also allow a list of multiple (lower, upper) pairs.
            rangos[nombre] = valor

    return rangos


def detectar_marcas(frame, color_ranges=None):
    """
    Detect all available markers.

    Returns:
        centros: {color: (x, y) or None}
        mascaras: {color: binary mask}
    """
    blur = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    # Use calibrated ranges when provided.
    if color_ranges is None:
        rangos_actuales = RANGOS
    else:
        rangos_actuales = preparar_rangos(color_ranges)

    centros = {}
    mascaras = {}

    for nombre, rangos in rangos_actuales.items():
        mascaras[nombre] = mascara_color(hsv, nombre, rangos)
        centros[nombre] = centroide_mayor(mascaras[nombre])

    return centros, mascaras


def dibujar_marcas(frame, centros):
    """Draw detected markers and their names."""
    for nombre, punto in centros.items():
        if punto is not None:
            color = COLORES_BGR[nombre]

            cv2.circle(frame, punto, 10, color, 2)

            cv2.putText(
                frame,
                nombre,
                (punto[0] + 12, punto[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
