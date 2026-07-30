#!/usr/bin/env python3
"""
Launcher script that starts synthetic_sensor or replay based on arguments.

This script checks the arguments and either:
1. Launches the synthetic_sensor.launch.py with the provided config
2. Runs the replay node directly with a CSV file

Usage:
    # Run synthetic sensor with default config
    ros2 run sensor_streamer sensor_play
    
    # Run synthetic sensor with custom config
    ros2 run sensor_streamer sensor_play --config config/custom_params.yaml
    
    # Run replay with CSV file
    ros2 run sensor_streamer sensor_play --replay sensor_log.csv
"""
import sys
import os
import subprocess


def main():
    # Parse arguments
    csv_file = None
    config_file = None
    
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
            sys.exit(1)
    
    # decided what to run
    if csv_file is not None:
        # Run replay node directly
        from sensor_streamer.replay import ReplayDataNode
        import rclpy
        
        rclpy.init()
        node = ReplayDataNode(csv_file=csv_file)
        
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()
    else:
        # Run synthetic sensor via launch file
        # Build command to launch synthetic_sensor.launch.py
        cmd = ['ros2', 'launch', 'sensor_streamer', 'synthetic_sensor.launch.py']
        
        if config_file is not None:
            cmd.append(f'config_file:={config_file}')
        
        # Execute the launch command
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)


if __name__ == '__main__':
    main()
