from kasa import Discover
import asyncio
import json
from datetime import datetime, UTC

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# Smart plug settings
IP = "YOUR_SMART_PLUG_IP"
USERNAME = "YOUR_TAPO_EMAIL"
PASSWORD = "YOUR_TAPO_PASSWORD"


# InfluxDB settings
INFLUX_URL = "http://localhost:8086"
TOKEN = "YOUR_INFLUXDB_TOKEN"
ORG = "pi_project"
BUCKET = "sensor_data"


# MQTT settings
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "smartplug/p110"


async def connect_mqtt():
    while True:
        try:
            client = mqtt.Client()
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print("MQTT connected")
            return client
        except Exception as e:
            print("MQTT connect error:", e)
            await asyncio.sleep(5)


async def connect_device():
    while True:
        try:
            device = await Discover.discover_single(
                IP,
                username=USERNAME,
                password=PASSWORD,
            )
            print("Smart Plug connected")
            return device
        except Exception as e:
            print("Smart Plug connect error:", e)
            await asyncio.sleep(5)


async def main():
    mqtt_client = await connect_mqtt()
    device = await connect_device()

    influx_client = InfluxDBClient(
        url=INFLUX_URL,
        token=TOKEN,
        org=ORG
    )
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    while True:
        try:
            await device.update()

            energy = device.modules["Energy"]
            power = energy.current_consumption
            voltage = energy.voltage
            current = energy.current

            print(f"Power: {power} W")
            print(f"Voltage: {voltage} V")
            print(f"Current: {current} A")

            payload = {
                "device_ip": IP,
                "power": float(power),
                "voltage": float(voltage),
                "current": float(current),
                "timestamp": datetime.now(UTC).isoformat(),
            }

            try:
                mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
            except Exception as e:
                print("MQTT publish error:", e)
                mqtt_client = await connect_mqtt()

            point = (
                Point("power_data")
                .field("power", float(power))
                .field("voltage", float(voltage))
                .field("current", float(current))
                .time(datetime.now(UTC), WritePrecision.NS)
            )

            try:
                write_api.write(bucket=BUCKET, org=ORG, record=point)
                print("InfluxDB write success")
            except Exception as e:
                print("InfluxDB error:", e)

        except Exception as e:
            print("Loop error:", e)
            await asyncio.sleep(5)

        await asyncio.sleep(5)


asyncio.run(main())