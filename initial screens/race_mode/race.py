import cv2
import numpy as np
import time
import math
import os
import threading

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650

SPEED = 220
TURN_GAIN = 0.8

MIN_AREA = 300

CAR_WIDTH = 60
CAR_HEIGHT = 36

START_X = 495
START_Y = 875

INITIAL_DIRECTION = 0

COLOR_RANGES = {
    "pink": ((164, 73, 147), (175, 167, 255)),
    "green": ((34, 57, 39), (91, 134, 214))
}

# Camera overlay
CAMERA_WIDTH = 240
CAMERA_HEIGHT = 180

camera_x = 15
camera_y = 15

dragging_camera = False
drag_offset_x = 0
drag_offset_y = 0

FOLDER = os.path.dirname(os.path.abspath(__file__))

circuit_path = os.path.join(FOLDER, "circuit_1.png")
car_path = os.path.join(FOLDER, "car.png")

circuit = cv2.imdecode(
    np.fromfile(circuit_path, dtype=np.uint8),
    cv2.IMREAD_COLOR
)

original_car = cv2.imdecode(
    np.fromfile(car_path, dtype=np.uint8),
    cv2.IMREAD_UNCHANGED
)

if circuit is None:
    raise FileNotFoundError("Could not load circuit.png")

if original_car is None:
    raise FileNotFoundError("Could not load car.png")

MAP_HEIGHT, MAP_WIDTH = circuit.shape[:2]

print("Circuit loaded successfully.")
print("Car loaded successfully.")

original_car = cv2.resize(
    original_car,
    (CAR_WIDTH, CAR_HEIGHT)
)

if len(original_car.shape) == 2:
    original_car = cv2.cvtColor(
        original_car,
        cv2.COLOR_GRAY2BGRA
    )

elif original_car.shape[2] == 3:
    original_car = cv2.cvtColor(
        original_car,
        cv2.COLOR_BGR2BGRA
    )

circuit_hsv = cv2.cvtColor(
    circuit,
    cv2.COLOR_BGR2HSV
)

green_mask = cv2.inRange(
    circuit_hsv,
    np.array([35, 40, 100]),
    np.array([90, 255, 255])
)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError("Could not open the camera.")

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

latest_frame = None
camera_lock = threading.Lock()
stop_camera = False


def read_camera():

    global latest_frame

    while not stop_camera:

        ok, frame = camera.read()

        if ok and frame is not None:

            with camera_lock:
                latest_frame = frame

        else:
            time.sleep(0.01)


camera_thread = threading.Thread(
    target=read_camera,
    daemon=True
)

camera_thread.start()

print("Camera thread started.")

def detect_marker(frame, color):

    hsv = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2HSV
    )

    lower, upper = COLOR_RANGES[color]

    mask = cv2.inRange(
        hsv,
        np.array(lower),
        np.array(upper)
    )

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    best_contour = None
    largest_area = MIN_AREA

    for contour in contours:

        area = cv2.contourArea(contour)

        if area > largest_area:
            largest_area = area
            best_contour = contour

    if best_contour is None:
        return None

    M = cv2.moments(best_contour)

    if M["m00"] == 0:
        return None

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    return (cx, cy)

def normalize_angle(angle):

    return (angle + 180) % 360 - 180


def calculate_angle(point1, point2):

    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]

    return math.degrees(
        math.atan2(dy, dx)
    )

def rotate_car(angle):

    height, width = original_car.shape[:2]

    center = (width // 2, height // 2)

    matrix = cv2.getRotationMatrix2D(
        center,
        180 - angle,
        1.0
    )

    cosine = abs(matrix[0, 0])
    sine = abs(matrix[0, 1])

    new_width = int(
        height * sine + width * cosine
    )

    new_height = int(
        height * cosine + width * sine
    )

    matrix[0, 2] += new_width / 2 - center[0]
    matrix[1, 2] += new_height / 2 - center[1]

    return cv2.warpAffine(
        original_car,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0)
    )

