from perception_loading import load_perception_data
from state_est_loading import (
    load_state_estimation_pred_corr_data,
    load_state_estimation_state_data,
)
from planning_loading import load_planning_data
from control_loading import load_control_metrics_data, load_control_data
from sensor_loading import load_sensor_data
from imu_loading import load_imu_data

TOPIC_TO_LOADER = {
    "/perception/execution_time": load_perception_data,
    "/perception/cones": load_perception_data,
    "/state_estimation/execution_time/correction_step": load_state_estimation_pred_corr_data,
    "/state_estimation/execution_time/prediction_step": load_state_estimation_pred_corr_data,
    "/state_estimation/vehicle_state": load_state_estimation_state_data,
    "/path_planning/execution_time": load_planning_data,
    "/path_planning/yellow_cones": load_planning_data,
    "/path_planning/blue_cones": load_planning_data,
    "/path_planning/after_rem_yellow_cones": load_planning_data,
    "/path_planning/after_rem_blue_cones": load_planning_data,
    "/control/evaluator_data": load_control_metrics_data,
    "/as_msgs/controls": load_control_data,
    "/vehicle/rl_rpm": load_sensor_data,
    "/vehicle/rr_rpm": load_sensor_data,
    "/vehicle/bosch_steering_angle": load_sensor_data,
    "/imu/acceleration": load_imu_data,
    "/imu/angular_velocity": load_imu_data,
    "/filter/euler": load_imu_data,
    "/filter/quaternion": load_imu_data,
}


def process_rosbag(input_bag, run_id):
    """
    Reads messages from the rosbag and routes them to the correct loader.

    :param input_bag: Path to the rosbag file.
    :param run_id: The run ID associated with the data.
    """
    from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    reader = SequentialReader()
    reader.open(
        StorageOptions(uri=input_bag, storage_id="mcap"),
        ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    topic_types = reader.get_all_topics_and_types()

    def get_msg_type(topic_name):
        for topic_type in topic_types:
            if topic_type.name == topic_name:
                return topic_type.type
        return None

    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        if topic in TOPIC_TO_LOADER:
            try:
                msg_type = get_message(get_msg_type(topic))
                msg = deserialize_message(data, msg_type)
                TOPIC_TO_LOADER[topic](run_id, topic, msg, timestamp)
            except Exception as e:
                print(f"Error processing topic {topic} at {timestamp}: {e}")
