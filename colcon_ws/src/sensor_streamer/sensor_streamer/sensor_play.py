#!/usr/bin/env python3
"""
Launcher node that starts either synthetic_sensor or replay based on arguments.

Usage:
    # Run synthetic sensor node (default)
    ros2 run sensor_streamer sensor_play
    
    # Run synthetic sensor with custom config
    ros2 run sensor_streamer sensor_play --config config/synthetic_params.yaml
    
    # Run replay node with CSV file
    ros2 run sensor_streamer sensor_play --replay sensor_log.csv
"""
import sys
import os
import rclpy


def main(args=None):
    # Parse arguments before ROS2 initialization
    csv_file = None
    
    # Check for --replay flag
    if '--replay' in sys.argv:
        idx = sys.argv.index('--replay')
        if idx + 1 >= len(sys.argv):
            print("Error: CSV file path not provided after --replay flag")
            print("Usage: ros2 run sensor_streamer sensor_play --replay <csv_file_path>")
            sys.exit(1)
        csv_file = sys.argv[idx + 1]
        
        # Check if file exists
        if not os.path.isfile(csv_file):
            print(f"Error: CSV file not found: {csv_file}")
            print("Usage: ros2 run sensor_streamer sensor_play --replay <csv_file_path>")
            sys.exit(1)
    
    # Check for --config flag (for synthetic sensor)
    if '--config' in sys.argv:
        idx = sys.argv.index('--config')
        if idx + 1 >= len(sys.argv):
            print("Error: Config file path not provided after --config flag")
            print("Usage: ros2 run sensor_streamer sensor_play --config <yaml_file_path>")
            sys.exit(1)
        config_file = sys.argv[idx + 1]
        
        # Check if file exists
        if not os.path.isfile(config_file):
            print(f"Error: Config file not found: {config_file}")
            print("Usage: ros2 run sensor_streamer sensor_play --config <yaml_file_path>")
            sys.exit(1)
        
        # Convert --config to --ros-args --params-file for ROS2
        sys.argv[idx] = '--ros-args'
        sys.argv[idx + 1] = '--params-file'
        sys.argv.insert(idx + 2, config_file)
    
    rclpy.init(args=args)
    
    node = None
    try:
        if csv_file is not None:
            # Run replay node
            from sensor_streamer.replay import ReplayDataNode
            node = ReplayDataNode(csv_file=csv_file)
        else:
            # Default to synthetic sensor
            from sensor_streamer.generator import SyntheticDataNode
            node = SyntheticDataNode()
        
        rclpy.spin(node)
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