def check_collision(x, y, angle):

    radians = math.radians(angle)

    cosine = math.cos(radians)
    sine = math.sin(radians)

    for dx in range(-22, 23, 6):

        for dy in range(-13, 14, 6):

            px = int(
                x + dx * cosine - dy * sine
            )

            py = int(
                y + dx * sine + dy * cosine
            )

            if px < 0 or px >= MAP_WIDTH:
                return True

            if py < 0 or py >= MAP_HEIGHT:
                return True

            if green_mask[py, px] > 0:
                return True

    return False

def draw_car(image, car, x, y):

    height, width = car.shape[:2]

    x1 = int(x - width / 2)
    y1 = int(y - height / 2)

    x2 = x1 + width
    y2 = y1 + height

    x1_crop = max(0, x1)
    y1_crop = max(0, y1)

    x2_crop = min(image.shape[1], x2)
    y2_crop = min(image.shape[0], y2)

    if x1_crop >= x2_crop or y1_crop >= y2_crop:
        return

    car_crop = car[
        y1_crop - y1:y2_crop - y1,
        x1_crop - x1:x2_crop - x1
    ]

    roi = image[
        y1_crop:y2_crop,
        x1_crop:x2_crop
    ]

    alpha = car_crop[:, :, 3:4] / 255.0

    image[
        y1_crop:y2_crop,
        x1_crop:x2_crop
    ] = (
        alpha * car_crop[:, :, :3]
        + (1 - alpha) * roi
    ).astype(np.uint8)

def create_circuit_view(x, y):

    screen = np.zeros(
        (SCREEN_HEIGHT, SCREEN_WIDTH, 3),
        dtype=np.uint8
    )

    half_width = SCREEN_WIDTH // 2
    half_height = SCREEN_HEIGHT // 2

    left = int(x) - half_width
    top = int(y) - half_height

    src_left = max(0, left)
    src_top = max(0, top)

    src_right = min(MAP_WIDTH, left + SCREEN_WIDTH)
    src_bottom = min(MAP_HEIGHT, top + SCREEN_HEIGHT)

    dst_left = src_left - left
    dst_top = src_top - top

    dst_right = dst_left + (src_right - src_left)
    dst_bottom = dst_top + (src_bottom - src_top)

    if src_right > src_left and src_bottom > src_top:

        screen[
            dst_top:dst_bottom,
            dst_left:dst_right
        ] = circuit[
            src_top:src_bottom,
            src_left:src_right
        ]

    return screen

def move_camera(event, mouse_x, mouse_y, flags, param):

    global camera_x, camera_y
    global dragging_camera
    global drag_offset_x, drag_offset_y

    if event == cv2.EVENT_LBUTTONDOWN:

        if (
            camera_x <= mouse_x <= camera_x + CAMERA_WIDTH
            and
            camera_y <= mouse_y <= camera_y + CAMERA_HEIGHT
        ):

            dragging_camera = True

            drag_offset_x = mouse_x - camera_x
            drag_offset_y = mouse_y - camera_y

    elif event == cv2.EVENT_MOUSEMOVE:

        if dragging_camera:

            camera_x = mouse_x - drag_offset_x
            camera_y = mouse_y - drag_offset_y

            camera_x = max(
                0,
                min(camera_x, SCREEN_WIDTH - CAMERA_WIDTH)
            )

            camera_y = max(
                0,
                min(camera_y, SCREEN_HEIGHT - CAMERA_HEIGHT)
            )

    elif event == cv2.EVENT_LBUTTONUP:

        dragging_camera = False

x = float(START_X)
y = float(START_Y)

car_angle = float(INITIAL_DIRECTION)

steering_angle = 0.0

steering_wheel_center = None

reference_angle = None
pink_reference_angle = None
green_reference_angle = None

calibrated = False

start_time = time.time()
previous_time = time.time()

collision = False
collision_time = 0

cv2.namedWindow("Race", cv2.WINDOW_NORMAL)

cv2.resizeWindow(
    "Race",
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)

cv2.setMouseCallback(
    "Race",
    move_camera
)

print("Game started.")
print("Place the steering wheel straight and press C to calibrate.")

