from flask import Flask
import board
import busio
import time
from adafruit_pca9685 import PCA9685
import threading

app = Flask(__name__)

# --- Conversion 12-bit PWM to 16-bit ---
def pwm12_to_16(val):
    return int(val * 65535 / 4096)

# --- PWM constants ---
NEUTRAL = pwm12_to_16(307)
FULL_FORWARD = pwm12_to_16(410)
FULL_BACKWARD = pwm12_to_16(205)
LEFT = pwm12_to_16(520)
RIGHT = pwm12_to_16(105)

# --- 10% throttle ---
FORWARD_10 = int(NEUTRAL + 0.04 * (FULL_FORWARD - NEUTRAL))
BACKWARD_10 = int(NEUTRAL - 0.05 * (NEUTRAL - FULL_BACKWARD))

# --- Init PCA9685 ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

THROTTLE_CHANNEL = 0
STEERING_CHANNEL = 1

# --- Stop all motors ---
def stop():
    pca.channels[THROTTLE_CHANNEL].duty_cycle = NEUTRAL
    pca.channels[STEERING_CHANNEL].duty_cycle = NEUTRAL

# --- Basic timed drive ---
def timed_drive(throttle_value, duration=3):
    stop()
    pca.channels[THROTTLE_CHANNEL].duty_cycle = throttle_value
    pca.channels[STEERING_CHANNEL].duty_cycle = NEUTRAL
    time.sleep(duration)
    stop()

# --- Drive + turn at the same time ---
def timed_drive_with_steering(throttle_value, steering_value, duration=3):
    stop()
    pca.channels[THROTTLE_CHANNEL].duty_cycle = throttle_value
    pca.channels[STEERING_CHANNEL].duty_cycle = steering_value
    time.sleep(duration)
    stop()

# --- Routes Flask ---
@app.route('/forward')
def forward():
    threading.Thread(target=timed_drive, args=(FORWARD_10,)).start()
    return "Avance 3s à 10%"

@app.route('/backward')
def backward():
    threading.Thread(target=timed_drive, args=(BACKWARD_10,)).start()
    return "Recule 3s à 10%"

@app.route('/left')
def left():
    pca.channels[STEERING_CHANNEL].duty_cycle = LEFT
    return "Tourne à gauche"

@app.route('/right')
def right():
    pca.channels[STEERING_CHANNEL].duty_cycle = RIGHT
    return "Tourne à droite"

@app.route('/stop')
def handle_stop():
    stop()
    return "Stop"

# --- Mouvements combinés ---
@app.route('/forward_left')
def forward_left():
    threading.Thread(target=timed_drive_with_steering, args=(FORWARD_10, LEFT)).start()
    return "Avance en tournant à gauche"

@app.route('/backward_right')
def backward_right():
    threading.Thread(target=timed_drive_with_steering, args=(BACKWARD_10, RIGHT)).start()
    return "Recule en tournant à droite"

@app.route('/forward_right')
def forward_right():
    threading.Thread(target=timed_drive_with_steering, args=(FORWARD_10, RIGHT)).start()
    return "Avance en tournant à droite"


if __name__ == '__main__':
    try:
        stop()
        app.run(host='0.0.0.0', port=5000)
    finally:
        stop()
