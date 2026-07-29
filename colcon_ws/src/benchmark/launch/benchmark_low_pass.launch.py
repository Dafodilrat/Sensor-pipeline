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
from launch_ros.substitutions import FindPackageShare, GetPackageShare


def generate_launch_description():
    
    # ========================================================================
    # LAUNCH ARGUMENTS - Only declare arguments specific to THIS launch file
    # Sensor arguments are handled by the included base_sensor_launch.py
    # ========================================================================
    
    launch_args = [
        # ===== LOW-PASS FILTER CONFIGURATION (from lp_node.ros__parameters in YAML) =====
        DeclareLaunchArgument('lp_cutoff_hz',
                           description='Low-pass filter cutoff frequency in Hz (from lp_node.ros__parameters)'),
        DeclareLaunchArgument('fixed_point_bits',
                           description='Number of bits for fixed-point arithmetic (from lp_node.ros__parameters)'),
        DeclareLaunchArgument('timeout_seconds',
                           description='Filter reset timeout (from lp_node.ros__parameters)'),
        
        # ===== BENCHMARK CONFIGURATION (from benchmark_node.ros__parameters in YAML) =====
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
        
        # 1. LOW-PASS FILTER NODE
        Node(
            package='signal_processing_cpp',
            executable='lp_node',
            name='lp_node',
            output='screen',
            parameters=[
                # Allow command-line overrides
                {'lp_cutoff_hz': LaunchConfiguration('lp_cutoff_hz')},
                {'fixed_point_bits': LaunchConfiguration('fixed_point_bits')},
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
