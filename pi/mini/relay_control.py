#!/usr/bin/env python3
"""
Control a relay on GPIO17 and read BMP388 sensor data.

Relay: ON (HIGH) between 06:00–22:00, OFF between 22:00–06:00.
Sensor: BMP388 on I2C (address 0x76), prints temp/pressure/altitude every 10 s.
Runs continuously with GPIO cleanup on stop.
"""

import RPi.GPIO as GPIO
import datetime
import signal
import sys
import time

# I2C / BMP388
try:
    import board
    import busio
    import adafruit_bmp388

    BMP388_AVAILABLE = True
except ImportError:
    BMP388_AVAILABLE = False

RELAY_PIN = 17
SENSOR_INTERVAL = 10  # seconds

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

bmp388 = None


def init_sensor():
    global bmp388
    if not BMP388_AVAILABLE:
        print("[bmp388] dependencies not installed, sensor disabled")
        return
    i2c = busio.I2C(board.SCL, board.SDA)
    bmp388 = adafruit_bmp388.BMP388_I2C(i2c, address=0x76)
    print("[bmp388] sensor initialized at 0x76")


def print_sensor():
    if not BMP388_AVAILABLE or bmp388 is None:
        return
    try:
        temp = bmp388.temperature
        pressure = bmp388.pressure
        altitude = bmp388.altitude
        print(
            f"[bmp388] temp={temp:.1f}°C  "
            f"pressure={pressure:.1f}hPa  "
            f"altitude={altitude:.1f}m"
        )
    except Exception as e:
        print(f"[bmp388] error: {e}")


def cleanup(signum=None, frame=None):
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)


signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

init_sensor()


def is_relay_on():
    now = datetime.datetime.now().time()
    return datetime.time(6, 0) <= now < datetime.time(22, 0)


last_sensor = 0

while True:
    GPIO.output(RELAY_PIN, GPIO.HIGH if is_relay_on() else GPIO.LOW)

    now = time.time()
    if now - last_sensor >= SENSOR_INTERVAL:
        print_sensor()
        last_sensor = now

    time.sleep(1)
