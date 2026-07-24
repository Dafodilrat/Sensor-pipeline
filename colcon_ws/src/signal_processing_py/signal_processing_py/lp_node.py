#!/usr/bin/env python3
"""
Low Pass Filter Processing Node for Signal Processing Pipeline.

This node subscribes to integer and floating-point sensor streams,
applies LOW PASS filters using the pybind11 bindings
of the standalone C++ library, and publishes the filtered results.

Requirements:
- The custom_lib must be built and the Python modules (py_filter) available
- ROS2 environment properly sourced

Usage:
    ros2 run signal_processing_py lp_node
    
    # With parameters
    ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=10.0 -p fixed_point_bits:=16 -p timeout_seconds:=10.0
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import sys
import os

# Add custom_lib to Python path for imports
custom_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               '../../../../', 'custom_lib')
if os.path.exists(custom_lib_path):
    sys.path.insert(0, custom_lib_path)


class LPNode(Node):
    """
    Python ROS2 node that applies LOW PASS filters to sensor streams.
    
    Subscribes to:
        - /encoder_count (Int32): Integer sensor stream
        - /accel_x_mss (Float32): Floating-point sensor stream
        
    Publishes:
        - /lp_encoder (Int32): Low-pass filtered integer stream
        - /lp_accel (Float32): Low-pass filtered float stream
    """
    
    def __init__(self):
        super().__init__('lp_node')
        
        # Declare parameters with defaults
        self.declare_parameter('lp_cutoff_hz', 10.0)
        self.declare_parameter('fixed_point_bits', 16)
        self.declare_parameter('timeout_seconds', 10.0)
        
        # Get parameter values
        self.lp_cutoff_hz = self.get_parameter('lp_cutoff_hz').get_parameter_value().double_value
        self.fixed_point_bits = self.get_parameter('fixed_point_bits').get_parameter_value().integer_value
        self.timeout_seconds = self.get_parameter('timeout_seconds').get_parameter_value().double_value
        
        self.get_logger().info(f"LP Parameters: cutoff={self.lp_cutoff_hz}Hz, FP bits={self.fixed_point_bits}, timeout={self.timeout_seconds}s")
        
        # Import filter modules (will fail if not built)
        self._init_filters()
        
        # Create subscribers
        self.encoder_sub = self.create_subscription(
            Int32, 
            'encoder_count', 
            self.encoder_callback, 
            10
        )
        
        self.accel_sub = self.create_subscription(
            Float32, 
            'accel_x_mss', 
            self.accel_callback, 
            10
        )
        
        # Create publishers
        self.lp_encoder_pub = self.create_publisher(Int32, 'lp_encoder', 10)
        self.lp_accel_pub = self.create_publisher(Float32, 'lp_accel', 10)
        
        self.get_logger().info("LP node initialized")
        self.get_logger().info("Subscribed to: /encoder_count, /accel_x_mss")
        self.get_logger().info("Publishing to: /lp_encoder, /lp_accel")
        
        # Counters for occasional logging
        self.encoder_update_count = 0
        self.accel_update_count = 0
    
    def _init_filters(self):
        """Initialize low-pass filter instances with error handling."""
        try:
            # Import and create low-pass filters based on fixed-point bits
            if self.fixed_point_bits == 8:
                from py_filter import FixedPointLowPassFilter_24_8 as LP_Int
                self.lp_encoder = LP_Int(self.lp_cutoff_hz, 8, self.timeout_seconds)
            elif self.fixed_point_bits == 16:
                from py_filter import FixedPointLowPassFilter_16_16 as LP_Int
                self.lp_encoder = LP_Int(self.lp_cutoff_hz, 16, self.timeout_seconds)
            elif self.fixed_point_bits == 24:
                from py_filter import FixedPointLowPassFilter_8_24 as LP_Int
                self.lp_encoder = LP_Int(self.lp_cutoff_hz, 24, self.timeout_seconds)
            elif self.fixed_point_bits == 30:
                from py_filter import FixedPointLowPassFilter_2_30 as LP_Int
                self.lp_encoder = LP_Int(self.lp_cutoff_hz, 30, self.timeout_seconds)
            else:
                # Default to 16
                from py_filter import FixedPointLowPassFilter_16_16 as LP_Int
                self.lp_encoder = LP_Int(self.lp_cutoff_hz, 16, self.timeout_seconds)
            
            # Float low-pass filter
            from py_filter import FloatLowPassFilter_Double as LP_Double
            self.lp_accel = LP_Double(self.lp_cutoff_hz, self.timeout_seconds)
            
            self.get_logger().info("Low-pass filters created with timeout")
            
        except ImportError as e:
            self.get_logger().error(f"Failed to import filter modules: {e}")
            raise
    
    def encoder_callback(self, msg):
        """Callback for encoder (integer) stream."""
        value = msg.data
        
        # Apply low-pass filter (uses system clock internally)
        lp_result = self.lp_encoder.update(value)
        
        # Increment counter
        self.encoder_update_count += 1
        
        # Publish results
        self.lp_encoder_pub.publish(Int32(data=int(lp_result)))
        
        # Log occasionally
        if self.encoder_update_count % 10 == 0:
            self.get_logger().debug(f"Encoder LP: raw={value}, lp={lp_result:.1f}")
    
    def accel_callback(self, msg):
        """Callback for acceleration (float) stream."""
        value = msg.data
        
        # Apply low-pass filter (uses system clock internally)
        lp_result = self.lp_accel.update(value)
        
        # Increment counter
        self.accel_update_count += 1
        
        # Publish results
        self.lp_accel_pub.publish(Float32(data=float(lp_result)))
        
        # Log occasionally
        if self.accel_update_count % 10 == 0:
            self.get_logger().debug(f"Accel LP: raw={value:.3f}, lp={lp_result:.3f}")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = LPNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
