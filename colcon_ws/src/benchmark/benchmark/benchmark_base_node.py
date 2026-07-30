#!/usr/bin/env python3
"""
Base Benchmark Node for Signal Processing Pipeline

This is a base class that provides common benchmarking functionality.
It includes callbacks for filtered data and functions to calculate benchmark metrics.
Statistics are written to files instead of being published.

Child classes only need to specify their subscription topics - no conditional logic.
"""

import rclpy
from rclpy.node import Node
import time
import os
import json
from std_msgs.msg import Float32
from ament_index_python.packages import get_package_share_directory


def get_workspace_root():
    """
    Get the root directory of the ROS 2 workspace.
    
    This function uses the package share directory to determine the workspace root
    by finding the path segment before /build, /install, or /src.
    
    Returns:
        str: The absolute path to the workspace root directory.
    """
    package_share = get_package_share_directory('benchmark')
    
    if not package_share:
        package_share = os.getcwd()
    
    for marker in ['/install/', '/build/', '/src/']:
        if marker in package_share:
            return package_share.split(marker)[0]
    
    return package_share


class FilterStatistics:
    """Statistics structure for benchmarking."""
    
    def __init__(self):
        self.total_samples = 0
        self.min_processing_time_us = float('inf')
        self.max_processing_time_us = 0.0
        self.total_processing_time_us = 0.0
        self.first_sample_time = None
        self.last_sample_time = None
        self.initialized = False
    
    def add_sample(self, count, processing_time_us):
        self.total_samples += count
        self.total_processing_time_us += processing_time_us
        self.min_processing_time_us = min(self.min_processing_time_us, processing_time_us)
        self.max_processing_time_us = max(self.max_processing_time_us, processing_time_us)
        
        current_time = time.time()
        if not self.initialized:
            self.first_sample_time = current_time
            self.initialized = True
        self.last_sample_time = current_time
    
    def get_average_processing_time(self):
        return self.total_processing_time_us / self.total_samples if self.total_samples > 0 else 0.0
    
    def get_duration_seconds(self):
        if not self.initialized or self.first_sample_time is None or self.last_sample_time is None:
            return 0.0
        return self.last_sample_time - self.first_sample_time
    
    def get_throughput_hz(self):
        duration = self.get_duration_seconds()
        return self.total_samples / duration if duration > 0 else 0.0
    
    def to_dict(self):
        return {
            'total_samples': self.total_samples,
            'min_processing_time_us': self.min_processing_time_us,
            'max_processing_time_us': self.max_processing_time_us,
            'avg_processing_time_us': self.get_average_processing_time(),
            'throughput_hz': self.get_throughput_hz(),
            'duration_seconds': self.get_duration_seconds()
        }


