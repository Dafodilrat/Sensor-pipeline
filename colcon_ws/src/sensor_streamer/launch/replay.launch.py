#!/usr/bin/env python3
"""
Launch file for replay node.

This launch file starts the replay node with a CSV file.

Usage:
    # Run replay with CSV file
    ros2 launch sensor_streamer replay.launch.py csv:=path/to/sensor_data.csv
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    
    # Launch arguments
    launch_args = [
        DeclareLaunchArgument('namespace', default_value='',
                           description='ROS namespace for sensor topics'),
        DeclareLaunchArgument('csv', default_value='',
                           description='Path to CSV file for replay (required)'),
    ]
    
    # Replay node
    replay_node = Node(
        package='sensor_streamer',
        executable='replay.py',
        name='replay_data_node',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[
            {'csv_file': LaunchConfiguration('csv')},
        ]
    )
    
    return LaunchDescription([
        *launch_args,
        replay_node,
    ])
