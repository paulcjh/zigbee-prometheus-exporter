import os
import time
import json

import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge

device_state = {}
device_config = []
MQTT_SERVER_HOST = os.getenv("MQTT_SERVER_HOST")


with open("config/last-state.json", "r") as ls:
    file_data = ls.read()
    device_state = json.loads(file_data)


def on_broadcast(client, userdata, message):
    topic = message.topic
    device = topic.split("/")[1]
    if device not in device_state:
        print(f"New device found with ID:{device}")
        device_state[device] = dict(sensors={}, name=device)
    new_sensor_states = json.loads(message.payload.decode())

    for sensor in list(new_sensor_states.keys()):
        device_state[device]["sensors"][sensor] = new_sensor_states[sensor]

    print(f"New device state ({device}): {new_sensor_states}")


def start():
    print("Starting zigbee prometheus exporter")
    mqtt_client = mqtt.Client()

    mqtt_client.on_message = on_broadcast

    mqtt_client.connect(MQTT_SERVER_HOST, port=1884)
    mqtt_client.loop_start()

    mqtt_client.subscribe("zigbee2mqtt/+")

    with open("config/device-config.json", "r") as df:
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
    start_http_server(11111)
    while True:
        with open("config/last-state.json", "r") as ls:
            last_state = json.loads(ls.read())

        if last_state != device_state:
            with open("config/last-state.json", "w") as ls:
                ls.write(json.dumps(device_state))
        time.sleep(1)
