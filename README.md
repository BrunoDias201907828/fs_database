## WORK IN PROGRESS

1. **Start the Docker Containers**
   ```sh
   docker compose up
   ```

2. **Create the Database**
   ```sh
   python3 create_db.py
   ```

3. **Copy Required Files**
   - Copy the `database` folder and the `rosbag` file to the ROS workspace.

4. **Load the Database**
   ```sh
   python3 database/loading_db.py rosbag.mcap
   ```