
import cv2
import numpy as np

from password_function import comprobar_contrasena
from race_mode.race import iniciar_modo_carrera


CONTRASENA_PRACTICA = ["azul", "amarillo", "rosa", "verde"]
CONTRASENA_CARRERA = ["rosa", "verde", "amarillo", "azul"]

ANCHO = 800
ALTO = 500

seleccion = None


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

    print("Entering practice mode.")

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

            correcta = comprobar_contrasena(contrasena)

            if correcta:

                print("Entering mode:", modo)

                if modo == "practica":

                    ejecutar_practica()

                elif modo == "carrera":

                    iniciar_modo_carrera()

            else:

                print("Incorrect password.")

            # When the selected mode finishes, return to main menu

    finally:

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
