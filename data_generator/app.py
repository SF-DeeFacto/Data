from generators.temp_generator import run_temp_simulation
from generators.hum_generator import run_humidity_simulation
from generators.wind_generator import run_wind_simulation
from generators.esd_generator import run_esd_simulation
from generators.particle_generator import run_particle_simulation
from create_table import create_table, table_exists
import threading
import time

if __name__ == "__main__":
    print("Creating table...\n")

    for table in ["temp_data", "hum_data", "wind_data", "esd_data", "lpm_data"]:
        if not table_exists(table):
            create_table(table)

    print("Starting sensor simulators...\n")

    # 스레드 정의
    temp_thread = threading.Thread(target=run_temp_simulation, name="TempThread", daemon=True)
    hum_thread = threading.Thread(target=run_humidity_simulation, name="HumThread", daemon=True)
    wind_thread = threading.Thread(target=run_wind_simulation, name="WindThread", daemon=True)
    esd_thread = threading.Thread(target=run_esd_simulation, name="EsdThread", daemon=True)
    particle_thread = threading.Thread(target=run_particle_simulation, name="ParticleThread", daemon=True)

    # 스레드 시작
    temp_thread.start()
    hum_thread.start()
    wind_thread.start()
    esd_thread.start()
    particle_thread.start()

    print("Sensor 시뮬레이터 실행 중...)\n")

    # 메인 스레드는 루프 유지
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n전체 시뮬레이터 종료됨.")
