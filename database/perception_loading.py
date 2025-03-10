from connecting_db import get_db_connection
from datetime import datetime, timezone
from std_msgs.msg import Float64
from custom_interfaces.msg import Cone, ConeArray

TOPIC_METRIC_MAPPING = {
    "/perception/execution_time": "execution_time",
    "/perception/cones": "num_cones",
}

def load_perception_data(run_id, topic, msg, timestamp):
    """
    Processes a perception topics and inserts data into the perception table.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic not in TOPIC_METRIC_MAPPING:
        print(f"Warning: Unknown topic {topic} for perception data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    if topic == "/perception/execution_time":
        metric_value = float(msg.data)
    elif topic == "/perception/cones":
        metric_value = float(len(msg.cone_array))
    else:
        return

    metric_name = TOPIC_METRIC_MAPPING[topic]

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO perception (time, run_id, metric, metric_value)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (time, run_id, metric) DO NOTHING;
    """

    try:
        cur.execute(insert_query, (time_value, run_id, metric_name, metric_value))
        conn.commit()
        print(f"Inserted {metric_name} -> perception at {time_value} for run {run_id}")
    except Exception as e:
        print(f"Database insert error for perception at {timestamp}: {e}")
    finally:
        cur.close()
        conn.close()
