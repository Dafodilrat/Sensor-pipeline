#!/usr/bin/env python3
"""
Launch file for benchmarking LOW-PASS FILTER performance (Task 4.3).

This launch file starts:
1. Synthetic data generator (includes base_sensor_launch.py)
2. Low-pass filter node with configurable parameters
3. Benchmark node that subscribes to low-pass filter output and measures performance

Usage:
    # Basic launch with defaults from benchmark_params.yaml (200Hz IMU, cutoff 10Hz)
    ros2 launch benchmark benchmark_low_pass.launch.py
    
    # Override parameters
    ros2 launch benchmark benchmark_low_pass.launch.py \
        imu_rate:=200.0 \
        lp_cutoff_hz:=10.0 \
        test_duration:=30.0
        
    # Test with different cutoff frequency
    ros2 launch benchmark benchmark_low_pass.launch.py \
        lp_cutoff_hz:=5.0 \
        test_duration:=60.0
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    
    # ========================================================================
    # LAUNCH ARGUMENTS - Benchmark-specific arguments only
    # Sensor arguments are inherited from base_sensor_launch.py
    # ========================================================================
    
    # Path to the combined benchmark config file (contains all parameters)
    benchmark_config_path = PathJoinSubstitution([
        FindPackageShare('benchmark'),
        'config',
        'benchmark_params.yaml'
    ])
    
    launch_args = [
        DeclareLaunchArgument('benchmark_config',
                             default_value=benchmark_config_path,
                             description='Path to combined benchmark config file'),
        
        # Filter-specific parameters
        DeclareLaunchArgument('lp_cutoff_hz',
                           default_value='10.0',
                           description='Low-pass filter cutoff frequency in Hz'),
        DeclareLaunchArgument('timeout_seconds',
                           default_value='5.0',
                           description='Low-pass filter timeout in seconds'),
        
        # Benchmark-specific parameters
        DeclareLaunchArgument('test_duration',
                           default_value='30.0',
                           description='Benchmark test duration in seconds'),
        DeclareLaunchArgument('warmup_duration',
                           default_value='2.0',
                           description='Benchmark warmup duration in seconds'),
        DeclareLaunchArgument('max_acceptable_latency_us',
                           default_value='1000',
                           description='Maximum acceptable latency in microseconds'),
        DeclareLaunchArgument('stats_interval',
                           default_value='1.0',
                           description='Statistics publishing interval in seconds'),
    ]
    
    # ========================================================================
    # INCLUDE BASE SENSOR LAUNCH
    # ========================================================================
    
    base_sensor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                FindPackageShare('benchmark').find('benchmark'),
                'launch',
                'base_sensor_launch.py'
            )
        )
    )
    
    # ========================================================================
    # ADDITIONAL NODES (specific to this launch file)
    # ========================================================================
    
    additional_nodes = [
        
        # 1. LOW-PASS FILTER NODE
        Node(
            package='signal_processing_cpp',
            executable='lp_node',
            name='lp_node',
            output='screen',
            parameters=[
                # Allow command-line overrides
                {'lp_cutoff_hz': LaunchConfiguration('lp_cutoff_hz')},
                {'timeout_seconds': LaunchConfiguration('timeout_seconds')},
                # Load from YAML file - ROS2 will use lp_node.ros__parameters section
                LaunchConfiguration('benchmark_config')
            ]
        ),
        
        # 2. LOW-PASS FILTER BENCHMARK NODE
        Node(
            package='benchmark',
            executable='lp_benchmark_node',
            name='lp_benchmark_node', 
            output='screen',
            parameters=[
                # Load the combined config file first - ROS2 will only use benchmark parameters
                LaunchConfiguration('benchmark_config'),
                # Override with launch-time values (these take precedence)
                {'benchmark.test_duration': LaunchConfiguration('test_duration')},
                {'benchmark.warmup_duration': LaunchConfiguration('warmup_duration')},
                {'benchmark.max_acceptable_latency_us': LaunchConfiguration('max_acceptable_latency_us')},
                {'benchmark.expected_imu_rate': LaunchConfiguration('imu_rate')},
                {'benchmark.expected_encoder_rate': LaunchConfiguration('encoder_rate')},
                {'benchmark.measure_latency': True},
                {'output.log_level': 'INFO'},
            ]
        ),
        
    ]
    
    return LaunchDescription([
        *launch_args,
        base_sensor_launch,
        *additional_nodes,
    ])
