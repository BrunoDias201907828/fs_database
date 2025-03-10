from connecting_db import get_db_connection
from datetime import datetime, timezone

TOPIC_TABLE_MAPPING = {
    "/imu/acceleration": "imu_acceleration",
    "/imu/angular_velocity": "imu_angular_velocity",
    "/filter/euler": "imu_euler_angles",
    "/filter/quaternion": "imu_quaternion",
}


def load_imu_data(run_id, topic, msg, timestamp):
    """
    Processes IMU-related topics and inserts them into their respective tables.

    :param run_id: The run ID associated with the data.
    :param topic: The topic name.
    :param msg: The message data.
    :param timestamp: The timestamp of the message.
    """
    if topic not in TOPIC_TABLE_MAPPING:
        print(f"Warning: Unknown topic {topic} for IMU data.")
        return

    # Convert timestamp to UTC (TIMESTAMPTZ format)
    time_value = datetime.fromtimestamp(timestamp / 1e9, tz=timezone.utc)

    try:
        if topic == "/imu/acceleration":
            x_acceleration = float(msg.vector.x)
            y_acceleration = float(msg.vector.y)
            z_acceleration = float(msg.vector.z)
            insert_query = """
            INSERT INTO imu_acceleration (time, run_id, x_acceleration, y_acceleration, z_acceleration)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (time, run_id) DO NOTHING;
            """
            values = (
                time_value,
                run_id,
                x_acceleration,
                y_acceleration,
                z_acceleration,
            )

        elif topic == "/imu/angular_velocity":
            x_angular_velocity = float(msg.vector.x)
            y_angular_velocity = float(msg.vector.y)
            z_angular_velocity = float(msg.vector.z)
            insert_query = """
            INSERT INTO imu_angular_velocity (time, run_id, x_angular_velocity, y_angular_velocity, z_angular_velocity)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (time, run_id) DO NOTHING;
            """
            values = (
                time_value,
                run_id,
                x_angular_velocity,
                y_angular_velocity,
                z_angular_velocity,
            )

        elif topic == "/filter/euler":
            roll = float(msg.vector.x)
            pitch = float(msg.vector.y)
            yaw = float(msg.vector.z)
            insert_query = """
            INSERT INTO imu_euler_angles (time, run_id, roll, pitch, yaw)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (time, run_id) DO NOTHING;
            """
            values = (time_value, run_id, roll, pitch, yaw)

        elif topic == "/filter/quaternion":
            x = float(msg.quaternion.x)
            y = float(msg.quaternion.y)
            z = float(msg.quaternion.z)
            w = float(msg.quaternion.w)
            insert_query = """
            INSERT INTO imu_quaternion (time, run_id, x, y, z, w)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, run_id) DO NOTHING;
            """
            values = (time_value, run_id, x, y, z, w)

        else:
            return

    except AttributeError as e:
        print(f"Error: Could not extract data from message on {topic}: {e}")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(insert_query, values)
        conn.commit()
        print(
            f"Inserted data into {TOPIC_TABLE_MAPPING[topic]} at {time_value} for run {run_id}"
        )
    except Exception as e:
        print(
            f"Database insert error for {TOPIC_TABLE_MAPPING[topic]} at {timestamp}: {e}"
        )
    finally:
        cur.close()
        conn.close()
