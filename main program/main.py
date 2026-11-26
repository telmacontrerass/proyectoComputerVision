
import cv2
import numpy as np

import password.password_function
from race_mode.race import iniciar_modo_carrera


CONTRASENA_PRACTICA = ["azul", "amarillo", "rosa", "morado"]
CONTRASENA_CARRERA = ["rosa", "morado", "amarillo", "azul"]

ANCHO = 800
ALTO = 500

seleccion = None



def calibrate_color(color_name):

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("No se ha podido abrir la cámara.")
        cap.release()
        return None

    window_camera = f"Calibrar {color_name}"
    window_sliders = f"Ajustar {color_name}"
    window_mask = f"Deteccion {color_name}"

    cv2.namedWindow(window_sliders)
    cv2.namedWindow(window_camera)
    cv2.namedWindow(window_mask)

    for slider, maximum in [
        ("H min", 179), ("H max", 179),
        ("S min", 255), ("S max", 255),
        ("V min", 255), ("V max", 255)
    ]:
        cv2.createTrackbar(
            slider,
            window_sliders,
            0 if "min" in slider else maximum,
            maximum,
            lambda x: None
        )

    state = {
        "capturing": False,
        "frame": None,
        "selected": False,
        "lower": None,
        "upper": None
    }

    def select_color(event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDOWN and state["capturing"]:

            frame = state["frame"]

            if frame is None:
                return

            height, width = frame.shape[:2]

            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            radius = 10

            x1 = max(0, x - radius)
            x2 = min(width, x + radius + 1)
            y1 = max(0, y - radius)
            y2 = min(height, y + radius + 1)

            zone = hsv[y1:y2, x1:x2]
            pixels = zone.reshape(-1, 3)

            minimum = np.percentile(pixels, 5, axis=0)
            maximum = np.percentile(pixels, 95, axis=0)

            margin = np.array([5, 40, 40])

            lower = np.clip(
                minimum - margin,
                [0, 0, 0],
                [179, 255, 255]
            ).astype(int)

            upper = np.clip(
                maximum + margin,
                [0, 0, 0],
                [179, 255, 255]
            ).astype(int)

            state["lower"] = lower
            state["upper"] = upper
            state["selected"] = True
            state["capturing"] = False

            for slider, value in zip(
                ("H min", "S min", "V min"),
                lower
            ):
                cv2.setTrackbarPos(slider, window_sliders, int(value))

            for slider, value in zip(
                ("H max", "S max", "V max"),
                upper
            ):
                cv2.setTrackbarPos(slider, window_sliders, int(value))

            print(f"Se ha seleccionado el color {color_name} correctamente.")

    cv2.setMouseCallback(window_camera, select_color)

    print(f"\nCALIBRACIÓN DEL COLOR: {color_name.upper()}")
    print("Pulsa C para congelar la imagen.")
    print("Haz clic sobre el marcador del color correspondiente.")
    print("Ajusta los deslizadores si es necesario.")
    print("Pulsa R para volver a la cámara.")
    print("Pulsa Q para confirmar y continuar.")

    result = None

    try:

        while True:

            if not state["capturing"]:

                ok, frame = cap.read()

                if not ok:
                    print("Error al leer la cámara.")
                    break

                state["frame"] = frame.copy()

            frame = state["frame"].copy()

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower = np.array([
                cv2.getTrackbarPos(name, window_sliders)
                for name in ("H min", "S min", "V min")
            ])

            upper = np.array([
                cv2.getTrackbarPos(name, window_sliders)
                for name in ("H max", "S max", "V max")
            ])

            mask = cv2.inRange(hsv, lower, upper)

            detected = cv2.bitwise_and(
                frame,
                frame,
                mask=mask
            )

            display_frame = frame.copy()

            if state["capturing"]:
                cv2.putText(
                    display_frame,
                    "IMAGEN CONGELADA - SELECCIONA EL COLOR",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

            cv2.imshow(window_camera, display_frame)
            cv2.imshow(window_mask, detected)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("c") and not state["capturing"]:

                state["capturing"] = True
                state["selected"] = False

                print("Imagen congelada. Haz clic sobre el marcador.")

            elif key == ord("r"):

                state["capturing"] = False
                state["selected"] = False

                print("Volviendo a la cámara.")

            elif key == ord("q"):

                if not state["selected"]:
                    print("Primero debes seleccionar el color con el ratón.")
                    continue

                lower = np.array([
                    cv2.getTrackbarPos(name, window_sliders)
                    for name in ("H min", "S min", "V min")
                ])

                upper = np.array([
                    cv2.getTrackbarPos(name, window_sliders)
                    for name in ("H max", "S max", "V max")
                ])

                result = (
                    tuple(lower.tolist()),
                    tuple(upper.tolist())
                )

                print(f"Rangos del color {color_name} guardados.")
                print("Límite inferior:", lower.tolist())
                print("Límite superior:", upper.tolist())

                break

    finally:

        cap.release()

        cv2.destroyWindow(window_camera)
        cv2.destroyWindow(window_sliders)
        cv2.destroyWindow(window_mask)

    return result


def calibrate_colors():

    colors = ["azul", "amarillo", "rosa", "morado"]
    color_ranges = {}

    print("\nVAMOS A CALIBRAR LOS CUATRO COLORES.")
    print("Prepara los marcadores para realizar la calibración.")

    for color in colors:

        color_range = calibrate_color(color)

        if color_range is None:
            print("La calibración no se ha podido completar.")
            return None

        color_ranges[color] = color_range

    print("\nLOS CUATRO COLORES SE HAN CALIBRADO CORRECTAMENTE.")

    return color_ranges


def seleccionar_modo(evento, x, y, flags, param):

    global seleccion

    if evento == cv2.EVENT_LBUTTONDOWN:

        if 150 <= x <= 380 and 220 <= y <= 320:
            seleccion = "practica"

        elif 420 <= x <= 650 and 220 <= y <= 320:
            seleccion = "carrera"


def mostrar_menu():

    pantalla = np.zeros(
        (ALTO, ANCHO, 3),
        dtype=np.uint8
    )

    cv2.putText(
        pantalla,
        "MENU PRINCIPAL",
        (210, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (255, 255, 255),
        3
    )

    # Practice button

    cv2.rectangle(
        pantalla,
        (150, 220),
        (380, 320),
        (180, 105, 255),
        -1
    )

    cv2.putText(
        pantalla,
        "PRACTICA",
        (195, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    # Race button

    cv2.rectangle(
        pantalla,
        (420, 220),
        (650, 320),
        (0, 180, 0),
        -1
    )

    cv2.putText(
        pantalla,
        "CARRERA",
        (475, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    cv2.putText(
        pantalla,
        "Selecciona un modo",
        (275, 390),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        1
    )

    return pantalla


def mostrar_modo(modo):

    pantalla = np.zeros(
        (ALTO, ANCHO, 3),
        dtype=np.uint8
    )

    texto = "MODO " + modo.upper()

    tamaño = cv2.getTextSize(
        texto,
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        3
    )[0]

    x = (ANCHO - tamaño[0]) // 2

    cv2.putText(
        pantalla,
        texto,
        (x, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (255, 255, 255),
        3
    )

    texto2 = "EN PROCESO..."

    tamaño2 = cv2.getTextSize(
        texto2,
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        2
    )[0]

    x2 = (ANCHO - tamaño2[0]) // 2

    cv2.putText(
        pantalla,
        texto2,
        (x2, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    return pantalla


def ejecutar_practica():

    pantalla = mostrar_modo("practica")

    cv2.namedWindow("Menu")

    cv2.imshow("Menu", pantalla)

    print("Entrando en el modo práctica.")

    while True:

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

        if cv2.getWindowProperty(
            "Menu",
            cv2.WND_PROP_VISIBLE
        ) < 1:
            break

    cv2.destroyWindow("Menu")


def main():

    global seleccion

    try:

        # Calibrate all four colors before starting the main menu

        color_ranges = calibrate_colors()

        if color_ranges is None:
            print("No se puede iniciar el juego sin calibrar los colores.")
            return

        # Update password color ranges

        password.password_function.RANGOS = color_ranges

        # Prepare marker ranges for race mode

        race_color_ranges = {
            "rosa": color_ranges["rosa"],
            "morado": color_ranges["morado"]
        } 
        while True:

            seleccion = None

            cv2.namedWindow("Menu")

            cv2.setMouseCallback(
                "Menu",
                seleccionar_modo
            )

            # Main menu loop

            while seleccion is None:

                pantalla = mostrar_menu()

                cv2.imshow("Menu", pantalla)

                tecla = cv2.waitKey(1) & 0xFF

                if tecla == ord("q"):
                    return

                if cv2.getWindowProperty(
                    "Menu",
                    cv2.WND_PROP_VISIBLE
                ) < 1:
                    return

            # Select password according to the chosen mode

            if seleccion == "practica":

                contrasena = CONTRASENA_PRACTICA
                modo = "practica"

            else:

                contrasena = CONTRASENA_CARRERA
                modo = "carrera"

            # Close main menu while entering password

            cv2.destroyWindow("Menu")

            correcta = password.password_function.comprobar_contrasena(contrasena, color_ranges)

            if correcta:

                print("Entrando en el modo:", modo)

                if modo == "practica":

                    ejecutar_practica()

                elif modo == "carrera":

                    iniciar_modo_carrera(race_color_ranges)

            else:

                print("Contraseña incorrecta.")

            # Return to the main menu when the selected mode finishes

    finally:

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
