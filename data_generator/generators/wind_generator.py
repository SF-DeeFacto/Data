import time
import random
import mysql.connector
from datetime import datetime
from config.sensor_config import WIND_SENSORS
from config.db_config import DB_CONFIG
from opensearchpy import helpers
from config.opensearch_config import get_os_client, ensure_index_for_type, get_index_for_type, to_iso_z

def run_wind_simulation():
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

    os_client = get_os_client()
    sensor_type = "windDir"
    index_name = ensure_index_for_type(os_client, sensor_type)

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
    os_actions = []

    try:
        while True:
            now = datetime.utcnow()
            ts_iso = to_iso_z(now)

            for state in sensor_states.values():
                if state["state"] == "NORMAL":
                    if random.random() < OUT_PROB:
                        if random.random() < 0.5:
                            state["spike_target"] = OUT_MIN + random.randint(0, MAX(0, MIN_WD - OUT_MIN))
                        else:
                            state["spike_target"] = MAX_WD + random.randint(0, MAX(0, OUT_MAX - MAX_WD))
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

            # 생성 → 두 버퍼에 저장
            for sensor in WIND_SENSORS:
                state = sensor_states[sensor.sensor_id]
                noisy = state["windDir"] + random.randint(-SENSOR_NOISE, SENSOR_NOISE)

                # MySQL
                data_buffer.append((now, "windDir", sensor.sensor_id, state["zone_id"], "deg", noisy))

                # OpenSearch
                os_actions.append({
                    "_index": index_name,
                    "_source": {
                        "sensor_id": str(sensor.sensor_id),
                        "zone_id": str(state["zone_id"]),
                        "timestamp": ts_iso,
                        "sensor_type": sensor_type,
                        "unit": "deg",
                        "val": int(noisy),
                    }
                })

            # 5초마다 flush (둘 다)
            if len(data_buffer) >= len(WIND_SENSORS) * 5:
                # MySQL
                cursor.executemany("""
                    INSERT INTO wind_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"[{now}] MySQL WIND inserted {len(data_buffer)} rows")
                data_buffer.clear()

                # OpenSearch
                try:
                    helpers.bulk(os_client, os_actions, raise_on_error=False)
                    print(f"[{now}] OpenSearch WIND indexed {len(os_actions)} docs")
                except Exception as e:
                    print(f"[OS] bulk error: {e}")
                finally:
                    os_actions.clear()

            time.sleep(1)

    except KeyboardInterrupt:
        print("WIND 시뮬레이터 종료됨.")
    finally:
        if data_buffer:
            try:
                cursor.executemany("""
                    INSERT INTO wind_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"Final MySQL WIND flush: {len(data_buffer)} rows")
            except Exception as e:
                conn.rollback()
                print(f"Final MySQL WIND error: {e}")

        if os_actions:
            try:
                helpers.bulk(os_client, os_actions, raise_on_error=False)
                print(f"Final OpenSearch WIND flush: {len(os_actions)} docs")
            except Exception as e:
                print(f"Final OS WIND error: {e}")

        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_wind_simulation()