class BenchmarkBaseNode(Node):
    """Base class for benchmark nodes."""
    
    def __init__(self, node_name, filter_type, imu_topic, output_file_prefix):
        super().__init__(node_name)
        
        self.filter_type = filter_type
        self.output_file_prefix = output_file_prefix
        
        # Parameters
        self.declare_parameter('benchmark.expected_imu_rate', 200.0)
        self.declare_parameter('benchmark.rate_tolerance_percent', 5.0)
        self.declare_parameter('benchmark.test_duration', 30.0)
        self.declare_parameter('benchmark.warmup_duration', 2.0)
        self.declare_parameter('benchmark.measure_latency', True)
        self.declare_parameter('output.log_level', 'INFO')
        
        # Get parameter values
        self.expected_imu_rate = self.get_parameter('benchmark.expected_imu_rate').value
        self.rate_tolerance_percent = self.get_parameter('benchmark.rate_tolerance_percent').value
        self.test_duration = self.get_parameter('benchmark.test_duration').value
        self.warmup_duration = self.get_parameter('benchmark.warmup_duration').value
        self.measure_latency = self.get_parameter('benchmark.measure_latency').value
        self.log_level = self.get_parameter('output.log_level').value
        
        # Set log level
        self.set_log_level(self.log_level)
        
        # State tracking
        self.last_imu_time = self.get_clock().now()
        
        # Statistics tracking
        self.imu_statistics = FilterStatistics()
        
        # Setup subscribers
        self.imu_sub = self.create_subscription(
            Float32, imu_topic, self.filtered_imu_callback, 10000)
        
        # Setup test timer
        self.test_timer = self.create_timer(
            self.test_duration + self.warmup_duration,
            self.complete_test)
        
        self.get_logger().info(f"{self.filter_type} Benchmark Node initialized")
        self.get_logger().info(f"Subscribed to: /{imu_topic} (IMU)")
        self.get_logger().info(f"Output will be written to: {self.output_file_prefix}_*.json")

    def set_log_level(self, level):
        if level == "DEBUG":
            self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)
        elif level == "INFO":
            self.get_logger().set_level(rclpy.logging.LoggingSeverity.INFO)
        elif level == "WARN":
            self.get_logger().set_level(rclpy.logging.LoggingSeverity.WARN)
        elif level == "ERROR":
            self.get_logger().set_level(rclpy.logging.LoggingSeverity.ERROR)

    def filtered_imu_callback(self, msg):
        start_time = time.time()
        
        value = msg.data
        current_time = self.get_clock().now()
        
        # Calculate dt
        dt = (current_time - self.last_imu_time).nanoseconds / 1e9
        self.last_imu_time = current_time
        
        # Increment counters
        self.imu_statistics.add_sample(1, 0.0)
        
        # Calculate processing latency
        if self.measure_latency:
            end_time = time.time()
            processing_time_us = (end_time - start_time) * 1e6
            self.imu_statistics.add_sample(0, processing_time_us)



    def validate_rate(self, actual_rate, expected_rate):
        tolerance = expected_rate * self.rate_tolerance_percent / 100.0
        return abs(actual_rate - expected_rate) <= tolerance

    def can_keep_up(self, avg_processing_time_us, expected_rate):
        # Less than 100% utilization means it can keep up
        return (avg_processing_time_us * expected_rate * 0.001) < 100.0

    def calculate_utilization(self, avg_processing_time_us, expected_rate):
        return avg_processing_time_us * expected_rate * 0.001

    def write_stats_to_file(self):
        """Write statistics to JSON files."""
        # Get results directory in workspace root
        results_dir = os.path.join(get_workspace_root(), 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # IMU statistics
        imu_stats = self.imu_statistics.to_dict()
        imu_stats.update({
            'expected_rate': self.expected_imu_rate,
            'rate_ok': self.validate_rate(imu_stats['throughput_hz'], self.expected_imu_rate),
            'utilization_percent': self.calculate_utilization(
                imu_stats['avg_processing_time_us'], self.expected_imu_rate),
            'can_keep_up': self.can_keep_up(imu_stats['avg_processing_time_us'], self.expected_imu_rate)
        })
        
        # Write IMU file with Hz in filename
        imu_rate_hz = int(self.expected_imu_rate)
        imu_file = os.path.join(results_dir, f"{self.output_file_prefix}_{imu_rate_hz}hz_{timestamp}.json")
        results = {
            'filter_type': self.filter_type,
            'sensor_type': 'imu',
            'timestamp': timestamp,
            'configuration': {
                'expected_rate': self.expected_imu_rate,
                'rate_tolerance_percent': self.rate_tolerance_percent,
                'test_duration': self.test_duration,
                'measure_latency': self.measure_latency
            },
            'statistics': imu_stats
        }
        with open(imu_file, 'w') as f:
            json.dump(results, f, indent=2)
        self.get_logger().info(f"Statistics written to: {imu_file}")

    def complete_test(self):
        self.get_logger().info(f"=== {self.filter_type} BENCHMARK TEST COMPLETED ===")
        
        # Calculate final statistics
        imu_duration = self.imu_statistics.get_duration_seconds()
        if imu_duration > 0:
            actual_imu_rate = self.imu_statistics.get_throughput_hz()
            imu_rate_ok = self.validate_rate(actual_imu_rate, self.expected_imu_rate)
            imu_avg_time = self.imu_statistics.get_average_processing_time()
            can_keep_up = self.can_keep_up(imu_avg_time, self.expected_imu_rate)
            utilization = self.calculate_utilization(imu_avg_time, self.expected_imu_rate)
            
            self.get_logger().info(
                f"IMU: {self.imu_statistics.total_samples} samples, "
                f"{actual_imu_rate:.2f}Hz (expected: {self.expected_imu_rate:.1f}Hz, {'OK' if imu_rate_ok else 'FAIL'}), "
                f"avg time: {imu_avg_time:.1f} us")
            self.get_logger().info(
                f"Performance: {'ABLE' if can_keep_up else 'UNABLE'} to keep up "
                f"({utilization:.1f}% utilization)")
        
        # Write statistics to file
        self.write_stats_to_file()
        
        # Shutdown the test timer
        if self.test_timer is not None:
            self.test_timer.cancel()
            self.test_timer = None
        
        # Shutdown this node
        self.get_logger().info("Node will now shutdown")
        raise KeyboardInterrupt()


def main(args=None):
    """Main function for testing the base class directly."""
    rclpy.init(args=args)
    
    # This is just for testing - child classes should be used in practice
    from benchmark.benchmark_base_node import BenchmarkBaseNode
    
    try:
        node = BenchmarkBaseNode(
            node_name='test_benchmark_node',
            filter_type='TEST FILTER',
            imu_topic='mean_accel',
            output_file_prefix='test_benchmark'
        )
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


