import psycopg2

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

    # removes db with that name if it already exists
    if exists:
        # terminate all the connections to the database
        cur.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s;
        """, (dbname,))
        
        # drops the database
        cur.execute(f"DROP DATABASE {dbname}")
        print(f"Dropped existing database '{dbname}'.")
    
    # Create the database
    cur.execute(f"CREATE DATABASE {dbname}")
    print(f"Database '{dbname}' created.")

    # if not exists:
    #     cur.execute(f"CREATE DATABASE {dbname}")
    #     print(f"Database '{dbname}' created.")
    # else:
    #     print(f"Database '{dbname}' already exists.")
    
    cur.close()
    conn.close()

def setup_schema():
    host = "localhost"       # or "timescaledb" if connecting from another container in Docker
    port = 5432
    user = "postgres"
    password = "password"
    dbname = "autonomous_db"
    
    # Create the database if it hasnt been done already.
    create_database_if_needed(host, port, user, password, dbname)
    
    # Connect to database
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()
    
    # Enable TimescaleDB extension if it hasnt already
    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS timescaledb;
    """)
    
    # runs (metadata table)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id       SERIAL PRIMARY KEY,
            run_name     TEXT NOT NULL,
            start_time   TIMESTAMPTZ NOT NULL,
            end_time     TIMESTAMPTZ,
            slam_type    TEXT,
            rosbag_path  TEXT,
            run_type     TEXT,
            doc_url      TEXT
        );
    """)
    
    # perception
    cur.execute("""
        CREATE TABLE IF NOT EXISTS perception (
            time              TIMESTAMPTZ NOT NULL,
            run_id            INT NOT NULL REFERENCES runs(run_id),
            num_objects       INT,
            detection_conf    REAL,
            metric_1          REAL,
            metric_2          REAL,
            PRIMARY KEY (time, run_id)
        );
    """)
    
    # state_estimation_pred_corr
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state_estimation_pred_corr (
            time                TIMESTAMPTZ NOT NULL,
            run_id              INT NOT NULL REFERENCES runs(run_id),
            prediction_error    REAL,
            correction_error    REAL,
            PRIMARY KEY (time, run_id)
        );
    """)
    
    # state_estimation_state
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state_estimation_state (
            time       TIMESTAMPTZ NOT NULL,
            run_id     INT NOT NULL REFERENCES runs(run_id),
            x          DOUBLE PRECISION,
            y          DOUBLE PRECISION,
            vx         DOUBLE PRECISION,
            vy         DOUBLE PRECISION,
            theta      DOUBLE PRECISION,
            v          DOUBLE PRECISION,
            omega      DOUBLE PRECISION,
            PRIMARY KEY (time, run_id)
        );
    """)
    
    # state_estimation_map
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state_estimation_map (
            time          TIMESTAMPTZ NOT NULL,
            run_id        INT NOT NULL REFERENCES runs(run_id),
            map_metric_1  REAL,
            map_metric_2  REAL,
            PRIMARY KEY (time, run_id)
        );
    """)
    
    # planning
    cur.execute("""
        CREATE TABLE IF NOT EXISTS planning (
            time              TIMESTAMPTZ NOT NULL,
            run_id            INT NOT NULL REFERENCES runs(run_id),
            size_yellow_cone  REAL,
            size_blue_cones  REAL,
            PRIMARY KEY (time, run_id)
        );
    """)
    
    # control
    cur.execute("""
        CREATE TABLE IF NOT EXISTS control (
            time                TIMESTAMPTZ NOT NULL,
            run_id              INT NOT NULL REFERENCES runs(run_id),
            steering_angle      REAL,
            throttle            REAL,
            PRIMARY KEY (time, run_id)
        );
    """)
    
    # vehicle_data
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_data (
            vehicle_config_id          SERIAL PRIMARY KEY,
            start_time                 TIMESTAMPTZ NOT NULL,
            end_time                   TIMESTAMPTZ,
            vehicle_name               TEXT,
            gear_ratio                 REAL,
            tire_type                  TEXT,
            tire_pressure              REAL
        );
    """)

    # perception parameters
    cur.execute("""
        CREATE TABLE IF NOT EXISTS perception_parameters (
            perception_param_id SERIAL PRIMARY KEY,
            run_id              INT NOT NULL REFERENCES runs(run_id),
            param_1             INT NOT NULL,
            param_2             INT NOT NULL                
        );
    """)
    
    # state estimation parameters
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state_estimation_parameters (
            state_est_param_id  SERIAL PRIMARY KEY,
            run_id              INT NOT NULL REFERENCES runs(run_id),
            param_1             INT NOT NULL,
            param_2             INT NOT NULL        
        );
    """)
    
    # planning parameters
    cur.execute("""
        CREATE TABLE IF NOT EXISTS planning_parameters (
            planning_param_id   SERIAL PRIMARY KEY,
            run_id              INT NOT NULL REFERENCES runs(run_id),
            param_1             INT NOT NULL,
            param_2             INT NOT NULL        
        );
    """)
    
    # control parameters
    cur.execute("""
        CREATE TABLE IF NOT EXISTS control_parameters (
            control_param_id    SERIAL PRIMARY KEY,
            run_id              INT NOT NULL REFERENCES runs(run_id),
            param_1             INT NOT NULL,
            param_2             INT NOT NULL        
        );
    """)
    
    # Converts some tables to hypertables
    for tbl in [
        "perception",
        "state_estimation_pred_corr",
        "state_estimation_state",
        "state_estimation_map",
        "planning",
        "control"
    ]:
        cmd = f"""
            SELECT create_hypertable('{tbl}', 'time', if_not_exists => TRUE);
        """
        cur.execute(cmd)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Schema created and tables converted to hypertables.")

if __name__ == "__main__":
    setup_schema()
