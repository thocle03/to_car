from flask import Flask
import board
import busio
import time
from adafruit_pca9685 import PCA9685
import threading

app = Flask(__name__)

# --- Constantes PWM ---
def pwm12_to_16(val):
    return int(val * 65535 / 4096)

NEUTRAL = pwm12_to_16(307)
FULL_FORWARD = pwm12_to_16(410)
FULL_BACKWARD = pwm12_to_16(205)
LEFT = pwm12_to_16(520)
RIGHT = pwm12_to_16(105)

# 50% vitesse = entre NEUTRAL et FULL
FORWARD_50 = int((NEUTRAL + FULL_FORWARD) / 10)
BACKWARD_50 = int((NEUTRAL + FULL_BACKWARD) / 5)

# --- Init PCA9685 ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

THROTTLE_CHANNEL = 0
STEERING_CHANNEL = 1

def stop():
    pca.channels[THROTTLE_CHANNEL].duty_cycle = NEUTRAL
    pca.channels[STEERING_CHANNEL].duty_cycle = NEUTRAL

def timed_drive(throttle_value, duration=3):
    stop()
    pca.channels[THROTTLE_CHANNEL].duty_cycle = throttle_value
    pca.channels[STEERING_CHANNEL].duty_cycle = NEUTRAL
    time.sleep(duration)
    stop()

@app.route('/forward')
def forward():
    threading.Thread(target=timed_drive, args=(FORWARD_50,)).start()
    return "Avance pendant 3 secondes à 50%"

@app.route('/backward')
def backward():
    threading.Thread(target=timed_drive, args=(BACKWARD_50,)).start()
    return "Recule pendant 3 secondes à 50%"

@app.route('/left')
def left():
    pca.channels[STEERING_CHANNEL].duty_cycle = LEFT
    return "Direction gauche"

@app.route('/right')
def right():
    pca.channels[STEERING_CHANNEL].duty_cycle = RIGHT
    return "Direction droite"

@app.route('/stop')
def handle_stop():
    stop()
    return "Stop"

if __name__ == '__main__':
    try:
        stop()
        app.run(host='0.0.0.0', port=5000)
    finally:
        stop()
