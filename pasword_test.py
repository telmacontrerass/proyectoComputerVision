
import cv2
import numpy as np
import time


# Rangos HSV de los colores
RANGOS = {
    "rosa": [
        ((164, 73, 147), (175, 167, 255))
    ],
    "azul": [
        ((94, 95, 101), (107, 187, 199))
    ],
    "verde": [
        ((34, 57, 39), (91, 134, 214))
    ],
    "amarillo": [
        ((23, 47, 136), (35, 139, 250))
    ]
}


# Colores para dibujar en la imagen (BGR)
COLORES_BGR = {
    "rosa": (180, 105, 255),
    "azul": (255, 0, 0),
    "verde": (0, 200, 0),
    "amarillo": (0, 255, 255)
}


# Contraseña que debe introducirse
CONTRASENA = ["azul", "amarillo", "rosa", "verde"]


# Parámetros de detección
AREA_MINIMA = 300
TIEMPO_ESTABLE = 1.5
TIEMPO_ESPERA = 3
TIEMPO_BLOQUEO = 1.0


# Inicializar cámara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se ha podido abrir la cámara.")
    exit()


# Variables de la contraseña
indice = 0
color_actual = None
inicio_color = None

inicio = time.time()
ultimo_registro = 0

empezar = False
terminado = False


def detectar_colores(frame):

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Máscara conjunta de todos los colores
    mascara_total = np.zeros(hsv.shape[:2], dtype=np.uint8)

    detecciones = {}

    kernel = np.ones((5, 5), np.uint8)

    for color, rangos in RANGOS.items():

        mascara_color = np.zeros(hsv.shape[:2], dtype=np.uint8)

        # Crear máscara para cada rango del color
        for inferior, superior in rangos:

            mascara = cv2.inRange(
                hsv,
                np.array(inferior),
                np.array(superior)
            )

            mascara_color = cv2.bitwise_or(
                mascara_color,
                mascara
            )

        # Eliminar ruido
        mascara_color = cv2.morphologyEx(
            mascara_color,
            cv2.MORPH_OPEN,
            kernel
        )

        mascara_color = cv2.morphologyEx(
            mascara_color,
            cv2.MORPH_CLOSE,
            kernel
        )

        # Añadir a la máscara conjunta
        mascara_total = cv2.bitwise_or(
            mascara_total,
            mascara_color
        )

        # Buscar contornos
        contornos, _ = cv2.findContours(
            mascara_color,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        mejor_contorno = None
        mayor_area = AREA_MINIMA

        for contorno in contornos:

            area = cv2.contourArea(contorno)

            if area > mayor_area:
                mayor_area = area
                mejor_contorno = contorno

        # Calcular centro del marcador
        if mejor_contorno is not None:

            M = cv2.moments(mejor_contorno)

            if M["m00"] != 0:

                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                detecciones[color] = (cx, cy)

            else:
                detecciones[color] = None

        else:
            detecciones[color] = None

    # Aplicar la máscara a la imagen original
    # Se mantienen los colores originales sobre fondo negro
    imagen_colores = cv2.bitwise_and(
        frame,
        frame,
        mask=mascara_total
    )

    return detecciones, imagen_colores


# Bucle principal
while True:

    ok, frame = cap.read()

    if not ok:
        print("No se ha podido recibir la imagen.")
        break

    tiempo_actual = time.time()

    # Detectar los cuatro colores
    detecciones, imagen_colores = detectar_colores(frame)

    # Espera inicial de 3 segundos
    if not empezar:

        restante = TIEMPO_ESPERA - (tiempo_actual - inicio)

        if restante <= 0:

            empezar = True
            print("Introduce la contraseña.")

        else:

            cv2.putText(
                frame,
                f"Comenzamos en: {restante:.1f}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )

    color_detectado = None

    # Detectar el marcador que está más arriba
    if empezar:

        candidatos = []

        for color, centro in detecciones.items():

            if centro is not None:

                cx, cy = centro

                candidatos.append((cy, color, cx))

        if candidatos:

            # El menor valor de Y corresponde al marcador más alto
            candidatos.sort(key=lambda x: x[0])

            cy, color_detectado, cx = candidatos[0]

            # Dibujar círculo en el marcador detectado
            cv2.circle(
                frame,
                (cx, cy),
                12,
                COLORES_BGR[color_detectado],
                -1
            )

            cv2.putText(
                frame,
                color_detectado,
                (cx + 15, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                COLORES_BGR[color_detectado],
                2
            )

    # Comprobar la contraseña
    if empezar and not terminado:

        # Esperar antes de aceptar otro color
        if tiempo_actual - ultimo_registro >= TIEMPO_BLOQUEO:

            if color_detectado is not None:

                if color_detectado != color_actual:

                    color_actual = color_detectado
                    inicio_color = tiempo_actual

                else:

                    tiempo_color = tiempo_actual - inicio_color

                    # Comprobar que el color lleva estable 1.5 segundos
                    if tiempo_color >= TIEMPO_ESTABLE:

                        print("Color detectado:", color_detectado)

                        esperado = CONTRASENA[indice]

                        if color_detectado == esperado:

                            indice += 1
                            ultimo_registro = tiempo_actual

                            if indice == len(CONTRASENA):

                                print("¡CONTRASEÑA CORRECTA!")
                                terminado = True
                                break

                            else:

                                print("Correcto. Ya puedes poner el siguiente.")

                                color_actual = None
                                inicio_color = None

                        else:

                            print("¡CONTRASEÑA INCORRECTA!")
                            terminado = True
                            break

            else:

                # Si no se detecta ningún marcador, reiniciar estabilidad
                color_actual = None
                inicio_color = None

    # Mostrar las dos ventanas
    cv2.imshow("Camara", frame)
    cv2.imshow("Colores detectados", imagen_colores)

    # Salir pulsando Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# Cerrar cámara y ventanas
cap.release()
cv2.destroyAllWindows()
