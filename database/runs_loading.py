import os
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py
from datetime import datetime, timezone
from connecting_db import get_db_connection

RUN_TYPE_MAPPING = {
    "Hard_Course": "Hard Course",
    "EBS_Test": "EBS Test",
    "Closed_Course": "Closed Course",
    "Aceleration": "Acceleration",
}


def get_rosbag_start_end_time(input_bag):
    """Gets the first and last timestamp in the rosbag."""
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=input_bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    start_time = None
    last_timestamp = None

    while reader.has_next():
        _, _, timestamp = reader.read_next()
        if start_time is None:
            start_time = timestamp
        last_timestamp = timestamp

    return start_time / 1e9 if start_time else None, (
        last_timestamp / 1e9 if last_timestamp else None
    )


def get_run_type(run_name):
    """Determines the run type based on the rosbag file name prefix."""
    for prefix, run_type in RUN_TYPE_MAPPING.items():
        if run_name.startswith(prefix):
            return run_type
    return "Unknown"


def insert_run(input_bag, slam_type=None, doc_url=None):
    """Inserts a new run and returns its run_id."""
    conn = get_db_connection()
    cur = conn.cursor()

    run_name = os.path.basename(input_bag).replace(".mcap", "")
    rosbag_path = os.path.abspath(input_bag)
    start_time, end_time = get_rosbag_start_end_time(input_bag)
    run_type = get_run_type(run_name)

    if start_time is None:
        print("Error: Could not determine start time from rosbag.")
        return None

    # Convert numeric timestamp to TIMESTAMPTZ format
    start_time = datetime.fromtimestamp(start_time, tz=timezone.utc)
    end_time = datetime.fromtimestamp(end_time, tz=timezone.utc) if end_time else None

    cur.execute(
        """
        INSERT INTO runs (run_name, start_time, end_time, slam_type, rosbag_path, run_type, doc_url) 
        VALUES (%s, %s, %s, %s, %s, %s, %s) 
        RETURNING run_id
    """,
        (run_name, start_time, end_time, slam_type, rosbag_path, run_type, doc_url),
    )

    run_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    print(
        f"Created run {run_id} with name '{run_name}', run type '{run_type}', start time {start_time}, end time {end_time}"
    )
    return run_id
