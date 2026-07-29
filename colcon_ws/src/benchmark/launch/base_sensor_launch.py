#!/usr/bin/env python3
"""
Base Launch file for sensor data generation.

This launch file provides the synthetic data generator with default parameters.
Child launch files can include this and override parameters as needed.

All sensor-related parameters are declared here with defaults.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    
    # Sensor-specific launch arguments - allow overrides from command line
    # Defaults come from benchmark_params.yaml
    launch_args = [
        DeclareLaunchArgument('namespace', default_value='',
                           description='ROS namespace for sensor topics'),
        
        # These parameters can be overridden at launch time
        # Defaults are in benchmark_params.yaml under synthetic_sensor section
        DeclareLaunchArgument('seed',
                           description='Random seed for repeatable data generation (default: 42)'),
        DeclareLaunchArgument('imu_rate',
                           description='IMU publish rate in Hz (from benchmark_params.yaml)'),
        DeclareLaunchArgument('imu_noise_std',
                           description='IMU noise standard deviation (from benchmark_params.yaml)'),
        DeclareLaunchArgument('imu_drop_rate',
                           description='IMU message drop rate (from benchmark_params.yaml)'),
        DeclareLaunchArgument('imu_jitter_range',
                           description='IMU timing jitter as fraction of period (from benchmark_params.yaml)'),
        DeclareLaunchArgument('encoder_rate',
                           description='Encoder publish rate in Hz (from benchmark_params.yaml)'),
        DeclareLaunchArgument('encoder_drop_rate',
                           description='Encoder message drop rate (from benchmark_params.yaml)'),
        DeclareLaunchArgument('encoder_jitter_range',
                           description='Encoder timing jitter as fraction of period (from benchmark_params.yaml)'),
    ]
    
    # Path to the combined benchmark config file
    benchmark_config_path = PathJoinSubstitution([
        FindPackageShare('benchmark'),
        'config',
        'benchmark_params.yaml'
    ])
    
    # Synthetic data generator node
    synthetic_node = Node(
        package='sensor_streamer',
        executable='synthetic_sensor',
        name='synthetic_sensor',
        output='screen',
        namespace=LaunchConfiguration('namespace'),
        parameters=[
            # Load from the combined benchmark config file
            # ROS2 will automatically use only the synthetic_sensor.ros__parameters section
            benchmark_config_path,
            # Allow launch-time overrides of specific parameters (these take precedence)
            {'seed': LaunchConfiguration('seed')},
            {'imu.rate': LaunchConfiguration('imu_rate')},
            {'imu.noise_std': LaunchConfiguration('imu_noise_std')},
            {'imu.drop_rate': LaunchConfiguration('imu_drop_rate')},
            {'imu.jitter_range': LaunchConfiguration('imu_jitter_range')},
            {'encoder.rate': LaunchConfiguration('encoder_rate')},
            {'encoder.drop_rate': LaunchConfiguration('encoder_drop_rate')},
            {'encoder.jitter_range': LaunchConfiguration('encoder_jitter_range')},
        ]
    )
    
    return LaunchDescription([
        *launch_args,
        synthetic_node,
    ])
