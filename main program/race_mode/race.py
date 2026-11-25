
import cv2
import numpy as np
import time
import math
import os
import threading


FOLDER = os.path.dirname(os.path.abspath(__file__))

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720

GAME_WIDTH = 900
GAME_HEIGHT = 650

SPEED = 150
TURN_GAIN = 0.8

MIN_AREA = 300

CAR_WIDTH = 60
CAR_HEIGHT = 36

START_POSITIONS = {
    1: {
        "x": 480,
        "y": 880,
        "angle": 0
    },
    2: {
        "x": 185,
        "y": 430,
        "angle": 120
    },
    3: {
        "x": 290,
        "y": 385,
        "angle": 120
    },
    4: {
        "x": 450,
        "y": 474,
        "angle": 50
    }
}

COLOR_RANGES = {
    "pink": ((164, 73, 147), (175, 167, 255)),
    "green": ((34, 57, 39), (91, 134, 214))
}

CAMERA_WIDTH = 240
CAMERA_HEIGHT = 180
NUM_VUELTAS = 3

camera_x = 15
camera_y = 15

dragging_camera = False

drag_offset_x = 0
drag_offset_y = 0

selected_circuit = None
back_requested = False
current_screen = "menu"

CARD_WIDTH = 400
CARD_HEIGHT = 230
IMAGE_HEIGHT = 185

CARD_RECTS = [
    (35, 125, 400, 230),
    (465, 125, 400, 230),
    (35, 405, 400, 230),
    (465, 405, 400, 230)
]

DIFFICULTIES = [
    "FACIL",
    "INTERMEDIO",
    "DIFICIL",
    "EXPERTO"
]


# Load car image

car_path = os.path.join(FOLDER, "car.png")

original_car = cv2.imdecode(
    np.fromfile(car_path, dtype=np.uint8),
    cv2.IMREAD_UNCHANGED
)

if original_car is None:
    raise FileNotFoundError("Could not load car.png")

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


# Load the four circuits

circuits = []

for i in range(1, 5):

    path = os.path.join(
        FOLDER,
        f"circuit_{i}.png"
    )

    circuit = cv2.imdecode(
        np.fromfile(path, dtype=np.uint8),
        cv2.IMREAD_COLOR
    )

    if circuit is None:
        raise FileNotFoundError(
            f"Could not load circuit_{i}.png"
        )

    circuits.append(circuit)

print("All four circuits loaded successfully.")


# Prepare circuit thumbnails

def create_thumbnail(image):

    height, width = image.shape[:2]

    scale = min(
        CARD_WIDTH / width,
        IMAGE_HEIGHT / height
    )

    new_width = int(width * scale)
    new_height = int(height * scale)

    resized = cv2.resize(
        image,
        (new_width, new_height)
    )

    thumbnail = np.zeros(
        (IMAGE_HEIGHT, CARD_WIDTH, 3),
        dtype=np.uint8
    )

    x_offset = (CARD_WIDTH - new_width) // 2
    y_offset = (IMAGE_HEIGHT - new_height) // 2

    thumbnail[
        y_offset:y_offset + new_height,
        x_offset:x_offset + new_width
    ] = resized

    return thumbnail


thumbnails = [
    create_thumbnail(circuit)
    for circuit in circuits
]


# Handle mouse clicks and camera movement

def mouse_callback(event, mouse_x, mouse_y, flags, param):

    global selected_circuit
    global back_requested
    global dragging_camera
    global drag_offset_x, drag_offset_y
    global camera_x, camera_y

    if current_screen == "menu":

        if event == cv2.EVENT_LBUTTONDOWN:

            for i, rect in enumerate(CARD_RECTS):

                x, y, width, height = rect

                if (
                    x <= mouse_x <= x + width
                    and
                    y <= mouse_y <= y + height
                ):

                    selected_circuit = i
                    return

    elif current_screen == "game":

        if event == cv2.EVENT_LBUTTONDOWN:

            # Back button

            if (
                GAME_WIDTH - 65 <= mouse_x <= GAME_WIDTH - 15
                and
                10 <= mouse_y <= 50
            ):

                back_requested = True
                dragging_camera = False
                return

            # Start dragging camera

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
                    min(camera_x, GAME_WIDTH - CAMERA_WIDTH)
                )

                camera_y = max(
                    0,
                    min(camera_y, GAME_HEIGHT - CAMERA_HEIGHT)
                )

        elif event == cv2.EVENT_LBUTTONUP:

            dragging_camera = False


# Draw circuit selection screen

