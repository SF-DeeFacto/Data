import time
import random
import mysql.connector
from datetime import datetime
from config.sensor_config import TEMP_SENSORS
from config.db_config import DB_CONFIG

def run_temp_simulation():
    # 온도 시뮬레이션 파라미터
    NORMAL_TEMP = 21.0
    NORMAL_RANGE = 1.0
    OUT_RANGE = 3.0
    MIN_TEMP = NORMAL_TEMP - NORMAL_RANGE
    MAX_TEMP = NORMAL_TEMP + NORMAL_RANGE
    OUT_MIN = NORMAL_TEMP - OUT_RANGE
    OUT_MAX = NORMAL_TEMP + OUT_RANGE
    DELTA = 0.1
    OUT_PROB = 0.01
    SENSOR_NOISE = 0.25

    # DB 연결
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # zone 상태 초기화
    zone_states = {
        sensor.zone_id: {
            "temp": NORMAL_TEMP + (random.random() * 2 - 1) * NORMAL_RANGE,
            "state": "NORMAL",
            "spike_step": 0,
            "spike_duration": 10,
            "spike_start_temp": NORMAL_TEMP,
            "spike_target_temp": NORMAL_TEMP,
            "hold_step": 0,
            "hold_duration": 25
        }
        for sensor in TEMP_SENSORS
    }

    data_buffer = []

    try:
        while True:
            now = datetime.utcnow()

            # zone별 상태 업데이트
            for state in zone_states.values():
                if state["state"] == "NORMAL":
                    if random.random() < OUT_PROB:
                        if random.random() < 0.5:
                            state["spike_target_temp"] = OUT_MIN + random.random() * (MIN_TEMP - OUT_MIN)
                        else:
                            state["spike_target_temp"] = MAX_TEMP + random.random() * (OUT_MAX - MAX_TEMP)
                        state["spike_start_temp"] = state["temp"]
                        state["spike_step"] = 0
                        state["state"] = "SPIKING"
                    else:
                        delta = (random.random() * 2 - 1) * DELTA
                        toward = random.random() < 0.3
                        if toward:
                            delta = abs(delta) if state["temp"] < NORMAL_TEMP else -abs(delta)
                        state["temp"] += delta
                        state["temp"] = max(min(state["temp"], MAX_TEMP), MIN_TEMP)

                elif state["state"] == "SPIKING":
                    state["spike_step"] += 1
                    t = state["spike_step"] / state["spike_duration"]
                    factor = 1 - pow(2.71828, -3 * t)
                    norm = 1 - pow(2.71828, -3)
                    state["temp"] = state["spike_start_temp"] + (state["spike_target_temp"] - state["spike_start_temp"]) * (factor / norm)
                    if state["spike_step"] >= state["spike_duration"]:
                        state["state"] = "HOLDING"
                        state["hold_step"] = 0

                elif state["state"] == "HOLDING":
                    state["hold_step"] += 1
                    state["temp"] = state["spike_target_temp"]
                    if state["hold_step"] >= state["hold_duration"]:
                        state["state"] = "OUT_OF_RANGE"

                elif state["state"] == "OUT_OF_RANGE":
                    toward = random.random() < 0.8
                    step = 0.05 + random.random() * 0.05
                    if state["temp"] < NORMAL_TEMP:
                        state["temp"] += step if toward else -step
                    else:
                        state["temp"] -= step if toward else -step
                    if MIN_TEMP <= state["temp"] <= MAX_TEMP:
                        state["state"] = "NORMAL"

            # 센서별 데이터 생성 → 버퍼에 저장
            for sensor in TEMP_SENSORS:
                zone_temp = zone_states[sensor.zone_id]["temp"]
                noisy_temp = zone_temp + (random.random() * 2 - 1) * SENSOR_NOISE
                rounded_temp = round(noisy_temp / 0.25) * 0.25

                data_buffer.append((
                    now, "temp", sensor.sensor_id, sensor.zone_id, "°C", rounded_temp
                ))

            # 5초마다 insert
            if len(data_buffer) >= len(TEMP_SENSORS) * 5:
                cursor.executemany("""
                    INSERT INTO temp_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"[{now}] TEMP 센서 데이터 {len(data_buffer)}개 삽입 완료")
                data_buffer.clear()

            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 TEMP 시뮬레이터 종료됨.")
    finally:
        cursor.close()
        conn.close()
