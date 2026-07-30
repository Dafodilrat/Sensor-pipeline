#!/usr/bin/env python3
"""
Base Launch file for sensor data generation.

This launch file includes the synthetic_sensor.launch.py from sensor_streamer
package and uses benchmark's synthetic_params.yaml config file.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    
    # Path to benchmark's synthetic sensor config file
    sensor_config_path = PathJoinSubstitution([
        FindPackageShare('benchmark'),
        'config',
        'synthetic_params.yaml'
    ])
    
    # Path to sensor_streamer's synthetic sensor launch file
    sensor_launch_path = PathJoinSubstitution([
        FindPackageShare('sensor_streamer'),
        'launch',
        'synthetic_sensor.launch.py'
    ])
    
    # Launch arguments - these override values from benchmark/config/synthetic_params.yaml
    launch_args = [
        DeclareLaunchArgument('namespace', default_value='',
                           description='ROS namespace for sensor topics'),
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
    
    # Include the sensor_streamer launch file with config file and parameter overrides
    sensor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sensor_launch_path),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'config_file': sensor_config_path,
            'seed': LaunchConfiguration('seed'),
            'amplitudes': LaunchConfiguration('amplitudes'),
            'frequencies': LaunchConfiguration('frequencies'),
            'phases': LaunchConfiguration('phases'),
            'wheel_circumference': LaunchConfiguration('wheel_circumference'),
            'counts_per_revolution': LaunchConfiguration('counts_per_revolution'),
            'imu_rate': LaunchConfiguration('imu_rate'),
            'imu_noise_std': LaunchConfiguration('imu_noise_std'),
            'imu_drop_rate': LaunchConfiguration('imu_drop_rate'),
            'imu_jitter_range': LaunchConfiguration('imu_jitter_range'),
            'encoder_rate': LaunchConfiguration('encoder_rate'),
            'encoder_drop_rate': LaunchConfiguration('encoder_drop_rate'),
            'encoder_jitter_range': LaunchConfiguration('encoder_jitter_range'),
        }.items()
    )
    
    return LaunchDescription([
        *launch_args,
        sensor_launch,
    ])
