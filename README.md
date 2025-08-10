# Data
시나리오 데이터 공유용 레포

7/22 - MES 데이터를 A 공정  B공정 C공정으로 나누어서 파일을 분리
no
공장 장비가 하나의 시간대만 사용되어 멀티 쓰레딩이 안된다~~~~~ 고친다 ~~~~

7/23 - 온도, 습도, 파티클, 정전기, 풍향 센서 데이터 생성기 작성 완료

각각의 데이터는 Data folder 안에 생성되어 있다. 2025년 7월 15일 9시32분00초 기준으로 60부  

8/4
- 그라파나 time series로 표시시 각 데이터를 센서별로 묶어서 표시하는 방법

    - Transformations에서 add transformation을 한다.
    - 나오는 메뉴에서 partition by values를 선택한다.
    - select field 에서 sensor_id를 선택하면 같은 센서끼리 그래프를 그려준다.

---------------------
# data_generator 사용법

1) 가상환경 생성 및 활성화
```
python -m venv venv
source .\venv\Scripts\activate
```

2) 필요한 패키지 설치
```
pip install -r requirements.txt
```

3) opensearch docker-compose 실행 
```
docker-compose up -d
```

4) 데이터 생성
```
python data_generator.py
```

5) opensearch와 mysql에 데이터가 잘 들어갔는지 확인

http://localhost:5601/ 
에 접속하여 확인

📌 센서별 저장 구조

| 센서 타입   | OpenSearch 인덱스명        | MySQL 테이블명 | 설명 |
|-------------|----------------------------|----------------|------|
| temp        | sensor_temp_stream         | temp_data      | 온도 센서 데이터 (°C) |
| humidity    | sensor_hum_stream          | hum_data       | 습도 센서 데이터 (%RH) |
| windDir     | sensor_wind_stream         | wind_data      | 풍향 센서 데이터 (deg) |
| esd         | sensor_esd_stream          | esd_data       | 정전기(ESD) 센서 데이터 (V) |
| particle    | sensor_particle_stream     | lpm_data       | 미세먼지(PM) 센서 데이터 (0.1/0.3/0.5um, PPM) |