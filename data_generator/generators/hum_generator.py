import time
import random
import mysql.connector
from datetime import datetime
from config.sensor_config import HUM_SENSORS
from config.db_config import DB_CONFIG

def run_humidity_simulation():
    NORMAL_HUM = 45.0
    NORMAL_RANGE = 5.0
    OUT_RANGE = 7.0
    MIN_HUM = NORMAL_HUM - NORMAL_RANGE
    MAX_HUM = NORMAL_HUM + NORMAL_RANGE
    OUT_MIN = NORMAL_HUM - OUT_RANGE
    OUT_MAX = NORMAL_HUM + OUT_RANGE
    DELTA = 0.5
    OUT_PROB = 0.001
    SENSOR_NOISE = 0.25

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    zone_states = {
        sensor.zone_id: {
            "hum": NORMAL_HUM + (random.random() * 2 - 1) * NORMAL_RANGE,
            "state": "NORMAL",
            "spike_step": 0,
            "spike_duration": 10,
            "spike_start_hum": NORMAL_HUM,
            "spike_target_hum": NORMAL_HUM,
            "hold_step": 0,
            "hold_duration": 25
        }
        for sensor in HUM_SENSORS
    }

    data_buffer = []

    try:
        while True:
            now = datetime.utcnow()

            for state in zone_states.values():
                if state["state"] == "NORMAL":
                    if random.random() < OUT_PROB:
                        if random.random() < 0.5:
                            state["spike_target_hum"] = OUT_MIN + random.random() * (MIN_HUM - OUT_MIN)
                        else:
                            state["spike_target_hum"] = MAX_HUM + random.random() * (OUT_MAX - MAX_HUM)
                        state["spike_start_hum"] = state["hum"]
                        state["spike_step"] = 0
                        state["state"] = "SPIKING"
                    else:
                        delta = (random.random() * 2 - 1) * DELTA
                        toward = random.random() < 0.3
                        if toward:
                            delta = abs(delta) if state["hum"] < NORMAL_HUM else -abs(delta)
                        state["hum"] += delta
                        state["hum"] = max(min(state["hum"], MAX_HUM), MIN_HUM)

                elif state["state"] == "SPIKING":
                    state["spike_step"] += 1
                    t = state["spike_step"] / state["spike_duration"]
                    factor = 1 - pow(2.71828, -3 * t)
                    norm = 1 - pow(2.71828, -3)
                    state["hum"] = state["spike_start_hum"] + (state["spike_target_hum"] - state["spike_start_hum"]) * (factor / norm)
                    if state["spike_step"] >= state["spike_duration"]:
                        state["state"] = "HOLDING"
                        state["hold_step"] = 0

                elif state["state"] == "HOLDING":
                    state["hold_step"] += 1
                    state["hum"] = state["spike_target_hum"]
                    if state["hold_step"] >= state["hold_duration"]:
                        state["state"] = "OUT_OF_RANGE"

                elif state["state"] == "OUT_OF_RANGE":
                    toward = random.random() < 0.8
                    step = 0.05 + random.random() * 0.005
                    if state["hum"] < NORMAL_HUM:
                        state["hum"] += step if toward else -step
                    else:
                        state["hum"] -= step if toward else -step
                    if MIN_HUM <= state["hum"] <= MAX_HUM:
                        state["state"] = "NORMAL"

            for sensor in HUM_SENSORS:
                zone_hum = zone_states[sensor.zone_id]["hum"]
                noisy_hum = zone_hum + (random.random() * 2 - 1) * SENSOR_NOISE
                rounded_hum = round(noisy_hum / 0.25) * 0.25

                data_buffer.append((
                    now, "humidity", sensor.sensor_id, sensor.zone_id, "%RH", rounded_hum
                ))

            if len(data_buffer) >= len(HUM_SENSORS) * 5:
                cursor.executemany("""
                    INSERT INTO hum_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"[{now}] ▶ HUMIDITY 데이터 {len(data_buffer)}개 삽입 완료")
                data_buffer.clear()

            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 HUMIDITY 시뮬레이터 종료됨.")
    finally:
        cursor.close()
        conn.close()
