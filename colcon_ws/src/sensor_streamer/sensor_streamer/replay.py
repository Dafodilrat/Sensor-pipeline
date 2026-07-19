import csv
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import sys
import os

class ReplayDataNode(Node):
    def __init__(self, csv_file):
        super().__init__('replay_data_node')
        self.csv_file = csv_file

        # Publishers
        self.encoder_pub = self.create_publisher(Int32, 'encoder_count', 10)
        self.imu_pub = self.create_publisher(Float32, 'accel_x_mss', 10)

        # Load CSV data
        self.data = self.load_csv()
        
        self.get_logger().info(f"Replay started with {len(self.data)} samples from {self.csv_file}")

        # Start replay
        self.start_time = time.time()
        self.index = 0
        self.timer = self.create_timer(0.005, self.publish_replay_data)  # 200 Hz timer

    def load_csv(self):
        data = []
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            # Check that required columns exist
            if reader.fieldnames is None:
                raise ValueError(f"CSV file {self.csv_file} has no header row")
            
            # Debug: print available columns
            self.get_logger().info(f"CSV columns: {reader.fieldnames}")
            
            # Find column names (case-insensitive)
            headers_lower = [h.lower() for h in reader.fieldnames]
            
            # Map expected columns to actual column names
            col_map = {}
            for expected, possible_names in [
                ('timestamp', ['timestamp', 'timestamp_s', 'time', 't']),
                ('encoder_count', ['encoder_count', 'encoder', 'count']),
                ('accel_x_mss', ['accel_x_mss', 'accel_x', 'acceleration', 'accel'])
            ]:
                for name in possible_names:
                    if name in headers_lower:
                        idx = headers_lower.index(name)
                        col_map[expected] = reader.fieldnames[idx]
                        break
                else:
                    raise ValueError(
                        f"CSV file {self.csv_file} missing required column '{expected}'. "
                        f"Available columns: {reader.fieldnames}. "
                        f"Expected one of: {possible_names}"
                    )
            
            # Debug: print column mapping
            self.get_logger().info(f"Column mapping: {col_map}")
            
            # Read data using mapped column names
            for row in reader:
                data.append({
                    'timestamp': float(row[col_map['timestamp']]),
                    'encoder_count': int(row[col_map['encoder_count']]),
                    'accel_x_mss': float(row[col_map['accel_x_mss']])
                })
        return data

    def publish_replay_data(self):
        if self.index >= len(self.data):
            self.get_logger().info("Reached end of data")
            self.timer.cancel()
            return

        current_time = time.time() - self.start_time
        target_time = self.data[self.index]['timestamp']

        # Skip if not yet time to publish this sample
        if current_time < target_time:
            return

        # Publish the data
        self.encoder_pub.publish(Int32(data=self.data[self.index]['encoder_count']))
        self.imu_pub.publish(Float32(data=self.data[self.index]['accel_x_mss']))

        self.index += 1

def main(args=None):
    # CSV file path is passed as argument
    # Extract it from sys.argv (ROS2 strips --ros-args but keeps others)
    csv_file = None
    
    # Look for --replay flag
    if '--replay' in sys.argv:
        idx = sys.argv.index('--replay')
        if idx + 1 < len(sys.argv):
            csv_file = sys.argv[idx + 1]
    
    if csv_file is None:
        print("Error: CSV file path not provided after --replay flag")
        print("Usage: ros2 run sensor_streamer replay --replay <csv_file_path>")
        sys.exit(1)
    
    # Check if file exists
    if not os.path.isfile(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
    
    rclpy.init(args=args)
    
    node = None
    try:
        # Create node
        node = ReplayDataNode(csv_file=csv_file)
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error loading CSV or running node: {e}")
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()