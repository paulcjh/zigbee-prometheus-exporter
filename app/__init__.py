import os
import time
import json
import serial

from watchgod import run_process, RegExpWatcher, AllWatcher

import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge

device_state = {}
device_config = []
MQTT_SERVER_HOST = os.getenv("MQTT_SERVER_HOST")
serial_channel = serial.Serial("/dev/ttyUSB1", 115200, timeout=1)
serial_channel.reset_input_buffer()
with open("/state/last-state.json", "r") as ls:
    file_data = ls.read()
    device_state = json.loads(file_data)


def on_broadcast(client, userdata, message):
    topic = message.topic
    device = topic.split("/")[1]
    if device not in device_state:
        print(f"New device found with ID:{device}", flush=True)
        device_state[device] = dict(sensors={}, name=device)
    new_sensor_states = json.loads(message.payload.decode())

    for sensor in list(new_sensor_states.keys()):
        device_state[device]["sensors"][sensor] = new_sensor_states[sensor]

    print(f"New device state ({device}): {new_sensor_states}", flush=True)


def start():
    print("Starting zigbee prometheus exporter", flush=True)
    mqtt_client = mqtt.Client()

    mqtt_client.on_message = on_broadcast

    mqtt_client.connect(MQTT_SERVER_HOST, port=1884)
    mqtt_client.loop_start()

    mqtt_client.subscribe("zigbee2mqtt/+")

    with open("device-config.json", "r") as df:
        device_config = json.loads(df.read())
    for device in device_config:
        if not device["device_id"] in device_state:
            device_state[device["device_id"]] = {
                "name": device["name"],
                "sensors": {_sensor: 0.0 for _sensor in device["sensors"]},
            }
        else:
            device_state[device["device_id"]]["name"] = device["name"]

        for sensor in device["sensors"]:
            _gauge = Gauge(
                f"{device['name']}_{sensor}",
                f"Sensor belonging to {device['name']} ({device['device_id']})",
            )
            _gauge.set_function(
                lambda device=device, sensor=sensor: device_state[device["device_id"]][
                    "sensors"
                ][sensor]
            )
    def get_current():
        serial_channel.writelines([b"getSolarCurrent"])
        while not serial_channel.in_waiting:
            time.sleep(0.01)
        response = serial_channel.readline()
        print(f"Solar charge output={response}", flush=True)
        response = response.decode().rstrip()
        device_state["solar_charging_current"]["sensors"]["current"] = float(response.split("=")[1])
    #_gauge = Gauge("solar_charging_current", "Solar charging current")
    #_gauge.set_function(get_current)
    start_http_server(11111)
    while True:
        #get_current()
        with open("/state/last-state.json", "r") as ls:
            last_state = json.loads(ls.read())

        if last_state != device_state:
            with open("/state/last-state.json", "w") as ls:
                ls.write(json.dumps(device_state))
        time.sleep(1)


if __name__ == "__main__":
    print("Starting!", flush=True)
    run_process(
        "/core/",
        start,
        watcher_cls=AllWatcher,
    )
