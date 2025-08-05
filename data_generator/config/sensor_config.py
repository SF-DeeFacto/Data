from collections import namedtuple

Sensor = namedtuple("Sensor", ["sensor_id", "zone_id"])

temp_ids = ["temp-005", "temp-006"]
zones = ["b01", "b02"]
TEMP_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(temp_ids, zones)]

hum_ids = ["hum-005", "hum-006"]
zones = ["b01", "b02"]
HUM_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(hum_ids, zones)]

wind_ids = ["wind-005", "wind-006"]
zones = ["b01", "b02"]
WIND_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(wind_ids, zones)]

esd_ids = ["esd-007", "esd-008"]
zones = ["b01", "b02"]
ESD_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(esd_ids, zones)]

lpm_ids = ["lpm-005", "lpm-006"]
zones = ["b01", "b02"]
LPM_SENSORS = [Sensor(sensor_id, zone) for sensor_id, zone in zip(lpm_ids, zones)]

