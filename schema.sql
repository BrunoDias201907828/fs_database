-- Enable the TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- runs (metadata table)
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

-- perception
CREATE TABLE IF NOT EXISTS perception (
    time              TIMESTAMPTZ NOT NULL,
    run_id            INT NOT NULL REFERENCES runs(run_id),
    num_objects       INT,
    detection_conf    REAL,
    metric_1          REAL,
    metric_2          REAL,
    PRIMARY KEY (time, run_id)
);

-- state_estimation_pred_corr
CREATE TABLE IF NOT EXISTS state_estimation_pred_corr (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    prediction_error    REAL,
    correction_error    REAL,
    PRIMARY KEY (time, run_id)
);

-- state_estimation_state
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

-- state_estimation_map
CREATE TABLE IF NOT EXISTS state_estimation_map (
    time          TIMESTAMPTZ NOT NULL,
    run_id        INT NOT NULL REFERENCES runs(run_id),
    map_metric_1  REAL,
    map_metric_2  REAL,
    PRIMARY KEY (time, run_id)
);

-- planning
CREATE TABLE IF NOT EXISTS planning (
    time              TIMESTAMPTZ NOT NULL,
    run_id            INT NOT NULL REFERENCES runs(run_id),
    size_yellow_cone  REAL,
    size_blue_cones   REAL,
    PRIMARY KEY (time, run_id)
);

-- control
CREATE TABLE IF NOT EXISTS control (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    steering_angle      REAL,
    throttle            REAL,
    PRIMARY KEY (time, run_id)
);

-- vehicle_data
CREATE TABLE IF NOT EXISTS vehicle_data (
    vehicle_config_id          SERIAL PRIMARY KEY,
    start_time                 TIMESTAMPTZ NOT NULL,
    end_time                   TIMESTAMPTZ,
    vehicle_name               TEXT,
    gear_ratio                 REAL,
    tire_type                  TEXT,
    tire_pressure              REAL
);

-- perception_parameters
CREATE TABLE IF NOT EXISTS perception_parameters (
    perception_param_id SERIAL PRIMARY KEY,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    param_1             INT NOT NULL,
    param_2             INT NOT NULL                
);

-- state_estimation_parameters
CREATE TABLE IF NOT EXISTS state_estimation_parameters (
    state_est_param_id  SERIAL PRIMARY KEY,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    param_1             INT NOT NULL,
    param_2             INT NOT NULL        
);

-- planning_parameters
CREATE TABLE IF NOT EXISTS planning_parameters (
    planning_param_id   SERIAL PRIMARY KEY,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    param_1             INT NOT NULL,
    param_2             INT NOT NULL        
);

-- control_parameters
CREATE TABLE IF NOT EXISTS control_parameters (
    control_param_id    SERIAL PRIMARY KEY,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    param_1             INT NOT NULL,
    param_2             INT NOT NULL        
);

-- Convert certain tables to hypertables
SELECT create_hypertable('perception', 'time', if_not_exists => TRUE);
SELECT create_hypertable('state_estimation_pred_corr', 'time', if_not_exists => TRUE);
SELECT create_hypertable('state_estimation_state', 'time', if_not_exists => TRUE);
SELECT create_hypertable('state_estimation_map', 'time', if_not_exists => TRUE);
SELECT create_hypertable('planning', 'time', if_not_exists => TRUE);
SELECT create_hypertable('control', 'time', if_not_exists => TRUE);
