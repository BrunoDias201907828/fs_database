import psycopg2
import os

def create_database_if_needed(host, port, user, password, dbname):
    conn = psycopg2.connect(
        dbname="postgres",
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if db already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone()

    # remove db with that name if it already exists
    if exists:
        # terminate all the connections
        cur.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s;
        """, (dbname,))
        
        # drop the database
        cur.execute(f"DROP DATABASE {dbname}")
        print(f"Dropped existing database '{dbname}'.")

    # Create the database
    cur.execute(f"CREATE DATABASE {dbname}")
    print(f"Database '{dbname}' created.")

    cur.close()
    conn.close()


def setup_schema():
    host = "localhost"
    port = 5432
    user = "postgres"
    password = "password"
    dbname = "autonomous_db"
    
    # 1) Recreate the database
    create_database_if_needed(host, port, user, password, dbname)
    
    # 2) Connect to the new DB
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()
    
    # 3) Run all SQL statements from schema.sql
    schema_file_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_file_path, "r") as f:
        sql_script = f.read()
    
    # If your psycopg2 version allows multiple statements in one go:
    cur.execute(sql_script)

    conn.commit()
    cur.close()
    conn.close()
    print("Schema created and tables converted to hypertables.")

if __name__ == "__main__":
    setup_schema()
