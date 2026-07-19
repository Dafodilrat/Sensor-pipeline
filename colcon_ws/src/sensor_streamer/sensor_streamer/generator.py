#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor  # Still needed for parallel execution
from std_msgs.msg import Int32, Float32
import math
import random
import time

class SyntheticDataNode(Node):
    def __init__(self):
        super().__init__('synthetic_sensor')

        # Declare parameters (values will be loaded from YAML)
        self.declare_parameter('amplitudes', [1.0, 0.5])
        self.declare_parameter('frequencies', [1.0, 2.0])
        self.declare_parameter('phases', [0.0, math.pi/2])
        self.declare_parameter('wheel_circumference', 0.203)
        self.declare_parameter('counts_per_revolution', 4096)
        self.declare_parameter('imu.rate', 200.0)
        self.declare_parameter('imu.noise_std', 0.05)
        self.declare_parameter('imu.drop_rate', 0.005)
        self.declare_parameter('imu.jitter_range', 0.1)
        self.declare_parameter('encoder.rate', 50.0)
        self.declare_parameter('encoder.drop_rate', 0.01)
        self.declare_parameter('encoder.jitter_range', 0.15)

        # Load parameters from YAML (no hardcoded values)
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
        self.encoder_jitter_range = self.get_parameter('encoder.drop_rate').get_parameter_value().double_value

        # State
        self.t0 = time.time()
        self.imu_prev_time = self.t0
        self.imu_prev_velocity = 0.0
        self.encoder_prev_time = self.t0
        self.encoder_position = 0.0
        
        # Publishers
        self.encoder_pub = self.create_publisher(Int32, 'encoder_count', 10)
        self.imu_pub = self.create_publisher(Float32, 'accel_x_mss', 10)
        
        # Timers
        self.imu_timer = self.create_timer(1.0 / self.imu_rate, self.publish_imu)
        self.encoder_timer = self.create_timer(1.0 / self.encoder_rate, self.publish_encoder)

    def velocity(self, t):
        """Pure function - computes velocity from motion model (no side effects)."""
        v = 0.0
        for A, f, phi in zip(self.amplitudes, self.frequencies, self.phases):
            v += A * math.sin(2 * math.pi * f * t + phi)
        return v

    def publish_imu(self):
        current_time = time.time()
        t = current_time - self.t0
        dt = current_time - self.imu_prev_time

        # Compute current velocity (analytic)
        current_vel = self.velocity(t)

        # Numerical acceleration (using IMU's own previous state)
        acceleration = (current_vel - self.imu_prev_velocity) / dt if dt > 0 else 0.0

        # Dropout
        if random.random() < self.imu_drop_rate:
            return

        # Add noise and publish
        imu_accel = acceleration + random.gauss(0, self.imu_noise_std)
        self.imu_pub.publish(Float32(data=float(imu_accel)))

        # Jitter
        if self.imu_jitter_range > 0:
            time.sleep(random.uniform(0, self.imu_jitter_range / self.imu_rate))

        # Update IMU state
        self.imu_prev_velocity = current_vel
        self.imu_prev_time = current_time

    def publish_encoder(self):
        
        current_time = time.time()
        t = current_time - self.t0
        dt = current_time - self.encoder_prev_time

        # Compute current velocity (analytic)
        current_vel = self.velocity(t)

        # Numerical position integration (using encoder's own previous state)
        self.encoder_position += current_vel * dt

        # Dropout
        if random.random() < self.encoder_drop_rate:
            return

        # Convert and publish
        rotations = self.encoder_position / self.wheel_circumference
        encoder_count = int(rotations * self.counts_per_revolution)
        self.encoder_pub.publish(Int32(data=encoder_count))

        # Jitter
        if self.encoder_jitter_range > 0:
            time.sleep(random.uniform(0, self.encoder_jitter_range / self.encoder_rate))

        # Update encoder state
        self.encoder_prev_time = current_time


def main(args=None):
    
    import sys
    from ament_index_python.packages import get_package_share_directory
    import os
    
    # Check for --config flag before ROS2 initialization
    if '--config' in sys.argv:
        idx = sys.argv.index('--config')
        if idx + 1 >= len(sys.argv):
            print("Warning: No file path provided after --config flag. Falling back to default values.")
            # Remove --config flag
            del sys.argv[idx]
        else:
            config_file = sys.argv[idx + 1]
            # Replace --config with --ros-args --params-file for ROS2 parameter loading
            sys.argv[idx] = '--ros-args'
            sys.argv[idx + 1] = '--params-file'
            sys.argv.insert(idx + 2, config_file)
    else:
        # No --config specified, use default config from package
        pkg_share_dir = get_package_share_directory('sensor_streamer')
        default_config = os.path.join(pkg_share_dir, 'config', 'synthetic_params.yaml')
        if os.path.exists(default_config):
            # Insert default config as params-file
            sys.argv.append('--ros-args')
            sys.argv.append('--params-file')
            sys.argv.append(default_config)
    
    rclpy.init(args=args)
    node = SyntheticDataNode()

    # Use MultiThreadedExecutor for parallel callbacks
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
