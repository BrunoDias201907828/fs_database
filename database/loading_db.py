from runs_loading import insert_run
from message_dispatcher import process_rosbag
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Read rosbag and populate TimescaleDB tables"
    )
    parser.add_argument("input", help="Path to input rosbag file")
    parser.add_argument(
        "--slam_type", help="Specify SLAM type (default: None)", default=None
    )
    parser.add_argument("--doc_url", help="Documentation URL (optional)", default=None)

    args = parser.parse_args()

    run_id = insert_run(args.input, args.slam_type, args.doc_url)

    if run_id is not None:
        process_rosbag(args.input, run_id)


if __name__ == "__main__":
    main()
