SENSOR_TABLE_SCHEMAS = {
    "temp_data": """
        CREATE TABLE IF NOT EXISTS temp_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            sensor_type VARCHAR(20),
            sensor_id VARCHAR(20),
            zone_id VARCHAR(10),
            unit VARCHAR(5),
            val FLOAT
        )
    """,
    "hum_data": """
        CREATE TABLE IF NOT EXISTS hum_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            sensor_type VARCHAR(20),
            sensor_id VARCHAR(20),
            zone_id VARCHAR(10),
            unit VARCHAR(5),
            val FLOAT
        )
    """,
    "wind_data": """
        CREATE TABLE IF NOT EXISTS wind_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            sensor_type VARCHAR(20),
            sensor_id VARCHAR(20),
            zone_id VARCHAR(10),
            unit VARCHAR(5),
            val FLOAT
        )
    """,
    "esd_data": """
        CREATE TABLE IF NOT EXISTS esd_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            sensor_type VARCHAR(20),
            sensor_id VARCHAR(20),
            zone_id VARCHAR(10),
            unit VARCHAR(5),
            val FLOAT
        )
    """,
    "lpm_data": """
        CREATE TABLE IF NOT EXISTS lpm_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            sensor_type VARCHAR(20),
            sensor_id VARCHAR(20),
            zone_id VARCHAR(10),
            unit VARCHAR(10),
            val_0_1um FLOAT,
            val_0_3um FLOAT,
            val_0_5um FLOAT
        )
    """
}
