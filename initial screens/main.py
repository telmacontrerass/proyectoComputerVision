import cv2
import numpy as np

from password_function import comprobar_contrasena


# Contraseñas de cada modo
CONTRASENA_PRACTICA = ["azul", "amarillo", "rosa", "verde"]

# Contraseña  para carrera
CONTRASENA_CARRERA = ["rosa", "verde", "amarillo", "azul"]


# Tamaño de las pantallas
ANCHO = 800
ALTO = 500


# Variable para guardar la selección del menú
seleccion = None


# Detectar clics del ratón
def seleccionar_modo(evento, x, y, flags, param):

    global seleccion

    if evento == cv2.EVENT_LBUTTONDOWN:

        # Botón modo práctica
        if 150 <= x <= 380 and 220 <= y <= 320:
            seleccion = "practica"

        # Botón modo carrera
        elif 420 <= x <= 650 and 220 <= y <= 320:
            seleccion = "carrera"


# Crear pantalla principal
def mostrar_menu():

    pantalla = np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)

    cv2.putText(
        pantalla,
        "MENU PRINCIPAL",
        (210, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (255, 255, 255),
        3
    )

    # Botón práctica
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

    # Botón carrera
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


# Mostrar pantalla de modo en proceso
def mostrar_modo(modo):

    pantalla = np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)

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


# Bucle principal
cv2.namedWindow("Menu")
cv2.setMouseCallback("Menu", seleccionar_modo)

while True:

    seleccion = None

    # Mostrar menú principal
    while seleccion is None:

        pantalla = mostrar_menu()

        cv2.imshow("Menu", pantalla)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            cv2.destroyAllWindows()
            exit()

    # Seleccionar contraseña según el modo
    if seleccion == "practica":

        contrasena = CONTRASENA_PRACTICA
        modo = "practica"

    else:

        contrasena = CONTRASENA_CARRERA
        modo = "carrera"

    # Ocultar el menú mientras se introduce la contraseña
    cv2.destroyWindow("Menu")

    # Comprobar contraseña
    correcta = comprobar_contrasena(contrasena)

    if correcta:

        # Mostrar pantalla correspondiente
        pantalla = mostrar_modo(modo)

        cv2.namedWindow("Menu")
        cv2.imshow("Menu", pantalla)

        print("Entrando en modo", modo)

        # Esperar hasta pulsar Q para volver al menú
        while True:

            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("q"):
                break

        cv2.destroyWindow("Menu")

    # Si es incorrecta, el bucle vuelve al menú principal


cv2.destroyAllWindows()
