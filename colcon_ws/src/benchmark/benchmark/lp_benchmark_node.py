#!/usr/bin/env python3
"""
Low-Pass Filter Benchmark Node

This node benchmarks the performance of the low-pass filter node
by subscribing to its output and measuring latency, throughput, and rate compliance.
Statistics are written to JSON files.

It inherits all functionality from BenchmarkBaseNode and only specifies
the subscription topics for the LP filter output.
"""

import rclpy
from benchmark.benchmark_base_node import BenchmarkBaseNode


class LPBenchmarkNode(BenchmarkBaseNode):
    """LP Filter Benchmark Node - inherits all functionality from base class."""
    
    def __init__(self):
        super().__init__(
            node_name='lp_benchmark_node',
            filter_type='LOW-PASS FILTER',
            imu_topic='lp_accel',      # Subscribe to LP filter IMU output
            output_file_prefix='lp_benchmark'
        )


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = LPBenchmarkNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
