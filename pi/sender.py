#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import requests
from influxdb import InfluxDBClient
import math
import numpy as np
import http.server
import socketserver
import threading
from urllib.parse import parse_qs, urlparse

PORT=8000

GPIO_RELAY_PIN = 4
GPIO_DHT_PIN = 17
SOIL_SENSOR_URL = 'http://soilsensor.local/sensor/soil1'

DISPENSED_ML = 0

def dispense_milliliters(ml):
    global DISPENSED_ML
    # Constants
    ML_PER_SECOND = 100 / 60  # 100ml per 60 seconds
    # Calculate the duration in seconds for the given milliliters
    duration_seconds = ml / ML_PER_SECOND

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_RELAY_PIN, GPIO.OUT)

    # Turn on the relay
    GPIO.output(GPIO_RELAY_PIN, GPIO.HIGH)
    print(f"Dispensing for {duration_seconds} seconds.")

    # Wait for the duration required to dispense the given milliliters
    time.sleep(duration_seconds)

    # Turn off the relay
    GPIO.output(GPIO_RELAY_PIN, GPIO.LOW)
    print("Dispensing complete.")

    # Cleanup GPIO
    GPIO.cleanup()
    DISPENSED_ML += ml
    write_metric('growbox_dispensed', DISPENSED_ML)

def read_temp_rh():
    # Set sensor type : DHT11
    sensor = Adafruit_DHT.DHT11

    humidity, temperature = Adafruit_DHT.read_retry(sensor, GPIO_DHT_PIN)
    if humidity is not None and temperature is not None:
        print(f"Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%")
        return (temperature, humidity)
    else:
        print("Failed to retrieve data from humidity sensor")
        return None


def get_soil_sensor_data():
    try:
        # Sending a GET request to the endpoint
        response = requests.get(SOIL_SENSOR_URL)
        # Checking if the response was successful
        if response.status_code == 200:
            # Parsing the JSON data
            data = response.json()
            return data["value"]
        else:
            return f"Failed to retrieve data, status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        # Handling exceptions that may occur during the request
        return str(e)

def write_metric(measurement, value, name='grow1', db_name='influxdb', host='10.8.0.1', port=8086):
    # Create an instance of the InfluxDB client
    client = InfluxDBClient(host=host, port=port)
    # Connect to the specified database
    client.switch_database(db_name)
    # Define the data point to write
    json_body = [
        {
            "measurement": measurement,
            "tags": {
                "host": name,
            },
            "fields": {
                "value": value
            }
        }
    ]
    # Write the data point to the database
    client.write_points(json_body)
    # Close the client
    client.close()

def calculate_vpd(temp_celsius, rh_fraction):
    # Calculate the saturation vapor pressure (SVP) using the Magnus formula
    svp = 0.6108 * np.exp((17.27 * temp_celsius) / (temp_celsius + 237.3))
    # Calculate the actual vapor pressure (AVP)
    avp = rh_fraction * svp
    # Calculate the vapor pressure deficit (VPD)
    vpd = svp - avp
    return vpd


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith('/dispense'):
            # Extract query parameters
            query_components = parse_qs(urlparse(self.path).query)
            amount = query_components.get('amount', [50])[0]  # Default to 15 if not specified
            dispense_milliliters(int(amount))
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Dispensed!")
        else:
            # Serve the button page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = f'''
            <html>
            <head><title>Dispenser</title></head>
            <body>
                <form action="/dispense?amount=50" method="get">
                    <button type="submit" style="width:200px; height:100px; font-size:20px;">Dispense 50 mL</button>
                </form>
            </body>
            </html>
            '''
            self.wfile.write(html_content.encode('utf-8'))


def start_server():
    with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

# Start the server in a separate thread
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

while True:
  print("reading data")
  try:
    temp_rh = read_temp_rh()
    if temp_rh is not None:
      write_metric('growbox_temperature', temp_rh[0])
      write_metric('growbox_rh', temp_rh[1])
      write_metric('growbox_vpd', calculate_vpd(temp_rh[0], temp_rh[1]/100))
    write_metric('growbox_soil_moisture', get_soil_sensor_data())
    time.sleep(30)
  except Exception as e:
    print(f"Errored {e}")

# Example usage: dispense 50 milliliters
#dispense_milliliters(50)
