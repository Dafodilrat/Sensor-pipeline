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
    # LAUNCH ARGUMENTS - Only declare arguments specific to THIS launch file
    # Sensor arguments are handled by the included base_sensor_launch.py
    # ========================================================================
    
    # Default parameter values from benchmark_params.yaml
    # These will be used if not overridden via command line
    yaml_defaults = {
        'lp_cutoff_hz': '10.0',
        'timeout_seconds': '5.0',
        'test_duration': '30.0',
        'warmup_duration': '2.0',
        'max_acceptable_latency_us': '1000',
        'stats_interval': '1.0',
        'imu_rate': '200.0',
        'encoder_rate': '50.0',
    }
    
    launch_args = [
        # Path to the combined benchmark config file (contains all parameters)
        DeclareLaunchArgument('benchmark_config',
                             default_value=PathJoinSubstitution([
                                 FindPackageShare('benchmark'),
                                 'config',
                                 'benchmark_params.yaml'
                             ]),
                             description='Path to combined benchmark config file'),
        
        # Parameters that can be overridden via command line
        # Defaults match values in benchmark_params.yaml
        DeclareLaunchArgument('lp_cutoff_hz',
                           default_value=yaml_defaults['lp_cutoff_hz'],
                           description='Override lp_node.lp_cutoff_hz from config'),
        DeclareLaunchArgument('timeout_seconds',
                           default_value=yaml_defaults['timeout_seconds'],
                           description='Override lp_node.timeout_seconds from config'),
        DeclareLaunchArgument('test_duration',
                           default_value=yaml_defaults['test_duration'],
                           description='Override benchmark.test_duration from config'),
        DeclareLaunchArgument('warmup_duration',
                           default_value=yaml_defaults['warmup_duration'],
                           description='Override benchmark.warmup_duration from config'),
        DeclareLaunchArgument('max_acceptable_latency_us',
                           default_value=yaml_defaults['max_acceptable_latency_us'],
                           description='Override benchmark.max_acceptable_latency_us from config'),
        DeclareLaunchArgument('stats_interval',
                           default_value=yaml_defaults['stats_interval'],
                           description='Override output.stats_interval from config'),
        DeclareLaunchArgument('imu_rate',
                           default_value=yaml_defaults['imu_rate'],
                           description='Override synthetic_sensor.imu.rate from config'),
        DeclareLaunchArgument('encoder_rate',
                           default_value=yaml_defaults['encoder_rate'],
                           description='Override synthetic_sensor.encoder.rate from config'),
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
