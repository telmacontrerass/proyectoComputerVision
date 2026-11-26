import math
import time
import cv2

from HSV_calibration.detector_hsv import COLORES_BGR, detectar_marcas, dibujar_marcas


# Target angles measured from the initial steering wheel position.
# Positive = right on screen. Negative = left. Zero = center.
ANGULOS_OBJETIVO = [15, -15, 30, -30, 0, 45, 20, -45, -20, 60, -60, 0]

COLORES_JUEGO = ("rosa", "morado")
TIEMPO_ACIERTO = 0.6


def girar_punto(punto, centro, grados):
    """Calculate the position of a marker after rotating around the center."""
    cx, cy = centro
    dx = punto[0] - cx
    dy = punto[1] - cy
    angulo = math.radians(grados)

    # Positive angles produce clockwise rotation on the image.
    x = cx + dx * math.cos(angulo) - dy * math.sin(angulo)
    y = cy + dx * math.sin(angulo) + dy * math.cos(angulo)

    return round(x), round(y)


def orientacion(centros):
    """Calculate the angle of the line from the purple marker to the pink marker."""
    vx, vy = centros["morado"]
    rx, ry = centros["rosa"]

    return math.degrees(math.atan2(ry - vy, rx - vx))


def escribir(frame, mensaje, fila):
    """Draw readable text over the webcam image."""
    posicion = (12, 28 + 28 * fila)
    fuente = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(
        frame, mensaje, posicion, fuente, 0.6,
        (0, 0, 0), 4, cv2.LINE_AA
    )
    cv2.putText(
        frame, mensaje, posicion, fuente, 0.6,
        (255, 255, 255), 1, cv2.LINE_AA
    )


def iniciar_modo_entrenamiento(color_ranges):
    """Run the training mode using the HSV ranges calibrated in main.py."""
    camara = cv2.VideoCapture(0)

    if not camara.isOpened():
        camara.release()
        print("No se ha podido abrir la webcam.")
        return False

    referencia = None
    ronda = 0
    dentro_desde = None
    total_rondas = len(ANGULOS_OBJETIVO)

    try:
        while True:
            ok, frame = camara.read()

            if not ok:
                print("No se ha podido leer la imagen de la webcam.")
                break

            # Detect markers using the HSV ranges calibrated in main.py.
            centros, _ = detectar_marcas(frame, color_ranges)
            dibujar_marcas(frame, centros)

            if referencia is None:
                escribir(frame, "Pon el volante recto y pulsa ESPACIO", 0)

                faltan = [
                    color for color in COLORES_JUEGO
                    if centros.get(color) is None
                ]

                if faltan:
                    escribir(frame, "Faltan: " + ", ".join(faltan), 1)
                else:
                    escribir(frame, "Las marcas estan visibles", 1)

            elif ronda == total_rondas:
                escribir(frame, "Entrenamiento completado", 0)
                escribir(frame, f"Has superado las {total_rondas} rondas", 1)
                escribir(frame, "ENTER: continuar | R: repetir", 2)

            else:
                grados = ANGULOS_OBJETIVO[ronda]

                if grados == 0:
                    instruccion = "Vuelve al centro"
                else:
                    lado = "derecha" if grados > 0 else "izquierda"
                    instruccion = f"{abs(grados)} grados a la {lado}"

                escribir(
                    frame,
                    f"Ronda {ronda + 1}/{total_rondas}: {instruccion}",
                    0
                )

                # Draw the target ring for each marker and check its position.
                ambas_dentro = True

                for color in COLORES_JUEGO:
                    objetivo = girar_punto(
                        referencia[color], centro_volante, grados
                    )

                    cv2.circle(
                        frame, objetivo, radio_aro,
                        COLORES_BGR[color], 3, cv2.LINE_AA
                    )

                    posicion_real = centros.get(color)

                    if (
                        posicion_real is None
                        or math.dist(posicion_real, objetivo) > radio_aro
                    ):
                        ambas_dentro = False

                faltan = [
                    color for color in COLORES_JUEGO
                    if centros.get(color) is None
                ]

                if faltan:
                    escribir(
                        frame,
                        "Marca fuera de vista: " + ", ".join(faltan),
                        1
                    )
                else:
                    giro = orientacion(centros) - orientacion_inicial
                    giro = (giro + 180) % 360 - 180
                    escribir(frame, f"Giro actual: {giro:+.0f} grados", 1)

                if ambas_dentro:
                    ahora = time.monotonic()

                    if dentro_desde is None:
                        dentro_desde = ahora

                    escribir(frame, "Bien, manten el volante ahi", 2)

                    if ahora - dentro_desde >= TIEMPO_ACIERTO:
                        ronda += 1
                        dentro_desde = None
                else:
                    # Reset the timer if a marker leaves its target ring.
                    dentro_desde = None

            cv2.imshow("Modo entrenamiento", frame)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla in (ord("q"), 27):
                break

            if ronda == total_rondas and tecla in (10, 13):
                break

            if tecla == ord("r"):
                referencia = None
                ronda = 0
                dentro_desde = None

            if tecla == ord(" ") and referencia is None:
                if all(
                    centros.get(color) is not None
                    for color in COLORES_JUEGO
                ):
                    referencia = centros.copy()

                    puntos = [
                        referencia[color]
                        for color in COLORES_JUEGO
                    ]

                    # Calculate the center of the steering wheel.
                    centro_volante = (
                        sum(x for x, y in puntos) / len(puntos),
                        sum(y for x, y in puntos) / len(puntos),
                    )

                    orientacion_inicial = orientacion(referencia)

                    # Adjust the target ring size to the steering wheel.
                    diametro = math.dist(
                        referencia["rosa"],
                        referencia["morado"]
                    )
                    radio_aro = max(8, round(0.06 * diametro))

    finally:
        camara.release()
        cv2.destroyAllWindows()

    return ronda == total_rondas
