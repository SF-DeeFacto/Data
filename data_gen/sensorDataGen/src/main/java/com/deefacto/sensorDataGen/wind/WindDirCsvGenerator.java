package com.deefacto.sensorDataGen.wind;

import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class WindDirCsvGenerator {
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
            new Sensor("WindDir", "WD-001", "A"),
            new Sensor("WindDir", "WD-002", "A"),
            new Sensor("WindDir", "WD-003", "A"),
            new Sensor("WindDir", "WD-004", "A"),
            new Sensor("WindDir", "WD-005", "B"),
            new Sensor("WindDir", "WD-006", "B"),
            new Sensor("WindDir", "WD-007", "B"),
            new Sensor("WindDir", "WD-008", "B"),
            new Sensor("WindDir", "WD-009", "C"),
            new Sensor("WindDir", "WD-010", "C")
    );

    // 풍향 시뮬레이션 파라미터 (정상값, 범위, 이상치 범위, 변화폭 등)
    private static final int NORMAL_WD = 0; // 정상 방향(도)
    private static final int NORMAL_RANGE = 14; // 정상 허용 범위(±)
    private static final int OUT_RANGE = 20; // 이상치 허용 범위(±)
    private static final int MIN_WD = NORMAL_WD - NORMAL_RANGE;
    private static final int MAX_WD = NORMAL_WD + NORMAL_RANGE;
    private static final int OUT_MIN = NORMAL_WD - OUT_RANGE;
    private static final int OUT_MAX = NORMAL_WD + OUT_RANGE;
    private static final int DELTA = 1; // 정상 상태 변화폭
    private static final double OUT_PROB = 0.001; // 0.1% 확률로 이상치 발생
    private static final int SECONDS = 3600; // 1시간치 데이터
    private static final int SENSOR_NOISE = 1; // 센서별 미세 노이즈 (±1도)

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'");

    public static void main(String[] args) throws IOException {
        // zone 목록 추출 (A, B, C)
        Set<String> zoneSet = new HashSet<>();
        for (Sensor s : SENSORS) zoneSet.add(s.zoneId);
        List<String> zones = new ArrayList<>(zoneSet);
        Collections.sort(zones);

        // zone별 상태 및 풍향  관리 객체
        class ZoneState {
            int windDir; // 현재 풍향 값
            String state; // 현재 상태 (NORMAL, SPIKING, HOLDING, OUT_OF_RANGE)
            int spikeStep; // 스파이크 단계(진행 중인 step)
            int spikeDuration; // 스파이크가 지속되는 총 step 수
            int spikeStartWindDir; // 스파이크 시작 시 풍향
            int spikeTargetWindDir; // 스파이크 목표 풍향
            int holdStep; // HOLDING 상태에서 경과한 step
            int holdDuration; // HOLDING 상태에서 유지할 step 수
            public ZoneState(int windDir) {
                this.windDir = windDir;
                this.state = "NORMAL";
                this.spikeStep = 0;
                this.spikeDuration = 10;
                this.spikeStartWindDir = windDir;
                this.spikeTargetWindDir = windDir;
                this.holdStep = 0;
                this.holdDuration = 25;
            }
        }
        Map<String, ZoneState> zoneStates = new HashMap<>();
        Random rand = new Random();
        for (String zone : zones) {
            // zone별 초기 풍향값을 정상범위 내에서 랜덤하게 설정
            int w0 = NORMAL_WD + (rand.nextInt(2) * 2 - 1) * NORMAL_RANGE;
            zoneStates.put(zone, new ZoneState(w0));
        }

        // 센서별 파일 준비 및 헤더 작성
        String dataDir = "Data/windDir";
        java.io.File dir = new java.io.File(dataDir);
        if (!dir.exists()) dir.mkdirs();
        Map<String, FileWriter> writers = new HashMap<>();
        for (Sensor sensor : SENSORS) {
            writers.put(sensor.sensorId, new FileWriter(dataDir + "/" + sensor.sensorId + ".csv"));
            writers.get(sensor.sensorId).write("timestamp,sensor_type,sensor_id,unit,val\n");
        }

        LocalDateTime now = LocalDateTime.of(2025, 7, 15, 9, 32, 0);
        for (int i = 0; i < SECONDS; i++) {
            // zone별 습도/상태 업데이트
            for (String zone : zones) {
                ZoneState zs = zoneStates.get(zone);
                switch (zs.state) {
                    case "NORMAL":
                        // 정상 상태: 확률적으로 스파이크(이상치) 발생
                        if (rand.nextDouble() < OUT_PROB) {
                            // 이상치 방향(상승/하강) 랜덤 결정
                            if (rand.nextBoolean()) {
                                zs.spikeTargetWindDir = OUT_MIN + rand.nextInt(MIN_WD - OUT_MIN);
                            } else {
                                zs.spikeTargetWindDir = MAX_WD + rand.nextInt(OUT_MAX - MAX_WD);
                            }
                            zs.spikeStartWindDir = zs.windDir;
                            zs.spikeStep = 0;
                            zs.spikeDuration = 10;
                            zs.holdStep = 0;
                            zs.holdDuration = 25;
                            zs.state = "SPIKING";
                        } else {
                            // 정상값으로 복원하려는 경향 + 랜덤 변화
                            double towardProb = 0.8;
                            boolean towardNormal = rand.nextDouble() < towardProb;
                            int delta = rand.nextInt(7) - 3;
                            if (towardNormal) {
                                if (delta < 0) {
                                    delta = -delta;
                                }
                                if (zs.windDir < NORMAL_WD) {
                                    zs.windDir += delta;
                                } else {
                                    zs.windDir -= delta;
                                }
                            } else {
                                zs.windDir += delta;
                            }
                            // 정상 범위 밖으로 벗어나지 않도록 보정
                            if (zs.windDir < MIN_WD) zs.windDir = MIN_WD;
                            if (zs.windDir > MAX_WD) zs.windDir = MAX_WD;
                        }
                        break;
                    case "SPIKING":
                        // 스파이크(이상치) 상태: exp 곡선으로 목표 습도까지 빠르게 이동
                        zs.spikeStep++;
                        double t = (double)zs.spikeStep / zs.spikeDuration;
                        double expFactor = 1 - Math.exp(-3 * t);
                        double expNorm = 1 - Math.exp(-3);
                        zs.windDir = (int)(zs.spikeStartWindDir + (zs.spikeTargetWindDir - zs.spikeStartWindDir) * (expFactor / expNorm));
                        if (zs.spikeStep >= zs.spikeDuration) {
                            zs.state = "HOLDING";
                            zs.holdStep = 0;
                        }
                        break;
                    case "HOLDING":
                        // HOLDING: 스파이크 목표값을 일정 시간 유지
                        zs.holdStep++;
                        zs.windDir = zs.spikeTargetWindDir;
                        if (zs.holdStep >= zs.holdDuration) {
                            zs.state = "OUT_OF_RANGE";
                        }
                        break;
                    case "OUT_OF_RANGE":
                        // OUT_OF_RANGE: 정상 범위로 완만하게 복귀
                        double towardProb = 0.8;
                        boolean towardNormal;
                        double delta;
                        if (zs.windDir < NORMAL_WD) {
                            towardNormal = rand.nextDouble() < towardProb;
                            if (towardNormal) {
                                delta = 0.05 + rand.nextDouble() * 0.005;
                            } else {
                                delta = -(0.05 + rand.nextDouble() * 0.005);
                            }
                        } else {
                            towardNormal = rand.nextDouble() < towardProb;
                            if (towardNormal) {
                                delta = -(0.05 + rand.nextDouble() * 0.005);
                            } else {
                                delta = 0.05 + rand.nextDouble() * 0.005;
                            }
                        }
                        zs.windDir += delta;
                        // 정상 범위로 복귀하면 NORMAL 상태로 전환
                        if (zs.windDir >= MIN_WD && zs.windDir <= MAX_WD) {
                            zs.state = "NORMAL";
                        }
                        break;
                }
            }
            // 센서별 데이터 기록 (zone 상태 + 센서 노이즈 적용)
            for (Sensor sensor : SENSORS) {
                ZoneState zs = zoneStates.get(sensor.zoneId);
                int sensorWindDir = zs.windDir + (rand.nextInt(2) * 2 - 1) * SENSOR_NOISE;
                String line = String.format("%s,windDir,%s,deg,%d\n",
                        now.plusSeconds(i).format(FORMATTER), sensor.sensorId, sensorWindDir);
                writers.get(sensor.sensorId).write(line);
            }
        }
        // 파일 닫기
        for (FileWriter w : writers.values()) w.close();
    }
}
