import argparse
import psycopg2
import os
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py

# Database Configuration
DB_CONFIG = {
    "dbname": "autonomous_db",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
}

# Define mappings for rosbag name prefixes to run types
RUN_TYPE_MAPPING = {
    "Hard_Course": "Hard Course",
    "Soft_Course": "Soft Course",
    "Simulation": "Simulation",
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def extract_value(msg, expected_type):
    """Converts message data to the expected type."""
    try:
        if expected_type == "INT":
            return int(msg)
        elif expected_type in ["DOUBLE PRECISION", "REAL"]:
            return float(msg)
        elif expected_type == "TEXT":
            return str(msg)
    except ValueError:
        return None
    return None

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
            start_time = timestamp  # First timestamp
        last_timestamp = timestamp  # Continuously update last timestamp

    return start_time / 1e9 if start_time else None, last_timestamp / 1e9 if last_timestamp else None

def get_run_type(run_name):
    """Determines the run type based on the rosbag file name prefix."""
    for prefix, run_type in RUN_TYPE_MAPPING.items():
        if run_name.startswith(prefix):
            return run_type
    return "Unknown"  # Default if no match is found

def insert_run(input_bag, slam_type=None, doc_url=None):
    """Inserts a new run and returns its run_id."""
    conn = get_db_connection()
    cur = conn.cursor()

    run_name = os.path.basename(input_bag).replace(".mcap", "")  # Extract filename without .mcap
    rosbag_path = os.path.abspath(input_bag)  # Full path of the rosbag
    start_time, end_time = get_rosbag_start_end_time(input_bag)  # Get timestamps
    run_type = get_run_type(run_name)  # Determine run type

    if start_time is None:
        print("Error: Could not determine start time from rosbag.")
        return None

    cur.execute("""
        INSERT INTO runs (run_name, start_time, end_time, slam_type, rosbag_path, run_type, doc_url) 
        VALUES (%s, %s, %s, %s, %s, %s, %s) 
        RETURNING run_id
    """, (run_name, start_time, end_time, slam_type, rosbag_path, run_type, doc_url))

    run_id = cur.fetchone()[0]  # Fetch generated run_id using RETURNING
    conn.commit()
    cur.close()
    conn.close()
    print(f"Created run {run_id} with name '{run_name}', run type '{run_type}', start time {start_time}, end time {end_time}")
    return run_id

def read_messages(input_bag, topics):
    """Reads specific topics from a rosbag file."""
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=input_bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    topic_types = reader.get_all_topics_and_types()

    def typename(topic_name):
        for topic_type in topic_types:
            if topic_type.name == topic_name:
                return topic_type.type
        return None

    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        if topic in topics:
            try:
                msg_type = get_message(typename(topic))
                msg = deserialize_message(data, msg_type)
                yield topic, msg, timestamp
            except Exception as e:
                print(f"Deserialization failed for {topic} at {timestamp}: {e}")

def insert_data(table_name, topic_col_mapping, input_bag, run_id):
    """Reads ROS topics and inserts data into the corresponding table."""
    conn = get_db_connection()
    cur = conn.cursor()

    topics = list(topic_col_mapping.keys())
    columns = list(topic_col_mapping.values())

    insert_query = f"""
    INSERT INTO {table_name} (time, run_id, {', '.join(columns)}) 
    VALUES (%s, %s, {', '.join(['%s'] * len(columns))});
    """

    column_types = {
        "num_objects": "INT",
        "detection_conf": "REAL",
        "x": "DOUBLE PRECISION",
        "y": "DOUBLE PRECISION",
        "vx": "DOUBLE PRECISION",
        "vy": "DOUBLE PRECISION",
        "steering_angle": "REAL",
        "throttle": "REAL"
    }

    for topic, msg, timestamp in read_messages(input_bag, topics):
        try:
            data_values = [None] * len(columns)
            column_index = topics.index(topic)
            data_values[column_index] = extract_value(msg, column_types[columns[column_index]])

            cur.execute(insert_query, [timestamp / 1e9, run_id] + data_values)
            conn.commit()
            print(f"Inserted {topic} -> {table_name} at {timestamp}")

        except Exception as e:
            print(f"Database insert error for {topic} in {table_name} at {timestamp}: {e}")

    cur.close()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Read rosbag and populate TimescaleDB tables")
    parser.add_argument("input", help="Path to input rosbag file")
    parser.add_argument("--slam_type", help="Specify SLAM type (default: None)", default=None)
    parser.add_argument("--doc_url", help="Documentation URL (optional)", default=None)

    args = parser.parse_args()

    run_id = insert_run(args.input, args.slam_type, args.doc_url)
    # if run_id is None:
    #     print("Error: Could not create run. Exiting.")
    #     return

    # table_mappings = {
    #     "perception": {"/perception/objects": "num_objects", "/perception/conf": "detection_conf"},
    #     "state_estimation_state": {"/state/x": "x", "/state/y": "y"}
    # }

    # for table, topic_mapping in table_mappings.items():
    #     insert_data(table, topic_mapping, args.input, run_id)

if __name__ == "__main__":
    main()
