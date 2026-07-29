#!/usr/bin/env python3
"""
Time Duration Moving Average Processing Node for Signal Processing Pipeline.

This node subscribes to integer and floating-point sensor streams,
applies TIME DURATION moving average filters using the pybind11 bindings
of the standalone C++ library, and publishes the filtered results.

Requirements:
- The custom_lib must be built and the Python modules (py_moving_average) available
- ROS2 environment properly sourced

Usage:
    ros2 run signal_processing_py time_ma_node
    
    # With parameters
    ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=10 -p ma_window_duration_ms:=200 -p timeout_seconds:=0.15
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
from datetime import timedelta

# Use system-level py_moving_average import (installed via pip in Docker)
# If running locally without pip install, you may need:
#   export PYTHONPATH=/path/to/custom_lib:$PYTHONPATH


class TimeMANode(Node):
    """
    Python ROS2 node that applies TIME DURATION moving average filters to sensor streams.
    
    Subscribes to:
        - /encoder_count (Int32): Integer sensor stream
        - /accel_x_mss (Float32): Floating-point sensor stream
        
    Publishes:
        - /time_ma_encoder (Int32): Time-based moving average of integer stream
        - /time_ma_accel (Float32): Time-based moving average of float stream
    """
    
    def __init__(self):
        super().__init__('time_ma_node')
        
        # Declare parameters with defaults
        self.declare_parameter('ma_window_size', 5)
        self.declare_parameter('ma_window_duration_ms', 200.0)
        self.declare_parameter('timeout_seconds', 0.15)  # 150ms timeout for dropout gaps
        
        # Get parameter values
        self.ma_window_size = self.get_parameter('ma_window_size').get_parameter_value().integer_value
        self.ma_window_duration_ms = self.get_parameter('ma_window_duration_ms').get_parameter_value().double_value
        self.timeout_seconds = self.get_parameter('timeout_seconds').get_parameter_value().double_value
        
        # Convert to float for compatibility with our bindings
        self.ma_window_duration_ms = float(self.ma_window_duration_ms)
        self.timeout_seconds = float(self.timeout_seconds)
        
        self.get_logger().info(f"Time MA Parameters: window size={self.ma_window_size}, duration={self.ma_window_duration_ms}ms, timeout={self.timeout_seconds}s")
        
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
        self.ma_encoder_pub = self.create_publisher(Int32, 'time_ma_encoder', 10)
        self.ma_accel_pub = self.create_publisher(Float32, 'time_ma_accel', 10)
        
        self.get_logger().info("Time MA node initialized")
        self.get_logger().info("Subscribed to: /encoder_count, /accel_x_mss")
        self.get_logger().info("Publishing to: /time_ma_encoder, /time_ma_accel")
    
    def _init_filters(self):
        """Initialize time duration moving average filter instances with error handling."""
        try:
            # Import and create time-based moving average filters with timeout
            from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Float as TD_MA_Float
            from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Integer as TD_MA_Int
            
            self.ma_encoder = TD_MA_Int(self.ma_window_size, timedelta(milliseconds=self.ma_window_duration_ms), self.timeout_seconds)
            self.ma_accel = TD_MA_Float(self.ma_window_size, timedelta(milliseconds=self.ma_window_duration_ms), self.timeout_seconds)
            
            self.get_logger().info("Time duration moving average filters created with timeout")
            
        except ImportError as e:
            self.get_logger().error(f"Failed to import time duration moving average modules: {e}")
            raise
    
    def encoder_callback(self, msg):
        """Callback for encoder (integer) stream."""
        value = msg.data
        
        # Pass through raw value without filtering for encoder motor topic
        ma_result = float(value)
        
        # Publish raw value to time_ma_encoder topic
        self.ma_encoder_pub.publish(Int32(data=int(ma_result)))
        
        # Log occasionally
        if self.ma_encoder.current_size() % 10 == 0:
            self.get_logger().debug(f"Encoder passthrough: raw={value}, published={ma_result:.1f}")
    
    def accel_callback(self, msg):
        """Callback for acceleration (float) stream."""
        value = msg.data
        
        # Apply time-based moving average
        # Note: timestamps are managed internally by the filter
        ma_result = self.ma_accel.update(value)
        
        # Publish results
        self.ma_accel_pub.publish(Float32(data=float(ma_result)))
        
        # Log occasionally
        if self.ma_accel.current_size() % 10 == 0:
            self.get_logger().debug(f"Accel time MA: raw={value:.3f}, ma={ma_result:.3f}")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = TimeMANode()
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
