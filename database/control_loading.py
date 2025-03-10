from connecting_db import get_db_connection
from datetime import datetime, timezone


def load_control_metrics_data(run_id, topic, msg, timestamp):
    """
    Processes /control/evaluator_data and inserts all extracted metrics into control_metrics.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic != "/control/evaluator_data":
        print(f"Warning: Unknown topic {topic} for control metrics.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        lookahead_x = float(msg.lookahead_point.x)
        lookahead_y = float(msg.lookahead_point.y)
        closest_x = float(msg.closest_point.x)
        closest_y = float(msg.closest_point.y)
        linear_velocity = float(msg.lookahead_velocity)
        closest_velocity = float(msg.closest_point_velocity)
        execution_time = float(msg.execution_time)

    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO control_metrics (time, run_id, lookahead_x, lookahead_y, closest_x, closest_y, 
                                 linear_velocity, closest_velocity, execution_time)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (time, run_id) DO UPDATE 
    SET lookahead_x = EXCLUDED.lookahead_x,
        lookahead_y = EXCLUDED.lookahead_y,
        closest_x = EXCLUDED.closest_x,
        closest_y = EXCLUDED.closest_y,
        linear_velocity = EXCLUDED.linear_velocity,
        closest_velocity = EXCLUDED.closest_velocity,
        execution_time = EXCLUDED.execution_time;
    """

    try:
        cur.execute(
            insert_query,
            (
                time_value,
                run_id,
                lookahead_x,
                lookahead_y,
                closest_x,
                closest_y,
                linear_velocity,
                closest_velocity,
                execution_time,
            ),
        )
        conn.commit()
        print(f"Inserted control metrics at {time_value} for run {run_id}")
    except Exception as e:
        print(f"Database insert error for control_metrics at {timestamp}: {e}")
    finally:
        cur.close()
        conn.close()


def load_control_data(run_id, topic, msg, timestamp):
    """
    Processes /as_msgs/controls and inserts extracted data into the control table.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic != "/as_msgs/controls":
        print(f"Warning: Unknown topic {topic} for control data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        throttle = float(msg.throttle)
        steering_angle = float(msg.steering)
    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    insert_query = """
    INSERT INTO control (time, run_id, throttle, steering_angle)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (time, run_id) DO NOTHING;
    """

    try:
        cur.execute(insert_query, (time_value, run_id, throttle, steering_angle))
        conn.commit()
        print(f"Inserted control data at {time_value} for run {run_id}")
    except Exception as e:
        print(f"Database insert error for control at {timestamp}: {e}")
    finally:
        cur.close()
        conn.close()
