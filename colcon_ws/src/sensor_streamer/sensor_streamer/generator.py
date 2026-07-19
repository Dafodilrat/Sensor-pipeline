#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import math
import random
import time

class SyntheticDataNode(Node):
    def __init__(self):
        super().__init__('synthetic_data_node')

        # === SHARED MOTION PARAMETERS ===
        self.declare_parameter('amplitudes', [1.0, 0.5])
        self.declare_parameter('frequencies', [1.0, 2.0])
        self.declare_parameter('phases', [0.0, math.pi/2])
        self.declare_parameter('wheel_circumference', 0.203)
        self.declare_parameter('counts_per_revolution', 4096)

        # === IMU PARAMETERS ===
        self.declare_parameter('imu/rate', 200.0)
        self.declare_parameter('imu/noise_std', 0.05)
        self.declare_parameter('imu/drop_rate', 0.005)
        self.declare_parameter('imu/jitter_range', 0.1)

        # === ENCODER PARAMETERS ===
        self.declare_parameter('encoder/rate', 50.0)
        self.declare_parameter('encoder/drop_rate', 0.01)
        self.declare_parameter('encoder/jitter_range', 0.15)

        # Load parameters
        self.amplitudes = self.get_parameter('amplitudes').get_parameter_value().double_array_value
        self.frequencies = self.get_parameter('frequencies').get_parameter_value().double_array_value
        self.phases = self.get_parameter('phases').get_parameter_value().double_array_value
        self.wheel_circumference = self.get_parameter('wheel_circumference').get_parameter_value().double_value
        self.counts_per_revolution = self.get_parameter('counts_per_revolution').get_parameter_value().integer_value

        self.imu_rate = self.get_parameter('imu.rate').get_parameter_value().double_value
        self.imu_noise_std = self.get_parameter('imu.noise_std').get_parameter_value().double_value
        self.imu_drop_rate = self.get_parameter('imu.drop_rate').get_parameter_value().double_value
        self.imu_jitter_range = self.get_parameter('imu.jitter_range').get_parameter_value().double_value

        self.encoder_rate = self.get_parameter('encoder.rate').get_parameter_value().double_value
        self.encoder_drop_rate = self.get_parameter('encoder.drop_rate').get_parameter_value().double_value
        self.encoder_jitter_range = self.get_parameter('encoder.jitter_range').get_parameter_value().double_value

        # === STATE (shared ground truth) ===
        self.t0 = time.time()
        self.prev_time = self.t0
        self.prev_velocity = 0.0
        self.position = 0.0

        # === PUBLISHERS ===
        self.encoder_pub = self.create_publisher(Int32, 'encoder_count', 10)
        self.imu_pub = self.create_publisher(Float32, 'accel_x_mss', 10)

        # === SEPARATE TIMERS ===
        self.imu_timer = self.create_timer(1.0 / self.imu_rate, self.publish_imu)
        self.encoder_timer = self.create_timer(1.0 / self.encoder_rate, self.publish_encoder)

    def get_ground_truth(self):
        """Compute current velocity and position from motion model."""
        current_time = time.time()
        t = current_time - self.t0  # Time since node start

        # Ground truth velocity
        current_velocity = 0.0
        for A, f, phi in zip(self.amplitudes, self.frequencies, self.phases):
            current_velocity += A * math.sin(2 * math.pi * f * t + phi)

        # Numerical acceleration
        dt = current_time - self.prev_time
        acceleration = (current_velocity - self.prev_velocity) / dt if dt > 0 else 0.0

        # Numerical position integration
        self.position += current_velocity * dt

        # Update state
        self.prev_velocity = current_velocity
        self.prev_time = current_time

        return current_velocity, acceleration, self.position

    def publish_imu(self):
        current_velocity, acceleration, _ = self.get_ground_truth()

        # Dropout
        if random.random() < self.imu_drop_rate:
            return

        # Add IMU-specific noise
        imu_accel = acceleration + random.gauss(0, self.imu_noise_std)

        # Jitter
        if self.imu_jitter_range > 0:
            time.sleep(random.uniform(0, self.imu_jitter_range / self.imu_rate))

        self.imu_pub.publish(Float32(data=float(imu_accel)))

    def publish_encoder(self):
        _, _, position = self.get_ground_truth()

        # Dropout
        if random.random() < self.encoder_drop_rate:
            return

        # Convert to encoder counts
        rotations = position / self.wheel_circumference
        encoder_count = int(rotations * self.counts_per_revolution)

        # Jitter
        if self.encoder_jitter_range > 0:
            time.sleep(random.uniform(0, self.encoder_jitter_range / self.encoder_rate))

        self.encoder_pub.publish(Int32(data=encoder_count))

def main(args=None):
    rclpy.init(args=args)
    node = SyntheticDataNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()