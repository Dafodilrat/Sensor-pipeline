#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import math
import random
import time
import numpy as np


class SyntheticDataNode(Node):
    """Synthetic data generator node that publishes IMU and encoder data."""
    
    def __init__(self):
        super().__init__('synthetic_sensor')

        # Declare parameters - all values should come from launch file or config
        self.declare_parameter('amplitudes', [1.0, 0.5])
        self.declare_parameter('frequencies', [1.0, 2.0])
        self.declare_parameter('phases', [0.0, math.pi/2])
        self.declare_parameter('wheel_circumference', 0.203)
        self.declare_parameter('counts_per_revolution', 4096)
        self.declare_parameter('seed', 42)
        self.declare_parameter('imu.rate', 2000.0)
        self.declare_parameter('imu.noise_std', 0.00)
        self.declare_parameter('imu.drop_rate', 0.000)
        self.declare_parameter('imu.jitter_range', 0.0)
        self.declare_parameter('encoder.rate', 1.0)
        self.declare_parameter('encoder.drop_rate', 0.00)
        self.declare_parameter('encoder.jitter_range', 0.00)

        # Load parameters from YAML (no hardcoded values)
        self.amplitudes = self.get_parameter('amplitudes').get_parameter_value().double_array_value
        self.frequencies = self.get_parameter('frequencies').get_parameter_value().double_array_value
        self.phases = self.get_parameter('phases').get_parameter_value().double_array_value
        self.wheel_circumference = self.get_parameter('wheel_circumference').get_parameter_value().double_value
        self.counts_per_revolution = self.get_parameter('counts_per_revolution').get_parameter_value().integer_value
        self.seed = self.get_parameter('seed').get_parameter_value().integer_value
        self.imu_rate = self.get_parameter('imu.rate').get_parameter_value().double_value
        self.imu_noise_std = self.get_parameter('imu.noise_std').get_parameter_value().double_value
        self.imu_drop_rate = self.get_parameter('imu.drop_rate').get_parameter_value().double_value
        self.imu_jitter_range = self.get_parameter('imu.jitter_range').get_parameter_value().double_value
        self.encoder_rate = self.get_parameter('encoder.rate').get_parameter_value().double_value
        self.encoder_drop_rate = self.get_parameter('encoder.drop_rate').get_parameter_value().double_value
        self.encoder_jitter_range = self.get_parameter('encoder.jitter_range').get_parameter_value().double_value
        
        # Set random seed for repeatable results
        random.seed(self.seed)
        self.get_logger().info(f"Random seed set to {self.seed} for repeatable data generation")

        # Pre-compute constants for velocity calculation
        self.two_pi = 2 * np.pi
        self.A = np.array(self.amplitudes)
        self.f = np.array(self.frequencies)
        self.phi = np.array(self.phases)
        self.A_cos_phi = self.A * np.cos(self.phi)
        self.A_sin_phi = self.A * np.sin(self.phi)
        self.two_pi_f = self.two_pi * self.f

        # Pre-check jitter and drop flags to avoid repeated comparisons
        self.imu_use_jitter = self.imu_jitter_range > 0
        self.encoder_use_jitter = self.encoder_jitter_range > 0
        self.imu_use_dropout = self.imu_drop_rate > 0
        self.encoder_use_dropout = self.encoder_drop_rate > 0

        # State
        self.t0 = time.time()
        self.imu_prev_time = self.t0
        self.imu_prev_velocity = 0.0
        self.encoder_prev_time = self.t0
        self.encoder_position = 0.0
        
        # Publishers
        self.encoder_pub = self.create_publisher(Int32, 'encoder_count', 10)
        self.imu_pub = self.create_publisher(Float32, 'accel_x_mss', 10)
        
        # Pre-allocate message objects to avoid repeated allocation
        self.imu_msg = Float32()
        self.encoder_msg = Int32()
        
        # Timers - only create if rate > 0
        self.imu_timer = self.create_timer(1.0 / self.imu_rate, self.publish_imu) if self.imu_rate > 0 else None
        self.encoder_timer = self.create_timer(1.0 / self.encoder_rate, self.publish_encoder) if self.encoder_rate > 0 else None

    def velocity(self, t):
        """Pure function - computes velocity using pre-computed constants for efficiency."""
        angle = self.two_pi_f * t
        return np.sum(self.A_cos_phi * np.sin(angle) + self.A_sin_phi * np.cos(angle))

    def publish_imu(self):

        current_time = time.time()
        t = current_time - self.t0
        dt = current_time - self.imu_prev_time

        # Compute current velocity (analytic)
        current_vel = self.velocity(t)

        # Numerical acceleration (using IMU's own previous state)
        acceleration = (current_vel - self.imu_prev_velocity) / dt if dt > 0 else 0.0

        # Dropout
        if self.imu_use_dropout and random.random() < self.imu_drop_rate:
            return

        # Add noise and publish
        imu_accel = acceleration + random.gauss(0, self.imu_noise_std)
        self.imu_msg.data = imu_accel  # Already a float, no conversion needed
        self.imu_pub.publish(self.imu_msg)

        # Jitter
        if self.imu_use_jitter:
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
        if self.encoder_use_dropout and random.random() < self.encoder_drop_rate:
            return

        # Convert and publish
        rotations = self.encoder_position / self.wheel_circumference
        encoder_count = int(rotations * self.counts_per_revolution)
        self.encoder_msg.data = encoder_count
        self.encoder_pub.publish(self.encoder_msg)

        # Jitter
        if self.encoder_use_jitter:
            time.sleep(random.uniform(0, self.encoder_jitter_range / self.encoder_rate))

        # Update encoder state
        self.encoder_prev_time = current_time
