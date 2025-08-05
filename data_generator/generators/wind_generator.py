import time
import random
import mysql.connector
from datetime import datetime
from config.sensor_config import WIND_SENSORS
from config.db_config import DB_CONFIG

def run_wind_simulation():
    # 풍향 시뮬레이션 파라미터
    NORMAL_WD = 0
    NORMAL_RANGE = 14
    OUT_RANGE = 20
    MIN_WD = NORMAL_WD - NORMAL_RANGE
    MAX_WD = NORMAL_WD + NORMAL_RANGE
    OUT_MIN = NORMAL_WD - OUT_RANGE
    OUT_MAX = NORMAL_WD + OUT_RANGE
    DELTA = 1
    OUT_PROB = 0.001
    SENSOR_NOISE = 1


    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sensor_states = {
        sensor.sensor_id: {
            "zone_id": sensor.zone_id,
            "windDir": NORMAL_WD + random.randint(-NORMAL_RANGE, NORMAL_RANGE),
            "state": "NORMAL",
            "spike_step": 0,
            "spike_duration": 10,
            "spike_start": NORMAL_WD,
            "spike_target": NORMAL_WD,
            "hold_step": 0,
            "hold_duration": 25
        }
        for sensor in WIND_SENSORS
    }

    data_buffer = []

    try:
        while True:
            now = datetime.utcnow()

            for state in sensor_states.values():
                if state["state"] == "NORMAL":
                    if random.random() < OUT_PROB:
                        if random.random() < 0.5:
                            state["spike_target"] = OUT_MIN + random.randint(0, MIN_WD - OUT_MIN)
                        else:
                            state["spike_target"] = MAX_WD + random.randint(0, OUT_MAX - MAX_WD)
                        state["spike_start"] = state["windDir"]
                        state["spike_step"] = 0
                        state["state"] = "SPIKING"
                    else:
                        delta = random.randint(-3, 3)
                        toward = random.random() < 0.8
                        if toward:
                            delta = abs(delta) if state["windDir"] < NORMAL_WD else -abs(delta)
                        state["windDir"] += delta
                        state["windDir"] = max(min(state["windDir"], MAX_WD), MIN_WD)

                elif state["state"] == "SPIKING":
                    state["spike_step"] += 1
                    t = state["spike_step"] / state["spike_duration"]
                    factor = 1 - pow(2.71828, -3 * t)
                    norm = 1 - pow(2.71828, -3)
                    interpolated = state["spike_start"] + (state["spike_target"] - state["spike_start"]) * (factor / norm)
                    state["windDir"] = int(interpolated)
                    if state["spike_step"] >= state["spike_duration"]:
                        state["state"] = "HOLDING"
                        state["hold_step"] = 0

                elif state["state"] == "HOLDING":
                    state["hold_step"] += 1
                    state["windDir"] = state["spike_target"]
                    if state["hold_step"] >= state["hold_duration"]:
                        state["state"] = "OUT_OF_RANGE"

                elif state["state"] == "OUT_OF_RANGE":
                    toward = random.random() < 0.8
                    step = 1 if toward else -1
                    if state["windDir"] < NORMAL_WD:
                        state["windDir"] += step
                    else:
                        state["windDir"] -= step
                    if MIN_WD <= state["windDir"] <= MAX_WD:
                        state["state"] = "NORMAL"

            for sensor in WIND_SENSORS:
                state = sensor_states[sensor.sensor_id]
                noisy = state["windDir"] + random.randint(-SENSOR_NOISE, SENSOR_NOISE)
                data_buffer.append((
                    now, "windDir", sensor.sensor_id, state["zone_id"], "deg", noisy
                ))

            if len(data_buffer) >= len(WIND_SENSORS) * 5:
                cursor.executemany("""
                    INSERT INTO wind_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"[{now}] WIND 데이터 {len(data_buffer)}개 삽입 완료")
                data_buffer.clear()

            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 WIND 시뮬레이터 종료됨.")
    finally:
        cursor.close()
        conn.close()
