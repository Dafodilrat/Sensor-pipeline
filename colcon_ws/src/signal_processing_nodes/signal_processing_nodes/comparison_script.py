#!/usr/bin/env python3
"""
Comparison script for verifying numerical consistency between C++ and Python processing nodes.

This script:
1. Subscribes to the output topics from both C++ and Python processing nodes
2. Collects a sample of data for comparison
3. Compares the results within a specified tolerance
4. Outputs a report showing any discrepancies

Usage:
    # Start both processing nodes first
    ros2 run signal_processing_nodes cpp_processing_node &
    ros2 run signal_processing_nodes python_processing_node &
    
    # Then run this comparison script
    python3 comparison_script.py
    
    # Or with custom parameters
    python3 comparison_script.py --samples 100 --tolerance 1e-6
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import sys
import numpy as np
from collections import defaultdict
import argparse


class ComparisonNode(Node):
    """
    ROS2 node that compares outputs from C++ and Python processing nodes.
    """
    
    def __init__(self, samples=100, tolerance=1e-6):
        super().__init__('comparison_node')
        
        self.samples = samples
        self.tolerance = tolerance
        self.comparison_data = defaultdict(lambda: {'cpp': [], 'python': []})
        self.received_callbacks = {}  # Track which callbacks have fired
        
        # Initialize storage for different topics
        self.topics = [
            'ma_encoder', 'ma_accel', 
            'lp_encoder', 'lp_accel',
            'filtered_encoder_count', 'filtered_accel_x_mss'
        ]
        
        for topic in self.topics:
            # Subscribe to both C++ and Python versions
            # Assume C++ nodes publish to /cpp/ namespace and Python to /python/ namespace
            # Or we can differentiate by node name prefix
            
            # For simplicity, let's assume the topics are already namespaced
            # C++ node: /cpp_processing_node/ma_encoder, etc.
            # Python node: /python_processing_node/ma_encoder, etc.
            
            cpp_topic = f'/cpp_processing_node/{topic}'
            py_topic = f'/python_processing_node/{topic}'
            
            # Subscribe to C++ topic
            self.create_subscription(
                Int32 if topic.endswith('_count') or topic.startswith('lp_encoder') or topic.startswith('ma_encoder') else Float32,
                cpp_topic,
                lambda msg, t=topic: self.cpp_callback(msg, t),
                10
            )
            
            # Subscribe to Python topic
            self.create_subscription(
                Int32 if topic.endswith('_count') or topic.startswith('lp_encoder') or topic.startswith('ma_encoder') else Float32,
                py_topic,
                lambda msg, t=topic: self.python_callback(msg, t),
                10
            )
        
        self.get_logger().info(f"Comparing {self.samples} samples with tolerance {self.tolerance}")
        self.get_logger().info("Collecting data from C++ and Python processing nodes...")
    
    def cpp_callback(self, msg, topic):
        """Callback for C++ node outputs."""
        value = msg.data
        self.comparison_data[topic]['cpp'].append(value)
        
        # Check if we have enough samples
        if len(self.comparison_data[topic]['cpp']) >= self.samples and \
           len(self.comparison_data[topic]['python']) >= self.samples:
            self.compare_topic(topic)
    
    def python_callback(self, msg, topic):
        """Callback for Python node outputs."""
        value = msg.data
        self.comparison_data[topic]['python'].append(value)
        
        # Check if we have enough samples
        if len(self.comparison_data[topic]['cpp']) >= self.samples and \
           len(self.comparison_data[topic]['python']) >= self.samples:
            self.compare_topic(topic)
    
    def compare_topic(self, topic):
        """Compare C++ and Python output for a specific topic."""
        cpp_values = self.comparison_data[topic]['cpp'][:self.samples]
        python_values = self.comparison_data[topic]['python'][:self.samples]
        
        if len(cpp_values) < self.samples or len(python_values) < self.samples:
            return
        
        # Calculate differences
        differences = []
        for cpp_val, py_val in zip(cpp_values, python_values):
            diff = abs(cpp_val - py_val)
            differences.append(diff)
        
        max_diff = max(differences) if differences else 0
        avg_diff = np.mean(differences) if differences else 0
        
        # Check if within tolerance
        cpp_array = np.array(cpp_values)
        python_array = np.array(python_values)
        
        # Calculate relative error where C++ value is not zero
        relative_errors = []
        for cpp_val, py_val in zip(cpp_values, python_values):
            if abs(cpp_val) > 1e-10:  # Avoid division by zero
                rel_error = abs(cpp_val - py_val) / abs(cpp_val)
                relative_errors.append(rel_error)
        
        max_rel_error = max(relative_errors) if relative_errors else 0
        avg_rel_error = np.mean(relative_errors) if relative_errors else 0
        
        # Determine pass/fail
        passed = max_diff <= self.tolerance or max_rel_error <= self.tolerance
        
        self.get_logger().info(f"\n=== Comparison Results for {topic} ===")
        self.get_logger().info(f"Samples compared: {len(cpp_values)}")
        self.get_logger().info(f"Max absolute difference: {max_diff:.6e}")
        self.get_logger().info(f"Average absolute difference: {avg_diff:.6e}")
        self.get_logger().info(f"Max relative error: {max_rel_error:.6e}")
        self.get_logger().info(f"Average relative error: {avg_rel_error:.6e}")
        self.get_logger().info(f"Tolerance: {self.tolerance:.6e}")
        self.get_logger().info(f"Status: {'PASS' if passed else 'FAIL'}")
        
        # Print first few samples for debugging
        if not passed:
            self.get_logger().info("First 5 samples:")
            self.get_logger().info("C++:    %s", [f"{v:.3f}" for v in cpp_values[:5]])
            self.get_logger().info("Python: %s", [f"{v:.3f}" for v in python_values[:5]])
    

def main(args=None):
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Compare C++ and Python processing node outputs')
    parser.add_argument('--samples', type=int, default=100, help='Number of samples to compare')
    parser.add_argument('--tolerance', type=float, default=1e-6, help='Maximum allowed difference/tolerance')
    
    # Parse known args (remove unknown args that ROS might add)
    known_args, ros_args = parser.parse_known_args()
    
    rclpy.init(args=ros_args)
    
    try:
        node = ComparisonNode(samples=known_args.samples, tolerance=known_args.tolerance)
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()