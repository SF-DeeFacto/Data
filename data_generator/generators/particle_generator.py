import time
import random
import mysql.connector
from datetime import datetime
from config.sensor_config import LPM_SENSORS
from config.db_config import DB_CONFIG

def run_particle_simulation():
    NORMAL_1 = 850
    NORMAL_3 = 82
    NORMAL_5 = 20
    RANGE_1 = 150
    RANGE_3 = 20
    RANGE_5 = 15
    MIN_1, MAX_1 = 0, NORMAL_1 + RANGE_1
    MIN_3, MAX_3 = 0, NORMAL_3 + RANGE_3
    MIN_5, MAX_5 = 0, NORMAL_5 + RANGE_5
    DELTA = 1
    OUT_PROB = 0.0008
    SENSOR_NOISE = 1

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sensor_states = {
        sensor.sensor_id: {
            "zone_id": sensor.zone_id,
            "p1": NORMAL_1 + random.randint(-RANGE_1, RANGE_1),
            "p3": NORMAL_3 + random.randint(-RANGE_3, RANGE_3),
            "p5": NORMAL_5 + random.randint(-RANGE_5, RANGE_5),
            "state": "NORMAL",
            "spike_step": 0,
            "spike_duration": 10,
            "spike_start": (NORMAL_1, NORMAL_3, NORMAL_5),
            "spike_target": (NORMAL_1, NORMAL_3, NORMAL_5),
            "hold_step": 0,
            "hold_duration": 25
        }
        for sensor in LPM_SENSORS
    }

    data_buffer = []

    try:
        while True:
            now = datetime.utcnow()

            for state in sensor_states.values():
                if state["state"] == "NORMAL":
                    if random.random() < OUT_PROB:
                        state["spike_target"] = (
                            MAX_1 + random.randint(0, 50),
                            MAX_3 + random.randint(0, 20),
                            MAX_5 + random.randint(0, 5)
                        )
                        state["spike_start"] = (state["p1"], state["p3"], state["p5"])
                        state["spike_step"] = 0
                        state["state"] = "SPIKING"
                    else:
                        toward = random.random() < 0.3
                        delta1 = random.randint(-40, 40)
                        delta3 = random.randint(-5, 5)
                        delta5 = random.randint(-1, 1)
                        if toward:
                            state["p1"] += abs(delta1) if state["p1"] < NORMAL_1 else -abs(delta1)
                            state["p3"] += abs(delta3) if state["p3"] < NORMAL_3 else -abs(delta3)
                            state["p5"] += abs(delta5) if state["p5"] < NORMAL_5 else -abs(delta5)
                        else:
                            state["p1"] += delta1
                            state["p3"] += delta3
                            state["p5"] += delta5
                        state["p1"] = max(min(state["p1"], MAX_1), MIN_1)
                        state["p3"] = max(min(state["p3"], MAX_3), MIN_3)
                        state["p5"] = max(min(state["p5"], MAX_5), MIN_5)

                elif state["state"] == "SPIKING":
                    state["spike_step"] += 1
                    t = state["spike_step"] / state["spike_duration"]
                    factor = 1 - pow(2.71828, -3 * t)
                    norm = 1 - pow(2.71828, -3)
                    start1, start3, start5 = state["spike_start"]
                    target1, target3, target5 = state["spike_target"]
                    state["p1"] = int(start1 + (target1 - start1) * (factor / norm))
                    state["p3"] = int(start3 + (target3 - start3) * (factor / norm))
                    state["p5"] = int(start5 + (target5 - start5) * (factor / norm))
                    if state["spike_step"] >= state["spike_duration"]:
                        state["state"] = "HOLDING"
                        state["hold_step"] = 0

                elif state["state"] == "HOLDING":
                    state["hold_step"] += 1
                    state["p1"], state["p3"], state["p5"] = state["spike_target"]
                    if state["hold_step"] >= state["hold_duration"]:
                        state["state"] = "OUT_OF_RANGE"

                elif state["state"] == "OUT_OF_RANGE":
                    toward = random.random() < 0.8
                    for key, normal, min_val, max_val in [
                        ("p1", NORMAL_1, MIN_1, MAX_1),
                        ("p3", NORMAL_3, MIN_3, MAX_3),
                        ("p5", NORMAL_5, MIN_5, MAX_5),
                    ]:
                        val = state[key]
                        if val > max_val:
                            state[key] += -random.randint(1, 3) if toward else random.randint(0, 1)
                        elif val < min_val:
                            state[key] += random.randint(1, 2)
                        state[key] = max(min(state[key], max_val), min_val)
                    if MIN_1 <= state["p1"] <= MAX_1 and MIN_3 <= state["p3"] <= MAX_3 and MIN_5 <= state["p5"] <= MAX_5:
                        state["state"] = "NORMAL"

            for sensor in LPM_SENSORS:
                state = sensor_states[sensor.sensor_id]
                noisy1 = state["p1"] + random.randint(-SENSOR_NOISE, SENSOR_NOISE)
                noisy3 = state["p3"] + random.randint(-SENSOR_NOISE, SENSOR_NOISE)
                noisy5 = state["p5"] + random.randint(-SENSOR_NOISE, SENSOR_NOISE)
                data_buffer.append((
                    now, "particle", sensor.sensor_id, state["zone_id"], "PPM", noisy1, noisy3, noisy5
                ))

            if len(data_buffer) >= len(LPM_SENSORS) * 5:
                cursor.executemany("""
                    INSERT INTO lpm_data
                    (timestamp, sensor_type, sensor_id, zone_id, unit, val_0_1um, val_0_3um, val_0_5um)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, data_buffer)
                conn.commit()
                print(f"[{now}] PARTICLE 데이터 {len(data_buffer)}개 삽입 완료")
                data_buffer.clear()

            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 PARTICLE 시뮬레이터 종료됨.")
    finally:
        cursor.close()
        conn.close()
