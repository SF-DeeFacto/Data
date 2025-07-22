package com.deefacto.sensorDataGen.particle;

import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class ParticleCsvGenerator {
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
            new Sensor("PPM", "LPM-001", "A"),
            new Sensor("PPM", "LPM-002", "A"),
            new Sensor("PPM", "LPM-003", "A"),
            new Sensor("PPM", "LPM-004", "A"),
            new Sensor("PPM", "LPM-005", "B"),
            new Sensor("PPM", "LPM-006", "B"),
            new Sensor("PPM", "LPM-007", "B"),
            new Sensor("PPM", "LPM-008", "B"),
            new Sensor("PPM", "LPM-009", "C")
    );

    // 미세먼지 시뮬레이션 파라미터 (정상값, 범위, 변화폭 등)
    private static final int NORMAL_1 = 850; // ≥0.1µm, 정상값
    private static final int NORMAL_3 = 82;  // ≥0.3µm, 정상값
    private static final int NORMAL_5 = 20;  // ≥0.5µm, 정상값
    private static final int NORMAL_1_RANGE = 150; // 정상 허용 범위(±)
    private static final int NORMAL_3_RANGE = 20;
    private static final int NORMAL_5_RANGE = 15;
    private static final int MIN_1 = 0;
    private static final int MAX_1 = NORMAL_1 + NORMAL_1_RANGE;
    private static final int MIN_3 = 0;
    private static final int MAX_3 = NORMAL_3 + NORMAL_3_RANGE;
    private static final int MIN_5 = 0;
    private static final int MAX_5 = NORMAL_5 + NORMAL_5_RANGE;
    private static final int DELTA = 1; // 정상 상태 변화폭
    private static final double OUT_PROB = 0.0008; // 0.08% 확률로 이상치 발생
    private static final int SECONDS = 3600; // 1시간치 데이터
    private static final int SENSOR_NOISE = 1; // 센서별 미세 노이즈 (±1 particles/m³)

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'");

    public static void main(String[] args) throws IOException {
        // zone 목록 추출 (A, B, C)
        Set<String> zoneSet = new HashSet<>();
        for (Sensor s : SENSORS) zoneSet.add(s.zoneId);
        List<String> zones = new ArrayList<>(zoneSet);
        Collections.sort(zones);

        // zone별 상태 및 미세먼지 값 관리 객체
        class ZoneState {
            int particle1; // 현재 0.1µm 미세먼지 값
            int particle3; // 현재 0.3µm 미세먼지 값
            int particle5; // 현재 0.5µm 미세먼지 값
            String state; // 현재 상태 (NORMAL, SPIKING, HOLDING, OUT_OF_RANGE)
            int spikeStep; // 스파이크 단계(진행 중인 step)
            int spikeDuration; // 스파이크가 지속되는 총 step 수
            int spikeStartParticle1; // 스파이크 시작 시 0.1µm 미세먼지 값
            int spikeStartParticle3; // 스파이크 시작 시 0.3µm 미세먼지 값
            int spikeStartParticle5; // 스파이크 시작 시 0.5µm 미세먼지 값
            int spikeTargetParticle1; // 스파이크 목표 0.1µm 미세먼지 값
            int spikeTargetParticle3; // 스파이크 목표 0.3µm 미세먼지 값
            int spikeTargetParticle5; // 스파이크 목표 0.5µm 미세먼지 값
            int holdStep; // HOLDING 상태에서 경과한 step
            int holdDuration; // HOLDING 상태에서 유지할 step 수
            public ZoneState(int particle1, int particle3, int particle5) {
                this.particle1 = particle1;
                this.particle3 = particle3;
                this.particle5 = particle5;
                this.state = "NORMAL";
                this.spikeStep = 0;
                this.spikeDuration = 10;
                this.spikeStartParticle1 = particle1;
                this.spikeStartParticle3 = particle3;
                this.spikeStartParticle5 = particle5;
                this.spikeTargetParticle1 = particle1;
                this.spikeTargetParticle3 = particle3;
                this.spikeTargetParticle5 = particle5;
                this.holdStep = 0;
                this.holdDuration = 25;
            }
        }
        Map<String, ZoneState> zoneStates = new HashMap<>();
        Random rand = new Random();
        for (String zone : zones) {
            // zone별 초기 미세먼지 값을 정상범위 내에서 랜덤하게 설정
            int particle1 = NORMAL_1 + (rand.nextInt(2 * NORMAL_1_RANGE) - NORMAL_1_RANGE);
            int particle3 = NORMAL_3 + (rand.nextInt(2 * NORMAL_3_RANGE) - NORMAL_3_RANGE);
            int particle5 = NORMAL_5 + (rand.nextInt(2 * NORMAL_5_RANGE) - NORMAL_5_RANGE);
            zoneStates.put(zone, new ZoneState(particle1, particle3, particle5));
        }

        // 센서별 파일 준비 및 헤더 작성
        String dataDir = "Data/particle";
        java.io.File dir = new java.io.File(dataDir);
        if (!dir.exists()) dir.mkdirs();
        Map<String, FileWriter> writers = new HashMap<>();
        for (Sensor sensor : SENSORS) {
            writers.put(sensor.sensorId, new FileWriter(dataDir + "/" + sensor.sensorId + ".csv"));
            writers.get(sensor.sensorId).write("timestamp,sensor_type,sensor_id,unit,val_0.1µm,val_0.3µm,val_0.5µm\n");
        }

        LocalDateTime now = LocalDateTime.of(2025, 7, 15, 9, 32, 0);
        for (int i = 0; i < SECONDS; i++) {
            // zone별 미세먼지 상태 업데이트
            for (String zone : zones) {
                ZoneState zs = zoneStates.get(zone);
                switch (zs.state) {
                    case "NORMAL":
                        // 정상 상태: 확률적으로 스파이크(이상치) 발생
                        if (rand.nextDouble() < OUT_PROB) {
                            zs.spikeTargetParticle1 = MAX_1 + rand.nextInt(50);
                            zs.spikeTargetParticle3 = MAX_3 + rand.nextInt(20);
                            zs.spikeTargetParticle5 = MAX_5 + rand.nextInt(5);
                            zs.spikeStartParticle1 = zs.particle1;
                            zs.spikeStartParticle3 = zs.particle3;
                            zs.spikeStartParticle5 = zs.particle5;
                            zs.spikeStep = 0;
                            zs.spikeDuration = 10;
                            zs.holdStep = 0;
                            zs.holdDuration = 25;
                            zs.state = "SPIKING";
                        } else {
                            // 정상값으로 복원하려는 경향 + 랜덤 변화
                            double towardProb = 0.3;
                            boolean towardNormal = rand.nextDouble() < towardProb;
                            int delta1 = (rand.nextInt(70 * DELTA + 1) - 40 * DELTA); // -40, -39, ..., 39, 40
                            int delta3 = (rand.nextInt(10 * DELTA + 1) - 5 * DELTA); // -5, -4, ..., 4, 5
                            int delta5 = (rand.nextInt(2 * DELTA + 1) - DELTA); // -1, 0, 1
                            // 정상값으로 복원하는 경향
                            if (towardNormal) {
                                if (zs.particle1 < NORMAL_1) {
                                    zs.particle1 += Math.abs(delta1);
                                } else if (zs.particle1 > NORMAL_1) {
                                    zs.particle1 -= Math.abs(delta1);
                                }
                                if (zs.particle3 < NORMAL_3) {
                                    zs.particle3 += Math.abs(delta3);
                                } else if (zs.particle3 > NORMAL_3) {
                                    zs.particle3 -= Math.abs(delta3);
                                }
                                if (zs.particle5 < NORMAL_5) {
                                    zs.particle5 += Math.abs(delta5);
                                } else if (zs.particle5 > NORMAL_5) {
                                    zs.particle5 -= Math.abs(delta5);
                                }
                            } else {
                                zs.particle1 += delta1;
                                zs.particle3 += delta3;
                                zs.particle5 += delta5;
                            }
                            // 정상 범위 밖으로 벗어나지 않도록 보정
                            if (zs.particle1 < MIN_1) zs.particle1 = MIN_1;
                            if (zs.particle1 > MAX_1) zs.particle1 = MAX_1;
                            if (zs.particle3 < MIN_3) zs.particle3 = MIN_3;
                            if (zs.particle3 > MAX_3) zs.particle3 = MAX_3;
                            if (zs.particle5 < MIN_5) zs.particle5 = MIN_5;
                            if (zs.particle5 > MAX_5) zs.particle5 = MAX_5;
                        }
                        break;
                    case "SPIKING":
                        // 스파이크(이상치) 상태: exp 곡선으로 목표값까지 빠르게 이동
                        zs.spikeStep++;
                        double t = zs.spikeStep / zs.spikeDuration;
                        double expFactor = 1 - Math.exp(-3 * t);
                        double expNorm = 1 - Math.exp(-3);
                        zs.particle1 = (int)(zs.spikeStartParticle1 + (zs.spikeTargetParticle1 - zs.spikeStartParticle1) * (expFactor / expNorm));
                        zs.particle3 = (int)(zs.spikeStartParticle3 + (zs.spikeTargetParticle3 - zs.spikeStartParticle3) * (expFactor / expNorm));
                        zs.particle5 = (int)(zs.spikeStartParticle5 + (zs.spikeTargetParticle5 - zs.spikeStartParticle5) * (expFactor / expNorm));
                        if (zs.spikeStep >= zs.spikeDuration) {
                            zs.state = "HOLDING";
                            zs.holdStep = 0;
                        }
                        break;
                    case "HOLDING":
                        // HOLDING: 스파이크 목표값을 일정 시간 유지
                        zs.holdStep++;
                        zs.particle1 = zs.spikeTargetParticle1;
                        zs.particle3 = zs.spikeTargetParticle3;
                        zs.particle5 = zs.spikeTargetParticle5;
                        if (zs.holdStep >= zs.holdDuration) {
                            zs.state = "OUT_OF_RANGE";
                        }
                        break;
                    case "OUT_OF_RANGE": {
                        // OUT_OF_RANGE: 정상 범위로 완만하게 복귀
                        double towardProb = 0.8;
                        int delta1 = 0, delta3 = 0, delta5 = 0;
                        boolean towardNormal;
                        if (zs.particle1 > MAX_1) {
                            towardNormal = rand.nextDouble() < towardProb;
                            if (towardNormal) {
                                delta1 = -rand.nextInt(3) - 1; // -1, -2, -3
                            } else {
                                delta1 = rand.nextInt(2); // 0, 1
                            }
                        } else if (zs.particle1 < MIN_1) {
                            delta1 = rand.nextInt(3) + 1; // 1, 2, 3
                        }
                        if (zs.particle3 > MAX_3) {
                            towardNormal = rand.nextDouble() < towardProb;
                            if (towardNormal) {
                                delta3 = -rand.nextInt(2) - 1; // -1, -2
                            } else {
                                delta3 = rand.nextInt(2); // 0, 1
                            }
                        } else if (zs.particle3 < MIN_3) {
                            delta3 = rand.nextInt(2) + 1; // 1, 2
                        }
                        if (zs.particle5 > MAX_5) {
                            towardNormal = rand.nextDouble() < towardProb;
                            if (towardNormal) {
                                delta5 = -rand.nextInt(2) - 1; // -1, -2
                            } else {
                                delta5 = rand.nextInt(2); // 0, 1
                            }
                        } else if (zs.particle5 < MIN_5) {
                            delta5 = rand.nextInt(2) + 1; // 1, 2
                        }
                        zs.particle1 += delta1;
                        zs.particle3 += delta3;
                        zs.particle5 += delta5;
                        // 정상 범위로 복귀하면 NORMAL 상태로 전환
                        if (zs.particle1 >= MIN_1 && zs.particle1 <= MAX_1 && zs.particle3 >= MIN_3 && zs.particle3 <= MAX_3 && zs.particle5 >= MIN_5 && zs.particle5 <= MAX_5) {
                            zs.state = "NORMAL";
                        }
                        // 정상 범위 밖으로 벗어나지 않도록 보정
                        if (zs.particle1 < MIN_1) zs.particle1 = MIN_1;
                        if (zs.particle3 < MIN_3) zs.particle3 = MIN_3;
                        if (zs.particle5 < MIN_5) zs.particle5 = MIN_5;
                        break;
                    }
                }
            }
            // 센서별 데이터 기록 (zone 상태 + 센서 노이즈 적용)
            for (Sensor sensor : SENSORS) {
                ZoneState zs = zoneStates.get(sensor.zoneId);
                int sensorParticle1 = zs.particle1 + (rand.nextInt(2 * SENSOR_NOISE) - SENSOR_NOISE);
                int sensorParticle3 = zs.particle3 + (rand.nextInt(2 * SENSOR_NOISE) - SENSOR_NOISE);
                int sensorParticle5 = zs.particle5 + (rand.nextInt(2 * SENSOR_NOISE) - SENSOR_NOISE);
                // 1 파티클 단위로 반올림
                String line = String.format("%s,particle,%s,%s,%d,%d,%d\n",
                        now.plusSeconds(i).format(FORMATTER), sensor.sensorId, sensor.sensorType, sensorParticle1, sensorParticle3, sensorParticle5);
                writers.get(sensor.sensorId).write(line);
            }
        }
        // 파일 닫기
        for (FileWriter w : writers.values()) w.close();
    }
}

