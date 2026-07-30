#!/usr/bin/env python3
"""
Launch file for synthetic sensor node.

This launch file starts the synthetic data generator with configuration
from a YAML file. Parameters can be overridden via command line.

Usage:
    # Run with default config
    ros2 launch sensor_streamer synthetic_sensor.launch.py
    
    # Run with custom config file
    ros2 launch sensor_streamer synthetic_sensor.launch.py config_file:=config/custom_params.yaml
    
    # Override specific parameters
    ros2 launch sensor_streamer synthetic_sensor.launch.py imu_rate:=500.0 encoder_rate:=10.0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    
    # Path to default config file
    default_config = PathJoinSubstitution([
        FindPackageShare('sensor_streamer'),
        'config',
        'synthetic_params.yaml'
    ])
    
    # Launch arguments
    launch_args = [
        DeclareLaunchArgument('namespace', default_value='',
                           description='ROS namespace for sensor topics'),
        DeclareLaunchArgument('config_file', default_value=default_config,
                           description='Path to YAML config file for synthetic sensor'),
        
        # Sensor parameter overrides (can override values from config file)
        DeclareLaunchArgument('seed', default_value='42',
                           description='Random seed for repeatable data generation'),
        DeclareLaunchArgument('amplitudes', default_value='[1.0, 0.3, 0.1]',
                           description='Motion signal amplitudes'),
        DeclareLaunchArgument('frequencies', default_value='[0.5, 1.5, 3.0]',
                           description='Motion signal frequencies'),
        DeclareLaunchArgument('phases', default_value='[0.0, 0.0, 0.0]',
                           description='Motion signal phases'),
        DeclareLaunchArgument('wheel_circumference', default_value='0.203',
                           description='Wheel circumference in meters'),
        DeclareLaunchArgument('counts_per_revolution', default_value='4096',
                           description='Encoder counts per revolution'),
        DeclareLaunchArgument('imu_rate', default_value='2000.0',
                           description='IMU publish rate in Hz'),
        DeclareLaunchArgument('imu_noise_std', default_value='0.00',
                           description='IMU noise standard deviation'),
        DeclareLaunchArgument('imu_drop_rate', default_value='0.000',
                           description='IMU message drop rate'),
        DeclareLaunchArgument('imu_jitter_range', default_value='0.0',
                           description='IMU timing jitter as fraction of period'),
        DeclareLaunchArgument('encoder_rate', default_value='1.0',
                           description='Encoder publish rate in Hz'),
        DeclareLaunchArgument('encoder_drop_rate', default_value='0.00',
                           description='Encoder message drop rate'),
        DeclareLaunchArgument('encoder_jitter_range', default_value='0.00',
                           description='Encoder timing jitter as fraction of period'),
    ]
    
    # Build parameter list for the node
    # 1. Load from config file first
    # 2. Override with launch arguments
    node_params = [
        LaunchConfiguration('config_file'),
        {'namespace': LaunchConfiguration('namespace')},
        {'seed': LaunchConfiguration('seed')},
        {'amplitudes': LaunchConfiguration('amplitudes')},
        {'frequencies': LaunchConfiguration('frequencies')},
        {'phases': LaunchConfiguration('phases')},
        {'wheel_circumference': LaunchConfiguration('wheel_circumference')},
        {'counts_per_revolution': LaunchConfiguration('counts_per_revolution')},
        {'imu.rate': LaunchConfiguration('imu_rate')},
        {'imu.noise_std': LaunchConfiguration('imu_noise_std')},
        {'imu.drop_rate': LaunchConfiguration('imu_drop_rate')},
        {'imu.jitter_range': LaunchConfiguration('imu_jitter_range')},
        {'encoder.rate': LaunchConfiguration('encoder_rate')},
        {'encoder.drop_rate': LaunchConfiguration('encoder_drop_rate')},
        {'encoder.jitter_range': LaunchConfiguration('encoder_jitter_range')},
    ]
    
    # Synthetic sensor node (Python version)
    synthetic_node = Node(
        package='sensor_streamer',
        executable='synthetic_sensor_node.py',
        name='synthetic_sensor',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=node_params
    )
    
    return LaunchDescription([
        *launch_args,
        synthetic_node,
    ])
