from connecting_db import get_db_connection
from datetime import datetime, timezone

# Topic to Metric Name Mapping
TOPIC_METRIC_MAPPING = {
    "/vehicle/rl_rpm": "rl_rpm",
    "/vehicle/rr_rpm": "rr_rpm",
    "/vehicle/bosch_steering_angle": "steering_angle",
}


def load_sensor_data(run_id, topic, msg, timestamp):
    """
    Processes sensor data topics and inserts them into the sensor_data table.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic not in TOPIC_METRIC_MAPPING:
        print(f"Warning: Unknown topic {topic} for sensor data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        if topic == "/vehicle/rl_rpm":
            metric_value = float(msg.rl_rpm)
        elif topic == "/vehicle/rr_rpm":
            metric_value = float(msg.rr_rpm)
        elif topic == "/vehicle/bosch_steering_angle":
            metric_value = float(msg.steering_angle)
        else:
            return

    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    metric_name = TOPIC_METRIC_MAPPING[topic]

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO sensor_data (time, run_id, metric, metric_value)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (time, run_id, metric) DO NOTHING;
    """

    try:
        cur.execute(insert_query, (time_value, run_id, metric_name, metric_value))
        conn.commit()
        print(f"Inserted {metric_name} -> sensor_data at {time_value} for run {run_id}")
    except Exception as e:
        print(f"Database insert error for sensor_data at {timestamp}: {e}")
    finally:
        cur.close()
        conn.close()
