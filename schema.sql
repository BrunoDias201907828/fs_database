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
    metric TEXT,
    metric_value REAL,
    PRIMARY KEY (time, run_id, metric)
);

-- state_estimation_pred_corr
CREATE TABLE IF NOT EXISTS state_estimation_pred_corr (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    metric TEXT,
    metric_value REAL,
    PRIMARY KEY (time, run_id, metric)
);

-- state_estimation_state
CREATE TABLE IF NOT EXISTS state_estimation_state (
    time       TIMESTAMPTZ NOT NULL,
    run_id     INT NOT NULL REFERENCES runs(run_id),
    x          DOUBLE PRECISION,
    y          DOUBLE PRECISION,
    theta      DOUBLE PRECISION,
    linear_velocity          DOUBLE PRECISION,
    angular_velocity      DOUBLE PRECISION,
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
    metric TEXT,
    metric_value REAL,
    PRIMARY KEY (time, run_id, metric)
);

-- control
CREATE TABLE IF NOT EXISTS control (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    throttle REAL,
    steering_angle REAL,
    PRIMARY KEY (time, run_id)
);

-- control metrics
CREATE TABLE IF NOT EXISTS control_metrics (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    lookahead_x REAL,
    lookahead_y REAL,
    closest_x REAL,
    closest_y REAL,
    linear_velocity REAL,
    closest_velocity REAL,
    execution_time REAL,
    PRIMARY KEY (time, run_id)
);

-- sensor data
CREATE TABLE IF NOT EXISTS sensor_data (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    metric         TEXT,
    metric_value        REAL,
    PRIMARY KEY (time, run_id, metric)
);

-- IMU acceleration
CREATE TABLE IF NOT EXISTS imu_acceleration (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    x_acceleration      REAL,
    y_acceleration      REAL,
    z_acceleration      REAL,
    PRIMARY KEY (time, run_id)
);

-- IMU angular velocity
CREATE TABLE IF NOT EXISTS imu_angular_velocity (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    x_angular_velocity  REAL,
    y_angular_velocity  REAL,
    z_angular_velocity  REAL,
    PRIMARY KEY (time, run_id)
);

-- IMU euler angles
CREATE TABLE IF NOT EXISTS imu_euler_angles (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    roll                REAL,
    pitch               REAL,
    yaw                 REAL,
    PRIMARY KEY (time, run_id)
);

-- IMU quaternion
CREATE TABLE IF NOT EXISTS imu_quaternion (
    time                TIMESTAMPTZ NOT NULL,
    run_id              INT NOT NULL REFERENCES runs(run_id),
    x                   REAL,
    y                   REAL,
    z                   REAL,
    w                   REAL,
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
SELECT create_hypertable('control_metrics', 'time', if_not_exists => TRUE);
SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

