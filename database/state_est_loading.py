from connecting_db import get_db_connection
from datetime import datetime, timezone
from custom_interfaces.msg import VehicleState


TOPIC_METRIC_MAPPING = {
    "/state_estimation/execution_time/correction_step": "correction_step",
    "/state_estimation/execution_time/prediction_step": "prediction_step",
}


def load_state_estimation_pred_corr_data(run_id, topic, msg, timestamp):
    """
    Processes a state estimation pred_corr data and inserts data into the state_estimation_pred_corr table.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic not in TOPIC_METRIC_MAPPING:
        print(f"Warning: Unknown topic {topic} for state estimation pred/corr data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        metric_value = float(msg.data)
    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    metric_name = TOPIC_METRIC_MAPPING[topic]

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO state_estimation_pred_corr (time, run_id, metric, metric_value)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (time, run_id, metric) DO NOTHING;
    """

    try:
        cur.execute(insert_query, (time_value, run_id, metric_name, metric_value))
        conn.commit()
        print(
            f"Inserted {metric_name} -> state_estimation_pred_corr at {time_value} for run {run_id}"
        )
    except Exception as e:
        print(
            f"Database insert error for state_estimation_pred_corr at {timestamp}: {e}"
        )
    finally:
        cur.close()
        conn.close()


def load_state_estimation_state_data(run_id, topic, msg, timestamp):
    """
    Processes the vehicle_state topic and inserts data into the state_estimation_state table.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic != "/state_estimation/vehicle_state":
        print(f"Warning: Unknown topic {topic} for state estimation state data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        x = float(msg.position.x)
        y = float(msg.position.y)
        theta = float(msg.theta)
        linear_velocity = float(msg.linear_velocity)
        angular_velocity = float(msg.angular_velocity)

    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO state_estimation_state (time, run_id, x, y, theta, linear_velocity, angular_velocity)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (time, run_id) DO NOTHING;
    """

    try:
        cur.execute(
            insert_query,
            (time_value, run_id, x, y, theta, linear_velocity, angular_velocity),
        )
        conn.commit()
        print(f"Inserted state estimation data at {time_value} for run {run_id}")
    except Exception as e:
        print(f"Database insert error for state_estimation_state at {timestamp}: {e}")
    finally:
        cur.close()
        conn.close()
