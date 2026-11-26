# test_detector.py
import cv2
from detector_hsv import detectar_marcas, dibujar_marcas

cap = cv2.VideoCapture(0)
while True:
    ok, frame = cap.read()
    if not ok:
        break
    centros, mascaras = detectar_marcas(frame)
    dibujar_marcas(frame, centros)
    cv2.imshow("camara", frame)
    cv2.imshow("rosa", mascaras["rosa"])
    cv2.imshow("azul", mascaras["azul"])
    cv2.imshow("amarillo", mascaras["amarillo"])
    cv2.imshow("verde", mascaras["verde"])
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()