import time
import json

import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge

device_state = {}
device_config = []

with open("last-state.json","r") as ls:
    file_data = ls.read()
    device_state = json.loads(file_data)

def on_broadcast(client, userdata, message):
    # print("Received n")
    # print(device_state)
    
    topic = message.topic
    device = topic.split("/")[1]
    if not device in device_state:
        print(f"New device found with ID:{device}")
        device_state[device] = dict(sensors={}, name=device)
    new_sensor_states = json.loads(message.payload.decode())
    #print(f"Update for {device}:{new_sensor_states}")
    for sensor in list(new_sensor_states.keys()):
        device_state[device]["sensors"][sensor] = new_sensor_states[sensor]
        #print(sensor)
    print(f"New state:{device_state}")
    

MQTT_SERVER_HOST = "localhost"


if __name__ == "__main__":
    mqtt_client = mqtt.Client()

    mqtt_client.on_message = on_broadcast

    mqtt_client.connect(MQTT_SERVER_HOST, port=1884)
    mqtt_client.loop_start()

    mqtt_client.subscribe("zigbee2mqtt/+")
    #    time.sleep(60)

    with open("device-config.json", "r") as df:
        device_config = json.loads(df.read())
    #print(device_config)
    for device in device_config:
        if not device["device_id"] in device_state:
            device_state[device["device_id"]] = {
                "name": device["name"],
                "sensors": {_sensor: 0.0 for _sensor in device["sensors"]},
            }
        
        for sensor in device["sensors"]:
            _gauge = Gauge(
                f"{device['name']}_{sensor}",
                f"Sensor belonging to {device['name']} ({device['device_id']})",
            )
            _gauge.set_function(
                lambda device=device, sensor=sensor: device_state[device["device_id"]]["sensors"][sensor]
            )
    start_http_server(11111)
    while True:
        with open("last-state.json", "r") as ls:
            last_state = json.loads(ls.read())
        
        if last_state != device_state:
            with open("last-state.json", "w") as ls:
                ls.write(json.dumps(device_state))
        time.sleep(1)
