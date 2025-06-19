from flask import Flask
import board
import busio
from adafruit_pca9685 import PCA9685

app = Flask(__name__)

# --- Constantes PWM ---
def pwm12_to_16(val):
    return int(val * 65535 / 4096)

NEUTRAL = pwm12_to_16(307)
FORWARD = pwm12_to_16(410)
BACKWARD = pwm12_to_16(205)
LEFT = pwm12_to_16(520)
RIGHT = pwm12_to_16(105)

# --- Init PCA9685 ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

THROTTLE_CHANNEL = 0
STEERING_CHANNEL = 1

def stop():
    pca.channels[THROTTLE_CHANNEL].duty_cycle = NEUTRAL
    pca.channels[STEERING_CHANNEL].duty_cycle = NEUTRAL

@app.route('/forward')
def forward():
    pca.channels[THROTTLE_CHANNEL].duty_cycle = FORWARD
    return "Avance"

@app.route('/backward')
def backward():
    pca.channels[THROTTLE_CHANNEL].duty_cycle = BACKWARD
    return "Recule"

@app.route('/left')
def left():
    pca.channels[STEERING_CHANNEL].duty_cycle = LEFT
    return "Gauche"

@app.route('/right')
def right():
    pca.channels[STEERING_CHANNEL].duty_cycle = RIGHT
    return "Droite"

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
