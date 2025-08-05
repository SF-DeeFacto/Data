import mysql.connector
from config.db_config import DB_CONFIG
from models.sensor_schema import SENSOR_TABLE_SCHEMAS

def create_table(table_name: str):

    if table_name not in SENSOR_TABLE_SCHEMAS:
        print(f"Unknown table: {table_name}")
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        print(f"Creating table: {table_name}")
        cursor.execute(SENSOR_TABLE_SCHEMAS[table_name])
        conn.commit()
        print("Table created successfully.")
    except mysql.connector.Error as e:
        print(f"Error creating table {table_name}: {e}")
    finally:
        cursor.close()
        conn.close()

def table_exists(table_name: str) -> bool:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python create_table.py <table_name>")
    else:
        create_table(sys.argv[1])
