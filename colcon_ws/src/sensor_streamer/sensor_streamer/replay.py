import csv
import time
import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import argparse

class ReplayDataNode(Node):
    def __init__(self, csv_file, jitter=False, drop_rate=0.0):
        super().__init__('replay_data_node')
        self.csv_file = csv_file
        self.jitter = jitter
        self.drop_rate = drop_rate

        # Publishers
        self.encoder_pub = self.create_publisher(Int32, 'encoder_count', 10)
        self.imu_pub = self.create_publisher(Float32, 'accel_x_mss', 10)

        # Load CSV data
        self.data = self.load_csv()

        # Start replay
        self.start_time = time.time()
        self.index = 0
        self.timer = self.create_timer(0.005, self.publish_replay_data)  # 200 Hz timer

    def load_csv(self):
        data = []
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'timestamp': float(row['timestamp']),
                    'encoder_count': int(row['encoder_count']),
                    'accel_x_mss': float(row['accel_x_mss'])
                })
        return data

    def publish_replay_data(self):
        if self.index >= len(self.data):
            self.timer.cancel()
            return

        current_time = time.time() - self.start_time
        target_time = self.data[self.index]['timestamp']

        # Skip if not yet time to publish this sample
        if current_time < target_time:
            return

        # Skip based on drop_rate
        if random.random() < self.drop_rate:
            self.index += 1
            return

        # Add jitter to the publish time
        if self.jitter:
            time.sleep(random.uniform(-0.001, 0.001))  # ±1ms jitter for 200 Hz data

        # Publish the data
        self.encoder_pub.publish(Int32(data=self.data[self.index]['encoder_count']))
        self.imu_pub.publish(Float32(data=self.data[self.index]['accel_x_mss']))

        self.index += 1

def main(args=None):
    rclpy.init(args=args)

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv-file', type=str, required=True,
                        help='Path to the CSV file to replay')
    parser.add_argument('--jitter', action='store_true',
                        help='Introduce randomized timing jitter')
    parser.add_argument('--drop-rate', type=float, default=0.0,
                        help='Probability of dropping a sample (0 to 1)')
    args, unknown = parser.parse_known_args()

    # Create node
    node = ReplayDataNode(
        csv_file=args.csv_file,
        jitter=args.jitter,
        drop_rate=args.drop_rate
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()