def draw_selection_screen():

    screen = np.full(
        (GAME_HEIGHT, GAME_WIDTH, 3),
        (115, 197, 94),
        dtype=np.uint8
    )

    screen[:] = (35, 30, 25)

    cv2.putText(
        screen,
        "SELECCIONA EL CIRCUITO",
        (175, 75),
        cv2.FONT_HERSHEY_DUPLEX,
        1.5,
        (115, 197, 94),
        3
    )

    for i in range(4):

        x, y, width, height = CARD_RECTS[i]
        thumbnail = thumbnails[i]

        cv2.rectangle(
            screen,
            (x - 5, y - 5),
            (x + width + 5, y + height + 5),
            (80, 80, 80),
            -1
        )

        screen[
            y:y + IMAGE_HEIGHT,
            x:x + CARD_WIDTH
        ] = thumbnail

        cv2.rectangle(
            screen,
            (x, y),
            (x + CARD_WIDTH, y + IMAGE_HEIGHT),
            (255, 255, 255),
            2
        )

        difficulty = DIFFICULTIES[i]

        text_size = cv2.getTextSize(
            difficulty,
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            2
        )[0]

        text_x = x + (width - text_size[0]) // 2

        cv2.putText(
            screen,
            difficulty,
            (text_x, y + IMAGE_HEIGHT + 35),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (255, 255, 255),
            2
        )

    cv2.putText(
        screen,
        "Click on a circuit to play",
        (350, 685),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (180, 180, 180),
        1
    )

    return screen


def normalize_angle(angle):

    return (angle + 180) % 360 - 180


def calculate_angle(point1, point2):

    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]

    return math.degrees(
        math.atan2(dy, dx)
    )


# Detect steering wheel markers

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


# Rotate car

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


# Draw car

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


# Create visible circuit area

def create_circuit_view(circuit, x, y):

    map_height, map_width = circuit.shape[:2]

    screen = np.zeros(
        (GAME_HEIGHT, GAME_WIDTH, 3),
        dtype=np.uint8
    )

    half_width = GAME_WIDTH // 2
    half_height = GAME_HEIGHT // 2

    left = int(x) - half_width
    top = int(y) - half_height

    src_left = max(0, left)
    src_top = max(0, top)

    src_right = min(map_width, left + GAME_WIDTH)
    src_bottom = min(map_height, top + GAME_HEIGHT)

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


# Detect crossing of the finish line

def crossed_finish_line(x1, y1, x2, y2, finish_mask):

    distance = math.hypot(x2 - x1, y2 - y1)
    steps = max(int(distance / 2), 1)

    map_height, map_width = finish_mask.shape

    for i in range(steps + 1):

        t = i / steps

        px = int(x1 + (x2 - x1) * t)
        py = int(y1 + (y2 - y1) * t)

        if 0 <= px < map_width and 0 <= py < map_height:

            if finish_mask[py, px] > 0:
                return True

    return False


# Check collisions with green area

def check_collision(x, y, angle, green_mask):

    map_height, map_width = green_mask.shape

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

            if px < 0 or px >= map_width:
                return True

            if py < 0 or py >= map_height:
                return True

            if green_mask[py, px] > 0:
                return True

    return False


# Run selected race

