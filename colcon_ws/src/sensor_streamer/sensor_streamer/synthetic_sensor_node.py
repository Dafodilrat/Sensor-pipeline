#!/usr/bin/env python3
"""
Entry point for synthetic_sensor node.

This is a minimal entry point that just creates the SyntheticDataNode
and spins it. All configuration should come from parameters passed via
launch files or command line arguments.

Usage:
    ros2 run sensor_streamer synthetic_sensor_node
"""

import rclpy
from sensor_streamer.generator import SyntheticDataNode


def main(args=None):
    rclpy.init(args=args)
    node = SyntheticDataNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
