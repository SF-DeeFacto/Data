from collections import namedtuple

Sensor = namedtuple("Sensor", ["sensor_id", "zone_id"])

temp_ids = ["temp-001", "temp-002","temp-003", "temp-004", "temp-005", "temp-006", "temp-007", "temp-008", "temp-009", "temp-010", "temp-011", "temp-012"]
zones = ["a01","a01","a02","a02","b01", "b02","b03", "b04", "c01", "c01", "c02", "c02"]
TEMP_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(temp_ids, zones)]

hum_ids = ["hum-001", "hum-002", "hum-003", "hum-004", "hum-005", "hum-006", "hum-007", "hum-008", "hum-009", "hum-010", "hum-011", "hum-012"]
zones = ["a01","a01","a01","a01","a02","a02","b01", "b02", "b03", "b04","c01", "c02"]
HUM_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(hum_ids, zones)]

wind_ids = ["wind-001", "wind-002", "wind-003", "wind-004", "wind-005", "wind-006","wind-007", "wind-008", "wind-009", "wind-010"]
zones = ["a01","a01","a02","a02","b01", "b02", "b03", "b04","c01","c02"]
WIND_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(wind_ids, zones)]

esd_ids = ["esd-001", "esd-002", "esd-003", "esd-004","esd-005", "esd-006", "esd-007", "esd-008", "esd-009", "esd-010", "esd-011", "esd-012"]
zones = ["a01","a01","a01","a01","a02","a02","b01", "b02", "b03", "b04","c01","c02"]
ESD_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(esd_ids, zones)]

lpm_ids = ["lpm-001", "lpm-002", "lpm-003", "lpm-004", "lpm-005", "lpm-006", "lpm-007", "lpm-008", "lpm-009"]
zones = ["a01","a01","a02","a02","b01", "b02", "b03", "b04", "c01"]
LPM_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(lpm_ids, zones)]

