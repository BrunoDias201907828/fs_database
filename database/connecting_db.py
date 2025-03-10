import psycopg2

DB_CONFIG = {
    "dbname": "autonomous_db",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
