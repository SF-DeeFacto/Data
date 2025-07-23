package com.deefacto.sensorDataGen.esd;

import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class EsdCsvGenerator {
  // 센서 정보 클래스 (타입, ID, 구역)
    private static class Sensor {
    String sensorType;
    String sensorId;
    String zoneId;
    public Sensor(String sensorType, String sensorId, String zoneId) {
        this.sensorType = sensorType;
        this.sensorId = sensorId;
        this.zoneId = zoneId;
    }
}

// 시뮬레이션에 사용할 센서 목록 (zone별로 배치)
private static final List<Sensor> SENSORS = Arrays.asList(
        new Sensor("esd", "ESD-001", "A"),
        new Sensor("esd", "ESD-002", "A"),
        new Sensor("esd", "ESD-003", "A"),
        new Sensor("esd", "ESD-004", "A"),
        new Sensor("esd", "ESD-005", "B"),
        new Sensor("esd", "ESD-006", "B"),
        new Sensor("esd", "ESD-007", "B"),
        new Sensor("esd", "ESD-008", "B"),
        new Sensor("esd", "ESD-009", "C"),
        new Sensor("esd", "ESD-010", "C")
);

// 습도 시뮬레이션 파라미터 (정상값, 범위, 이상치 범위, 변화폭 등)
private static final int NORMAL_ESD = 50; // 정상 정전기(V) - 100V 이하
private static final int NORMAL_RANGE = 30; // 정상 허용 범위(±)
private static final int MIN_ESD = 0;
private static final int MAX_ESD = 100;
private static final int DELTA = 5; // 정상 상태 변화폭
private static final double OUT_PROB = 0.001; // 0.1% 확률로 이상치 발생
private static final int SECONDS = 3600; // 1시간치 데이터
private static final int SENSOR_NOISE = 5; // 센서별 미세 노이즈 (±5V)

private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'");

public static void main(String[] args) throws IOException {
    // zone 목록 추출 (A, B, C)
    Set<String> zoneSet = new HashSet<>();
    for (Sensor s : SENSORS) zoneSet.add(s.zoneId);
    List<String> zones = new ArrayList<>(zoneSet);
    Collections.sort(zones);

    // zone별 상태 및 정전기 관리 객체
    class ZoneState {
        int esd; // 현재 정전기 값
        String state; // 현재 상태 (NORMAL, SPIKING, HOLDING, OUT_OF_RANGE)
        int spikeStep; // 스파이크 단계(진행 중인 step)
        int spikeDuration; // 스파이크가 지속되는 총 step 수
        int spikeStartEsd; // 스파이크 시작 시 정전기
        int spikeTargetEsd; // 스파이크 목표 정전기
        int holdStep; // HOLDING 상태에서 경과한 step
        int holdDuration; // HOLDING 상태에서 유지할 step 수
        public ZoneState(int esd) {
            this.esd = esd;
            this.state = "NORMAL";
            this.spikeStep = 0;
            this.spikeDuration = 10;
            this.spikeStartEsd = esd;
            this.spikeTargetEsd = esd;
            this.holdStep = 0;
            this.holdDuration = 25;
        }
    }
    Map<String, ZoneState> zoneStates = new HashMap<>();
    Random rand = new Random();
    for (String zone : zones) {
        // zone별 초기 습도값을 정상범위 내에서 랜덤하게 설정
        int esd0 = NORMAL_ESD + (rand.nextInt(2 * NORMAL_RANGE + 1) - NORMAL_RANGE);
        zoneStates.put(zone, new ZoneState(esd0));
    }

    // 센서별 파일 준비 및 헤더 작성
    String dataDir = "Data/esd";
    java.io.File dir = new java.io.File(dataDir);
    if (!dir.exists()) dir.mkdirs();
    Map<String, FileWriter> writers = new HashMap<>();
    for (Sensor sensor : SENSORS) {
        writers.put(sensor.sensorId, new FileWriter(dataDir + "/" + sensor.sensorId + ".csv"));
        writers.get(sensor.sensorId).write("timestamp,sensor_type,sensor_id,unit,val,state\n");
    }

    LocalDateTime now = LocalDateTime.of(2025, 7, 15, 9, 32, 0);
    for (int i = 0; i < SECONDS; i++) {
        // zone별 정전기/상태 업데이트
        for (String zone : zones) {
            ZoneState zs = zoneStates.get(zone);
            switch (zs.state) {
                case "NORMAL":
                    // 정상 상태: 확률적으로 스파이크(이상치) 발생
                    if (rand.nextDouble() < OUT_PROB) {
                        zs.spikeTargetEsd = MAX_ESD + rand.nextInt(20); 
                        zs.spikeStartEsd = zs.esd;
                        zs.spikeStep = 0;
                        zs.spikeDuration = 10;
                        zs.holdStep = 0;
                        zs.holdDuration = 25;
                        zs.state = "SPIKING";
                    } else {
                        // 정상값으로 복원하려는 경향 + 랜덤 변화
                        double towardProb = 0.3;
                        boolean towardNormal = rand.nextDouble() < towardProb;
                        int delta = (rand.nextInt(10 * DELTA + 1) - 5 * DELTA); // -25 ~ +25 (포함)
                        if (towardNormal) {
                            if (zs.esd < NORMAL_ESD) {
                                zs.esd += Math.abs(delta);
                            } else if (zs.esd > NORMAL_ESD) {
                                zs.esd -= Math.abs(delta);
                            }
                        } else {
                            zs.esd += delta;
                        }
                        // 정상 범위 밖으로 벗어나지 않도록 보정
                        if (zs.esd < MIN_ESD) zs.esd = MIN_ESD;
                        if (zs.esd > MAX_ESD) zs.esd = NORMAL_ESD + NORMAL_RANGE;
                    }
                    break;
                case "SPIKING":
                    // 스파이크(이상치) 상태: 바로 목표 정전기로 이동
                    zs.spikeStep++;
                    if (zs.spikeStep >= zs.spikeDuration) {
                        zs.esd = zs.spikeTargetEsd; // 바로 목표값으로 설정
                        zs.state = "OUT_OF_RANGE"; // HOLDING 없이 바로 OUT_OF_RANGE로 이동
                    }
                    break;
                case "OUT_OF_RANGE":
                    double towardProb = 0.98;
                    boolean towardNormal;
                    int delta;
                    
                    towardNormal = rand.nextDouble() < towardProb;
                    if (towardNormal) {
                        delta = (rand.nextInt(5 * DELTA + 1) - 20 * DELTA); // -20 ~ +5 (포함)
                    } else {
                        delta = -(rand.nextInt(10 * DELTA + 1) - 5 * DELTA); // -5 ~ +10 (포함)
                    }
                    zs.esd += delta;
                    // 정상 범위로 복귀하면 NORMAL 상태로 전환
                    if (zs.esd >= MIN_ESD && zs.esd <= MAX_ESD) {
                        zs.state = "NORMAL";
                    }
                    break;
            }
        }
        // 센서별 데이터 기록 (zone 상태 + 센서 노이즈 적용)
        for (Sensor sensor : SENSORS) {
            ZoneState zs = zoneStates.get(sensor.zoneId);
            int sensorEsd = zs.esd + (rand.nextInt(2 * SENSOR_NOISE + 1) - SENSOR_NOISE);
            if (sensorEsd < MIN_ESD) sensorEsd = MIN_ESD;
            if (zs.state == "NORMAL" && sensorEsd >= MAX_ESD) {
                sensorEsd = NORMAL_ESD + NORMAL_RANGE;
            }
            String line = String.format("%s,esd,%s,V,%d,%s\n",
                    now.plusSeconds(i).format(FORMATTER), sensor.sensorId, sensorEsd, zs.state);
            writers.get(sensor.sensorId).write(line);
        }
    }
    // 파일 닫기
    for (FileWriter w : writers.values()) w.close();
}
}

