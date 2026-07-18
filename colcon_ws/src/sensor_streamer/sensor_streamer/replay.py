#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import csv
import os
import time
import argparse

class CSVReplayNode(Node):
    def __init__(self, csv_path):
        super().__init__('csv_replay_node')
        self.csv_path = csv_path

        # Publishers
        self.encoder_pub = self.create_publisher(Int32, '/encoder_count', 10)
        self.accel_pub = self.create_publisher(Float32, '/accel_x_mss', 10)
        self.timestamp_pub = self.create_publisher(Float32, '/timestamp', 10)

        # Load CSV data
        self.data = self.load_csv()
        self.start_time = None

        # Timer (placeholder, actual timing handled in replay loop)
        self.timer = self.create_timer(0.1, self.replay_loop)

    def load_csv(self):
        data = []
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'timestamp_s': float(row['timestamp_s']),
                    'encoder_count': int(row['encoder_count']),
                    'accel_x_mss': float(row['accel_x_mss'])
                })
        return data

    def replay_loop(self):
        if not self.data:
            self.get_logger().warn("No data loaded from CSV.")
            return

        if self.start_time is None:
            self.start_time = time.time()

        current_time = time.time() - self.start_time
        tolerance = 0.001 

        for row in self.data:
            target_time = row['timestamp_s']
            sleep_time = target_time - current_time

            if sleep_time > 0:
                sleep_time = max(sleep_time - tolerance, 0.0)  # Ensure non-negative
                time.sleep(sleep_time)
                current_time = time.time() - self.start_time

            # Publish data
            self.encoder_pub.publish(Int32(data=row['encoder_count']))
            self.accel_pub.publish(Float32(data=row['accel_x_mss']))
            self.timestamp_pub.publish(Float32(data=row['timestamp_s']))

        # Stop after replaying once
        self.timer.cancel()
        self.get_logger().info("Replay complete.")

def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser()
    parser.add_argument('--replay', action='store_true', help='Enable replay mode')
    args, unknown = parser.parse_known_args()

    if not args.replay:
        parser.error("--replay flag is required to run this node.")

    csv_path = os.path.join(os.path.dirname(__file__), 'confidential', 'sensor_log.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    node = CSVReplayNode(csv_path)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()