def run_race(circuit, circuit_number):

    global current_screen
    global back_requested

    current_screen = "game"
    back_requested = False

    circuit_hsv = cv2.cvtColor(
        circuit,
        cv2.COLOR_BGR2HSV
    )

    green_mask = cv2.inRange(
        circuit_hsv,
        np.array([35, 40, 100]),
        np.array([90, 255, 255])
    )

    # Detect the red finish line

    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    red_mask1 = cv2.inRange(
        circuit_hsv,
        lower_red1,
        upper_red1
    )

    red_mask2 = cv2.inRange(
        circuit_hsv,
        lower_red2,
        upper_red2
    )

    finish_mask = cv2.bitwise_or(
        red_mask1,
        red_mask2
    )

    kernel = np.ones((5, 5), np.uint8)

    finish_mask = cv2.dilate(
        finish_mask,
        kernel,
        iterations=1
    )

    # Get starting position for the selected circuit

    start_position = START_POSITIONS[circuit_number]

    x = float(start_position["x"])
    y = float(start_position["y"])

    car_angle = float(start_position["angle"])

    steering_angle = 0.0

    steering_wheel_center = None
    reference_angle = None
    pink_reference_angle = None
    green_reference_angle = None

    calibrated = False

    collision = False
    collision_time = 0

    finish_crossings = 0
    finish_line_armed = True
    finished = False

    start_time = time.time()
    previous_time = time.time()

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():

        print("Could not open the camera.")
        camera.release()
        return

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    latest_frame = None

    camera_lock = threading.Lock()
    stop_camera = threading.Event()

    def read_camera():

        nonlocal latest_frame

        while not stop_camera.is_set():

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

    print(
        f"Race started: circuit {circuit_number}. "
        "Press C to calibrate."
    )

    try:

        while True:

            if back_requested:
                break

            current_time = time.time()

            dt = min(
                current_time - previous_time,
                0.05
            )

            previous_time = current_time

            with camera_lock:

                if latest_frame is not None:
                    frame = latest_frame.copy()

                else:
                    frame = None

            screen = create_circuit_view(
                circuit,
                x,
                y
            )

            rotated_car = rotate_car(car_angle)

            draw_car(
                screen,
                rotated_car,
                GAME_WIDTH // 2,
                GAME_HEIGHT // 2
            )

            pink = None
            green = None

            if frame is not None:

                pink = detect_marker(frame, "pink")
                green = detect_marker(frame, "green")

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

            if calibrated and not collision and not finished:

                previous_x = x
                previous_y = y

                car_angle -= (
                    steering_angle * TURN_GAIN * dt
                )

                radians = math.radians(car_angle)

                x += SPEED * math.cos(radians) * dt
                y += SPEED * math.sin(radians) * dt

                if finish_line_armed:

                    if crossed_finish_line(
                        previous_x,
                        previous_y,
                        x,
                        y,
                        finish_mask
                    ):

                        finish_crossings += 1
                        finish_line_armed = False

                        print(
                            f"Finish line crossed: {finish_crossings}"
                        )

                        if finish_crossings >= NUM_VUELTAS:

                            finished = True

                            print(f"{NUM_VUELTAS} LAPS COMPLETED!")
                            print("CIRCUIT COMPLETED!")

                else:

                    px = int(x)
                    py = int(y)

                    if (
                        0 <= px < finish_mask.shape[1]
                        and
                        0 <= py < finish_mask.shape[0]
                    ):

                        if finish_mask[py, px] == 0:
                            finish_line_armed = True

                if not finished and check_collision(
                    x,
                    y,
                    car_angle,
                    green_mask
                ):

                    collision = True
                    collision_time = current_time

                    print("YOU CRASHED!")

            if collision:

                cv2.putText(
                    screen,
                    "Te has chocado",
                    (GAME_WIDTH // 2 - 130, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

                if current_time - collision_time >= 1.5:

                    # Reset car to the starting position of this circuit

                    x = float(start_position["x"])
                    y = float(start_position["y"])

                    car_angle = float(start_position["angle"])

                    start_time = time.time()

                    finish_crossings = 0
                    finish_line_armed = True
                    finished = False

                    collision = False

                    print("Race restarted.")

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
                    "Presiona C para calibrar",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

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

            # Show circuit completion message

            if finished:

                cv2.rectangle(
                    screen,
                    (120, 230),
                    (780, 420),
                    (35, 30, 25),
                    -1
                )

                cv2.putText(
                    screen,
                    "1 VUELTA COMPLETADA",
                    (190, 305),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.1,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    screen,
                    "CIRCUITO COMPLETADO!",
                    (175, 365),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.1,
                    (255, 255, 255),
                    2
                )

            # Back button

            cv2.rectangle(
                screen,
                (GAME_WIDTH - 65, 10),
                (GAME_WIDTH - 15, 50),
                (50, 50, 50),
                -1
            )

            cv2.rectangle(
                screen,
                (GAME_WIDTH - 65, 10),
                (GAME_WIDTH - 15, 50),
                (255, 255, 255),
                2
            )

            cv2.putText(
                screen,
                "<",
                (GAME_WIDTH - 52, 41),
                cv2.FONT_HERSHEY_DUPLEX,
                1,
                (255, 255, 255),
                2
            )

            cv2.imshow("Race", screen)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("c") and not calibrated:

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

        stop_camera.set()

        camera.release()

        camera_thread.join(timeout=1.0)

        print("Returning to circuit selection.")


# Start race mode from main.py

def iniciar_modo_carrera():

    global current_screen
    global selected_circuit
    global back_requested

    current_screen = "menu"
    selected_circuit = None
    back_requested = False

    cv2.namedWindow(
        "Race",
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        "Race",
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    )

    cv2.setMouseCallback(
        "Race",
        mouse_callback
    )

    print("Choose a circuit to start.")

    try:

        while True:

            if current_screen == "menu":

                menu = draw_selection_screen()

                cv2.imshow("Race", menu)

                key = cv2.waitKey(20) & 0xFF

                # Press Q to return to the main menu

                if key == ord("q"):
                    break

                if cv2.getWindowProperty(
                    "Race",
                    cv2.WND_PROP_VISIBLE
                ) < 1:

                    break

                if selected_circuit is not None:

                    circuit_number = selected_circuit + 1

                    circuit_to_play = circuits[selected_circuit]

                    print(
                        f"Selected circuit {circuit_number}: "
                        f"{DIFFICULTIES[selected_circuit]}"
                    )

                    selected_circuit = None

                    run_race(
                        circuit_to_play,
                        circuit_number
                    )

                    current_screen = "menu"
                    back_requested = False

                    if cv2.getWindowProperty(
                        "Race",
                        cv2.WND_PROP_VISIBLE
                    ) < 1:

                        break

    finally:

        cv2.destroyWindow("Race")

        current_screen = "menu"
        selected_circuit = None
        back_requested = False

        print("Exiting race mode.")
