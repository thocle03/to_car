import cv2
import numpy as np
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from collections import deque

# --- Constantes PWM (en 16 bits pour PCA9685) ---
def pwm12_to_16(val):
    return int(val * 65535 / 4096)

NEUTRAL = pwm12_to_16(307)
FORWARD = pwm12_to_16(410)
BACKWARD = pwm12_to_16(205)
LEFT = pwm12_to_16(520)
RIGHT = pwm12_to_16(105)
MOTOR_DEADZONE = pwm12_to_16(317)

# --- PCA9685 ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

THROTTLE_CHANNEL = 0
STEERING_CHANNEL = 1

# --- Caméra ---
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 736)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 414)

# --- Moyennes glissantes ---
throttle_history = deque([NEUTRAL] * 3, maxlen=3)
steering_history = deque([NEUTRAL] * 1, maxlen=1)

def smooth(val, history):
    history.append(val)
    return int(np.mean(history))

def detect_red_triangle(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    triangles = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
        if len(approx) == 3 and cv2.contourArea(cnt) > 100:
            triangles.append(cnt)

    if not triangles:
        return None, None, None

    largest = max(triangles, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    center_x = x + w // 2
    return center_x, w, h

def estimate_distance(triangle_width_px, known_width_cm=5.0, focal_length_px=240):
    try:
        return round((known_width_cm * focal_length_px) / triangle_width_px, 2)
    except ZeroDivisionError:
        return -1

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cx, w, h = detect_red_triangle(frame)
        if cx is not None:
            offset = cx - (frame.shape[1] // 2)
            distance = estimate_distance(w)

            # --- Throttle (vitesse proportionnelle à la distance, plage divisée par 2) ---
            min_distance = 23
            max_distance = 275
            if distance > min_distance:
                ratio = np.clip((distance - min_distance) / (max_distance - min_distance), 0, 1)
                raw_throttle = MOTOR_DEADZONE + ratio * ((FORWARD - MOTOR_DEADZONE) / 2)
                throttle = smooth(int(raw_throttle), throttle_history)
            else:
                throttle = smooth(NEUTRAL, throttle_history)

            # --- Steering (modéré par la vitesse) ---
            max_offset = frame.shape[1] // 2
            offset = cx - max_offset

            if throttle > MOTOR_DEADZONE:
                throttle_ratio = (throttle - MOTOR_DEADZONE) / ((FORWARD - MOTOR_DEADZONE) / 2)
                steering_range = 1.0 - throttle_ratio * 0.999  # max ~3% de braquage à plein régime
                steering_range = np.clip(steering_range, 0.001, 1.0)  # sécurité pour ne pas tomber à 0
            else:
                 steering_range = 1.0

            raw_steering = NEUTRAL + (offset / max_offset) * (RIGHT - NEUTRAL) * steering_range
            steering = smooth(int(np.clip(raw_steering, min(LEFT, RIGHT), max(LEFT, RIGHT))), steering_history)

        else:
            throttle = smooth(NEUTRAL, throttle_history)
            steering = smooth(NEUTRAL, steering_history)
            distance = -1

        # --- Envoi PWM ---
        pca.channels[THROTTLE_CHANNEL].duty_cycle = throttle
        pca.channels[STEERING_CHANNEL].duty_cycle = steering

        # --- Console ---
        print(f"throttle: {throttle}, steering: {steering}, distance: {distance} cm")

        time.sleep(0.01)  # ~50 FPS max

except KeyboardInterrupt:
    print("Arrêt par l'utilisateur.")
finally:
    pca.channels[THROTTLE_CHANNEL].duty_cycle = NEUTRAL
    pca.channels[STEERING_CHANNEL].duty_cycle = NEUTRAL
    cap.release()

