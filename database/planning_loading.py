from connecting_db import get_db_connection
from datetime import datetime, timezone
from std_msgs.msg import Float64
from visualization_msgs.msg import MarkerArray

TOPIC_METRIC_MAPPING = {
    "/path_planning/execution_time": "execution_time",
    "/path_planning/yellow_cones": "num_yellow_cones",
    "/path_planning/blue_cones": "num_blue_cones",
    "/path_planning/after_rem_yellow_cones": "num_removed_yellow_cones",
    "/path_planning/after_rem_blue_cones": "num_removed_blue_cones",
}


def load_planning_data(run_id, topic, msg, timestamp):
    """
    Processes a planning topics and inserts data into the planning table.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic not in TOPIC_METRIC_MAPPING:
        print(f"Warning: Unknown topic {topic} for planning data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        if topic == "/path_planning/execution_time":
            metric_value = float(msg.data)
        elif topic in {
            "/path_planning/yellow_cones",
            "/path_planning/blue_cones",
            "/path_planning/after_rem_yellow_cones",
            "/path_planning/after_rem_blue_cones",
        }:
            if isinstance(msg, MarkerArray):
                metric_value = float(len(msg.markers))
            else:
                print(
                    f"Error: {topic} expected a MarkerArray message but got {type(msg)}"
                )
                return
        else:
            return

    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    metric_name = TOPIC_METRIC_MAPPING[topic]

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO planning (time, run_id, metric, metric_value)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (time, run_id, metric) DO NOTHING;
    """

    try:
        cur.execute(insert_query, (time_value, run_id, metric_name, metric_value))
        conn.commit()
        print(f"Inserted {metric_name} -> planning at {time_value} for run {run_id}")
    except Exception as e:
        print(f"Database insert error for planning at {timestamp}: {e}")
    finally:
        cur.close()
        conn.close()
