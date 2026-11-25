
import cv2
import numpy as np
import time
import math
import os

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650

SPEED = 220
TURN_GAIN = 0.8

MIN_AREA = 300

CAR_WIDTH = 60
CAR_HEIGHT = 36

# Initial car position
START_X = 580
START_Y = 1050

# Initial direction: right
INITIAL_DIRECTION = 0

# HSV ranges for steering wheel markers
COLOR_RANGES = {
    "pink": ((164, 73, 147), (175, 167, 255)),
    "green": ((34, 57, 39), (91, 134, 214))
}

FOLDER = os.path.dirname(os.path.abspath(__file__))

circuit_path = os.path.join(FOLDER, "circuit.png")
car_path = os.path.join(FOLDER, "car.png")


# Load circuit
circuit = cv2.imdecode(
    np.fromfile(circuit_path, dtype=np.uint8),
    cv2.IMREAD_COLOR
)

# Load car while preserving transparency
original_car = cv2.imdecode(
    np.fromfile(car_path, dtype=np.uint8),
    cv2.IMREAD_UNCHANGED
)


if circuit is None:
    raise FileNotFoundError(
        f"Could not find circuit.png at: {circuit_path}"
    )

if original_car is None:
    raise FileNotFoundError(
        f"Could not find car.png at: {car_path}"
    )

print("Circuit loaded successfully.")
print("Car loaded successfully.")

MAP_HEIGHT, MAP_WIDTH = circuit.shape[:2]


original_car = cv2.resize(
    original_car,
    (CAR_WIDTH, CAR_HEIGHT)
)

# Make sure the image has an alpha channel
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

# Detect the green background
green_mask = cv2.inRange(
    circuit_hsv,
    np.array([35, 40, 100]),
    np.array([90, 255, 255])
)


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

    # The original car image faces left.
    # Rotate it by 180 degrees so that it starts facing right.
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

    rotated_car = cv2.warpAffine(
        original_car,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0)
    )

    return rotated_car


def check_collision(x, y, angle):

    radians = math.radians(angle)

    cosine = math.cos(radians)
    sine = math.sin(radians)

    # Check several points distributed
    # across the approximate car surface

    for dx in range(-22, 23, 6):

        for dy in range(-13, 14, 6):

            # Rotate each point according to the car's direction
            px = int(
                x + dx * cosine - dy * sine
            )

            py = int(
                y + dx * sine + dy * cosine
            )

            # Check map boundaries
            if px < 0 or px >= MAP_WIDTH:
                return True

            if py < 0 or py >= MAP_HEIGHT:
                return True

            # If the point is on the green area, a collision occurs
            if green_mask[py, px] > 0:
                return True

    return False


def draw_car(image, car, x, y):

    height, width = car.shape[:2]

    x1 = int(x - width / 2)
    y1 = int(y - height / 2)

    x2 = x1 + width
    y2 = y1 + height

    # Crop if the car goes outside the screen
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

    alpha = car_crop[:, :, 3] / 255.0

    for channel in range(3):

        roi[:, :, channel] = (
            alpha * car_crop[:, :, channel]
            + (1 - alpha) * roi[:, :, channel]
        ).astype(np.uint8)


cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open the camera.")

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

print("Place the steering wheel straight and press C to calibrate.")



while True:

    ok, frame = cap.read()

    if not ok:
        print("Error reading camera frame.")
        break

    current_time = time.time()

    dt = min(
        current_time - previous_time,
        0.05
    )

    previous_time = current_time

    # Detect markers
    pink = detect_marker(frame, "pink")
    green = detect_marker(frame, "green")

    # Draw markers
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

    # Display tracking status
    if not calibrated:

        cv2.putText(
            frame,
            "Place the steering wheel straight and press C",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    else:

        cv2.putText(
            frame,
            f"Steering angle: {steering_angle:.1f} degrees",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    if calibrated and not collision:

        # The steering wheel controls the car direction
        car_angle -= (
            steering_angle * TURN_GAIN * dt
        )

        radians = math.radians(car_angle)

        # Constant speed
        x += SPEED * math.cos(radians) * dt

        y += SPEED * math.sin(radians) * dt

        # Check for collision
        if check_collision(x, y, car_angle):

            print("YOU CRASHED!")

            collision = True
            collision_time = current_time

    if collision:

        cv2.putText(
            frame,
            "YOU CRASHED!",
            (150, 100),
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

    screen = cv2.getRectSubPix(
        circuit,
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        (float(x), float(y))
    )

    # Rotate and draw the car
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

        cv2.putText(
            screen,
            f"Speed: {SPEED}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    cv2.imshow("Race", screen)
    cv2.imshow("Steering Wheel Camera", frame)

    key = cv2.waitKey(1) & 0xFF

    # Calibrate with C
    if key == ord("c"):

        if pink is not None and green is not None:

            steering_wheel_center = (
                (pink[0] + green[0]) / 2,
                (pink[1] + green[1]) / 2
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

            steering_angle = 0.0

            start_time = time.time()
            previous_time = time.time()

            print("Steering wheel calibrated. The race starts now!")

        else:

            print("Both markers could not be detected.")

    # Close the program when the window is closed
    if cv2.getWindowProperty("Race", cv2.WND_PROP_VISIBLE) < 1:
        break

    if cv2.getWindowProperty("Steering Wheel Camera", cv2.WND_PROP_VISIBLE) < 1:
        break


cap.release()
cv2.destroyAllWindows()