try:

    while True:

        current_time = time.time()

        dt = min(
            current_time - previous_time,
            0.05
        )

        previous_time = current_time

        # ------------------------------------------
        # GET LATEST CAMERA FRAME
        # ------------------------------------------

        with camera_lock:

            if latest_frame is not None:
                frame = latest_frame.copy()
            else:
                frame = None

        screen = create_circuit_view(x, y)

        # Draw car in the centre
        rotated_car = rotate_car(car_angle)

        draw_car(
            screen,
            rotated_car,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2
        )

        if calibrated:

            if collision:
                race_time = collision_time - start_time
            else:
                race_time = current_time - start_time

            cv2.putText(
                screen,
                f"Time: {race_time:.1f} s",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        else:

            cv2.putText(
                screen,
                "Press C to calibrate",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        if frame is not None:

            pink = detect_marker(frame, "pink")
            green = detect_marker(frame, "green")

            # Draw detected markers
            if pink is not None:

                cv2.circle(
                    frame,
                    pink,
                    10,
                    (180, 105, 255),
                    -1
                )

            if green is not None:

                cv2.circle(
                    frame,
                    green,
                    10,
                    (0, 200, 0),
                    -1
                )

            if calibrated:

                if pink is not None and green is not None:

                    current_angle = calculate_angle(
                        pink,
                        green
                    )

                    steering_angle = normalize_angle(
                        current_angle - reference_angle
                    )

                elif pink is not None:

                    current_angle = calculate_angle(
                        steering_wheel_center,
                        pink
                    )

                    steering_angle = normalize_angle(
                        current_angle - pink_reference_angle
                    )

                elif green is not None:

                    current_angle = calculate_angle(
                        steering_wheel_center,
                        green
                    )

                    steering_angle = normalize_angle(
                        current_angle - green_reference_angle
                    )

            if calibrated and not collision:

                car_angle -= (
                    steering_angle * TURN_GAIN * dt
                )

                radians = math.radians(car_angle)

                x += SPEED * math.cos(radians) * dt
                y += SPEED * math.sin(radians) * dt

                if check_collision(x, y, car_angle):

                    collision = True
                    collision_time = current_time

                    print("YOU CRASHED!")

        else:

            cv2.putText(
                screen,
                "Waiting for camera...",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        if collision:

            cv2.putText(
                screen,
                "YOU CRASHED!",
                (SCREEN_WIDTH // 2 - 130, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

            if current_time - collision_time >= 1.5:

                x = float(START_X)
                y = float(START_Y)

                car_angle = float(INITIAL_DIRECTION)

                start_time = time.time()

                collision = False

                print("Race restarted.")

        if frame is not None:

            mirrored_frame = cv2.flip(frame, 1)

            camera_image = cv2.resize(
                mirrored_frame,
                (CAMERA_WIDTH, CAMERA_HEIGHT)
            )

            screen[
                camera_y:camera_y + CAMERA_HEIGHT,
                camera_x:camera_x + CAMERA_WIDTH
            ] = camera_image

            cv2.rectangle(
                screen,
                (camera_x - 2, camera_y - 2),
                (
                    camera_x + CAMERA_WIDTH + 2,
                    camera_y + CAMERA_HEIGHT + 2
                ),
                (255, 255, 255),
                2
            )

        cv2.imshow("Race", screen)

        # IMPORTANT: Process window events every frame
        key = cv2.waitKey(1) & 0xFF

        if key == ord("c") and not calibrated:

            if frame is not None:

                pink = detect_marker(frame, "pink")
                green = detect_marker(frame, "green")

                if pink is not None and green is not None:

                    steering_wheel_center = (
                        (pink[0] + green[0]) // 2,
                        (pink[1] + green[1]) // 2
                    )

                    reference_angle = calculate_angle(
                        pink,
                        green
                    )

                    pink_reference_angle = calculate_angle(
                        steering_wheel_center,
                        pink
                    )

                    green_reference_angle = calculate_angle(
                        steering_wheel_center,
                        green
                    )

                    calibrated = True

                    start_time = time.time()
                    previous_time = time.time()

                    print("Steering wheel calibrated!")

                else:

                    print(
                        "Both pink and green markers must be visible."
                    )

        if key == 27:
            break

        if cv2.getWindowProperty(
            "Race",
            cv2.WND_PROP_VISIBLE
        ) < 1:
            break

finally:

    stop_camera = True

    camera.release()

    camera_thread.join(timeout=1.0)

    cv2.destroyAllWindows()

    print("Game closed.")
