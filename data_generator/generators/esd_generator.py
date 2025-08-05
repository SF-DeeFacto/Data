import time
import random
import mysql.connector
from datetime import datetime
from config.sensor_config import ESD_SENSORS
from config.db_config import DB_CONFIG

def run_esd_simulation():
    NORMAL_ESD = 50
    NORMAL_RANGE = 30
    MIN_ESD = 0
    MAX_ESD = 100
    DELTA = 5
    OUT_PROB = 0.001
    SENSOR_NOISE = 5

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sensor_states = {
        sensor.sensor_id: {
            "zone_id": sensor.zone_id,
            "esd": NORMAL_ESD + random.randint(-NORMAL_RANGE, NORMAL_RANGE),
            "state": "NORMAL",
            "spike_step": 0,
            "spike_duration": 10,
            "spike_start": NORMAL_ESD,
            "spike_target": NORMAL_ESD
        }
        for sensor in ESD_SENSORS
    }

    data_buffer = []

    try:
        while True:
            now = datetime.utcnow()

            for state in sensor_states.values():
                if state["state"] == "NORMAL":
                    if random.random() < OUT_PROB:
                        state["spike_target"] = MAX_ESD + random.randint(0, 20)
                        state["spike_start"] = state["esd"]
                        state["spike_step"] = 0
                        state["state"] = "SPIKING"
                    else:
                        delta = random.randint(-25, 25)
                        toward = random.random() < 0.3
                        if toward:
                            delta = abs(delta) if state["esd"] < NORMAL_ESD else -abs(delta)
                        state["esd"] += delta
                        state["esd"] = max(min(state["esd"], NORMAL_ESD + NORMAL_RANGE), MIN_ESD)

                elif state["state"] == "SPIKING":
                    state["spike_step"] += 1
                    if state["spike_step"] >= state["spike_duration"]:
                        state["esd"] = state["spike_target"]
                        state["state"] = "OUT_OF_RANGE"

                elif state["state"] == "OUT_OF_RANGE":
                    toward = random.random() < 0.98
                    if toward:
                        delta = random.randint(-100, 5)
                    else:
                        delta = -random.randint(-5, 10)
                    state["esd"] += delta
                    if MIN_ESD <= state["esd"] <= MAX_ESD:
                        state["state"] = "NORMAL"

            for sensor in ESD_SENSORS:
                state = sensor_states[sensor.sensor_id]
                noisy = state["esd"] + random.randint(-SENSOR_NOISE, SENSOR_NOISE)
                if noisy < MIN_ESD:
                    noisy = MIN_ESD
                elif state["state"] == "NORMAL" and noisy >= MAX_ESD:
                    noisy = NORMAL_ESD + NORMAL_RANGE

                data_buffer.append((
                    now, "esd", sensor.sensor_id, state["zone_id"], "V", noisy
                ))

            if len(data_buffer) >= len(ESD_SENSORS) * 5:
                cursor.executemany("""
                    INSERT INTO esd_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"[{now}] ESD 데이터 {len(data_buffer)}개 삽입 완료")
                data_buffer.clear()

            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 ESD 시뮬레이터 종료됨.")
    finally:
        cursor.close()
        conn.close()
