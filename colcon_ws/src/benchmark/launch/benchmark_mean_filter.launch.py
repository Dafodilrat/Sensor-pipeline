#!/usr/bin/env python3
"""
Launch file for benchmarking MEAN FILTER performance (Task 4.3).

This launch file starts:
1. Synthetic data generator (includes base_sensor_launch.py)
2. Mean filter node with configurable parameters
3. Benchmark node that subscribes to mean filter output and measures performance

Usage:
    # Basic launch with defaults from base_sensor_launch.py (200Hz IMU, 50Hz encoder)
    ros2 launch benchmark benchmark_mean_filter.launch.py
    
    # Override parameters
    ros2 launch benchmark benchmark_mean_filter.launch.py \
        imu_rate:=200.0 \
        ma_window_size:=10 \
        test_duration:=30.0
        
    # Test with jitter and drop rate
    ros2 launch benchmark benchmark_mean_filter.launch.py \
        imu_jitter_range:=0.2 \
        imu_drop_rate:=0.01
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare, GetPackageShare


def generate_launch_description():
    
    # ========================================================================
    # LAUNCH ARGUMENTS - Only declare arguments specific to THIS launch file
    # Sensor arguments are handled by the included base_sensor_launch.py
    # ========================================================================
    
    launch_args = [
        # ===== MEAN FILTER CONFIGURATION (from mean_filter_node.ros__parameters in YAML) =====
        DeclareLaunchArgument('ma_window_size',
                           description='Mean filter window size (from mean_filter_node.ros__parameters)'),
        DeclareLaunchArgument('use_time_based_ma',
                           description='Use time-based window instead of sample count (from mean_filter_node.ros__parameters)'),
        DeclareLaunchArgument('ma_window_duration_ms',
                           description='Time window duration in ms (from mean_filter_node.ros__parameters)'),
        DeclareLaunchArgument('ma_timeout_seconds',
                           description='Filter reset timeout (from mean_filter_node.ros__parameters)'),
        
        # Path to the combined benchmark config file (contains both synthetic_sensor and benchmark_node params)
        DeclareLaunchArgument('benchmark_config',
                             default_value=PathJoinSubstitution([
                                 FindPackageShare('benchmark'),
                                 'config',
                                 'benchmark_params.yaml'
                             ]),
                             description='Path to combined benchmark config file'),
        
        DeclareLaunchArgument('test_duration',
                           description='Benchmark test duration in seconds'),
        DeclareLaunchArgument('warmup_duration',
                           description='Warmup period before measurements start'),
        DeclareLaunchArgument('max_acceptable_latency_us',
                           description='Warning threshold for processing latency (microseconds)'),
        DeclareLaunchArgument('stats_interval',
                           description='Statistics publishing interval in seconds'),
        
        # ===== SENSOR PARAMETERS NEEDED BY BENCHMARK NODE =====
        # These are declared in base_sensor_launch.py but needed here for benchmark_node parameters
        DeclareLaunchArgument('imu_rate',
                           description='IMU publish rate in Hz (from base_sensor_launch.py)'),
        DeclareLaunchArgument('encoder_rate',
                           description='Encoder publish rate in Hz (from base_sensor_launch.py)'),
    ]
    
    # ========================================================================
    # INCLUDE BASE SENSOR LAUNCH
    # ========================================================================
    
    base_sensor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                GetPackageShare('benchmark').find('benchmark'),
                'launch',
                'base_sensor_launch.py'
            )
        )
    )
    
    # ========================================================================
    # ADDITIONAL NODES (specific to this launch file)
    # ========================================================================
    
    additional_nodes = [
        
        # 1. MEAN FILTER NODE
        Node(
            package='signal_processing_cpp',
            executable='mean_filter_node',
            name='mean_filter_node',
            output='screen',
            parameters=[
                # Allow command-line overrides
                {'ma_window_size': LaunchConfiguration('ma_window_size')},
                {'use_time_based_ma': LaunchConfiguration('use_time_based_ma')},
                {'ma_window_duration_ms': LaunchConfiguration('ma_window_duration_ms')},
                {'timeout_seconds': LaunchConfiguration('ma_timeout_seconds')},
                # Load from YAML file - ROS2 will use mean_filter_node section
                LaunchConfiguration('benchmark_config')
            ]
        ),
        
        # 2. MEAN FILTER BENCHMARK NODE
        Node(
            package='benchmark',
            executable='mean_benchmark_node',
            name='mean_benchmark_node', 
            output='screen',
            parameters=[
                # Test configuration - these override values from the config file
                {'benchmark.test_duration': LaunchConfiguration('test_duration')},
                {'benchmark.warmup_duration': LaunchConfiguration('warmup_duration')},
                {'benchmark.max_acceptable_latency_us': LaunchConfiguration('max_acceptable_latency_us')},
                {'benchmark.expected_imu_rate': LaunchConfiguration('imu_rate')},
                {'benchmark.expected_encoder_rate': LaunchConfiguration('encoder_rate')},
                {'benchmark.measure_latency': True},
                {'output.log_level': 'INFO'},
                
                # Load the combined config file - ROS2 will only use benchmark parameters
                LaunchConfiguration('benchmark_config')
            ]
        ),
        
    ]
    
    return LaunchDescription([
        *launch_args,
        base_sensor_launch,
        *additional_nodes,
    ])
