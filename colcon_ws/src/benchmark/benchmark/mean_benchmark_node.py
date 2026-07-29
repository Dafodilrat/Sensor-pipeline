#!/usr/bin/env python3
"""
Mean Filter Benchmark Node

This node benchmarks the performance of the mean filter node
by subscribing to its output and measuring latency, throughput, and rate compliance.
Statistics are written to JSON files.

It inherits all functionality from BenchmarkBaseNode and only specifies
the subscription topics for the mean filter output.
"""

import rclpy
from benchmark.benchmark_base_node import BenchmarkBaseNode


class MeanBenchmarkNode(BenchmarkBaseNode):
    """Mean Filter Benchmark Node - inherits all functionality from base class."""
    
    def __init__(self):
        super().__init__(
            node_name='mean_benchmark_node',
            filter_type='MEAN FILTER',
            imu_topic='mean_accel',      # Subscribe to mean filter IMU output
            output_file_prefix='mean_benchmark'
        )


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = MeanBenchmarkNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
