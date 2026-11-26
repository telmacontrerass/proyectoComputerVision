import math
import sys
import time
from pathlib import Path
import cv2

# detector_hsv.py está en la carpeta "HSV calibration" del proyecto.
carpeta_detector = Path(__file__).resolve().parent / "HSV calibration"
sys.path.insert(0, str(carpeta_detector))

from HSV_calibration.detector_hsv import COLORES_BGR, detectar_marcas, dibujar_marcas


# Ángulos medidos respecto a la posición inicial del volante.
# Positivo = derecha en pantalla. Negativo = izquierda. Cero = centro.
ANGULOS_OBJETIVO = [15, -15, 30, -30, 0, 45, 20, -45, -20, 60, -60, 0]

COLORES_JUEGO = ("rosa", "verde")
TIEMPO_ACIERTO = 0.6  # Segundos que ambas marcas deben permanecer en sus aros.


def girar_punto(punto, centro, grados):
    """Calcula dónde queda una pegatina al girar alrededor del centro."""
    cx, cy = centro
    dx = punto[0] - cx
    dy = punto[1] - cy
    angulo = math.radians(grados)

    # En una imagen, el eje Y crece hacia abajo.
    # Por eso un ángulo positivo produce un giro horario en pantalla.
    x = cx + dx * math.cos(angulo) - dy * math.sin(angulo)
    y = cy + dx * math.sin(angulo) + dy * math.cos(angulo)

    return round(x), round(y)


def orientacion(centros):
    """Calcula el ángulo de la línea que va de la pegatina verde a la rosa."""
    vx, vy = centros["verde"]
    rx, ry = centros["rosa"]

    return math.degrees(math.atan2(ry - vy, rx - vx))


def escribir(frame, mensaje, fila):
    """Dibuja texto con borde para que se lea sobre la imagen de la webcam."""
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


def jugar() -> bool:
    """Ejecuta el entrenamiento y devuelve True si se completan las 12 rondas."""
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

            # Detectar las pegatinas antes de dibujar los aros sobre la imagen.
            centros, _ = detectar_marcas(frame)
            dibujar_marcas(frame, centros)

            if referencia is None:
                escribir(frame, "Pon el volante recto y pulsa ESPACIO", 0)

                faltan = [
                    color for color, punto in centros.items()
                    if punto is None
                ]

                if faltan:
                    escribir(frame, "Faltan: " + ", ".join(faltan), 1)
                else:
                    escribir(frame, "Las cuatro marcas estan visibles", 1)

            elif ronda == total_rondas:
                escribir(frame, "Entrenamiento completado", 0)
                escribir(frame, f"Has superado las {total_rondas} rondas", 1)
                escribir(frame, "ENTER: continuar   |   R: repetir", 2)

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

                # Dibujar el aro objetivo de cada pegatina y comprobar
                # si su centro se encuentra dentro del aro correspondiente.
                ambas_dentro = True

                for color in COLORES_JUEGO:
                    objetivo = girar_punto(
                        referencia[color], centro_volante, grados
                    )

                    cv2.circle(
                        frame, objetivo, radio_aro,
                        COLORES_BGR[color], 3, cv2.LINE_AA
                    )

                    posicion_real = centros[color]

                    if (
                        posicion_real is None
                        or math.dist(posicion_real, objetivo) > radio_aro
                    ):
                        ambas_dentro = False

                faltan = [
                    color for color in COLORES_JUEGO
                    if centros[color] is None
                ]

                if faltan:
                    escribir(frame, "Marca fuera de vista: " + ", ".join(faltan), 1)
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
                    # Si una pegatina sale de su aro, el tiempo vuelve a cero.
                    dentro_desde = None

            cv2.imshow("Modo entrenamiento", frame)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla in (ord("q"), 27):  # Q o Escape
                break

            if ronda == total_rondas and tecla in (10, 13):  # Enter
                break

            if tecla == ord("r"):
                referencia = None
                ronda = 0
                dentro_desde = None

            if tecla == ord(" ") and referencia is None:
                if all(punto is not None for punto in centros.values()):
                    referencia = centros.copy()
                    puntos = list(referencia.values())

                    # El centro del volante es la media de las cuatro marcas.
                    centro_volante = (
                        sum(x for x, y in puntos) / len(puntos),
                        sum(y for x, y in puntos) / len(puntos),
                    )

                    orientacion_inicial = orientacion(referencia)

                    # Ajustar el tamaño de los aros al tamaño del volante.
                    diametro = math.dist(referencia["rosa"], referencia["verde"])
                    radio_aro = max(8, round(0.06 * diametro))

    finally:
        camara.release()
        cv2.destroyAllWindows()

    return ronda == total_rondas


if __name__ == "__main__":
    jugar()