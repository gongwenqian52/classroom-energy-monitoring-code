import serial
import time
import re
from datetime import datetime, UTC

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# InfluxDB settings
INFLUX_URL = "http://localhost:8086"
TOKEN = "YOUR_INFLUXDB_TOKEN"
ORG = "pi_project"
BUCKET = "sensor_data"


# Serial settings
SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200


# Time settings
WRITE_INTERVAL = 2
NO_DATA_TIMEOUT = 10


# Initial state
occupancy = 0
distance = 0
last_write_time = 0
last_data_time = time.time()
buffer = ""
is_cleaned_up = False


client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


def write_point(current_occupancy, current_distance):
    point = (
        Point("radar_data")
        .field("occupancy", int(current_occupancy))
        .field("range", int(current_distance))
        .time(datetime.now(UTC), WritePrecision.NS)
    )

    try:
        write_api.write(bucket=BUCKET, org=ORG, record=point)
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            f"occupancy={current_occupancy}, range={current_distance}, "
            f"InfluxDB write success"
        )
    except Exception as e:
        print("InfluxDB error:", e)


def write_off_state():
    point = (
        Point("radar_data")
        .field("occupancy", 0)
        .field("range", 0)
        .time(datetime.now(UTC), WritePrecision.NS)
    )

    try:
        write_api.write(bucket=BUCKET, org=ORG, record=point)
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            f"occupancy=0, range=0, stop write success"
        )
    except Exception as e:
        print("InfluxDB stop write error:", e)


def cleanup():
    global is_cleaned_up

    if not is_cleaned_up:
        print("Stopping radar script...")
        write_off_state()
        is_cleaned_up = True

    try:
        client.close()
    except Exception:
        pass


try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Radar serial connected")

    while True:
        try:
            data = ser.read(ser.in_waiting or 1)

            if data:
                buffer += data.decode(errors="ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    if line == "ON":
                        occupancy = 1
                        last_data_time = time.time()

                    elif line == "OFF":
                        occupancy = 0
                        distance = 0
                        last_data_time = time.time()

                    else:
                        match = re.search(r"Range\s+(\d+)", line)

                        if match:
                            distance = int(match.group(1))
                            last_data_time = time.time()

            if time.time() - last_data_time > NO_DATA_TIMEOUT:
                occupancy = 0
                distance = 0

            if time.time() - last_write_time >= WRITE_INTERVAL:
                write_point(occupancy, distance)
                last_write_time = time.time()

            time.sleep(0.1)

        except Exception as e:
            print("Loop error:", e)
            time.sleep(1)

except KeyboardInterrupt:
    cleanup()

except Exception as e:
    print("Startup error:", e)
    cleanup()

finally:
    cleanup()