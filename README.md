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

    