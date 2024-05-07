# plantcontroller

all components are optional, just comment out the configurations you don't need.

I just use a WAGO clamp to make sort of "bus bars" for 3V3 and GND pins.

To set up and run the controller
* create secrets.yaml based on [secrets_empty.yaml](../secrets_empty.yaml)
* install esphome if necessary, or use esphome webapp to build+flash the firmware

## Monitoring with Grafana Cloud

* Set up a free-tier Grafana Cloud account
* Add the [dashboard](dashboard.json)
* Create an API key
* Set the API key and URL (monitoring_target) in the secrets.yaml
  * API key will be something like "Bearer youruseridinteger:somebase64"
  * target will be something like `https://influxdb<...>/api/v1/push/influx/write`. Add the influx write suffix if needed.
* Deploy and check that the lambda works (should report status 200. If HTTP code is 400, check the payload and sensors. If a sensor reports invalid values, it may cause monitoring to not work. Remove unused metrics from the request body.)

## PWM light control

Honestly just a simple circuit based on what i had laying around, but a useful circuit nonetheless.

I use a BC337 NPN transistor as a gate driver and an IRF540NPBF MOSFET to actually drive the lights.

ESP8266 GPIO <-> 1kOhm resistor <-> BC337 base
ESP8266 GND <-> BC337 emitter
BC337 collector <-> MOSFET gate
power supply VCC <-> 10kOhm resistor <-> MOSFET gate
MOSFET drain <-> LED array GND
MOSFET source <-> power supply GND

This way the BC337 can pull the gate down, the 10kOhm resistor will pull the gate up by default.
This is why we invert the PWM signal in the controller by default.
The power supply + obviously must not exceed the Vgs of the MOSFET in this case.

If you have a logic level MOSFET that can fully turn on using just the GPIO voltage, you can just connect the gate (probably best through a 1kOhm resistor to reduce current) directly to GPIO.

## soil sensor

just hook it up to 3V3 for VCC, A0 for readout, GND.

## VPD sensor

use the related [printables](../../printables/vpdsensor) for case+holder.

for the sensors themselves, i just hook up the I2C and VCC in parallel, then send a single set of I2C wires down to the ESP.

