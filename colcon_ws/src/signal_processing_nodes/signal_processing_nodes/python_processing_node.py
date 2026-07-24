#!/usr/bin/env python3
"""
Python Processing Node for Signal Processing Pipeline.

This node subscribes to integer and floating-point sensor streams,
applies moving average and low-pass filters using the pybind11 bindings
of the standalone C++ library, and publishes the filtered results.

Requirements:
- The custom_lib must be built and the Python modules (py_filter, py_moving_average) available
- ROS2 environment properly sourced

Usage:
    ros2 run signal_processing_nodes python_processing_node
    
    # With parameters
    ros2 run signal_processing_nodes python_processing_node --ros-args -p ma_window_size:=10 -p lp_cutoff:=5.0
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float32
import sys
import os

# Add custom_lib to Python path for imports
custom_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               '../../../..', 'custom_lib')
if os.path.exists(custom_lib_path):
    sys.path.insert(0, custom_lib_path)


class PythonProcessingNode(Node):
    """
    Python ROS2 node that processes sensor streams using pybind11 filters.
    
    Subscribes to:
        - /encoder_count (Int32): Integer sensor stream
        - /accel_x_mss (Float32): Floating-point sensor stream
        
    Publishes:
        - /filtered_encoder_count (Int32): Filtered integer stream
        - /filtered_accel_x_mss (Float32): Filtered floating-point stream
        - /ma_encoder (Int32): Moving average of integer stream
        - /ma_accel (Float32): Moving average of float stream
        - /lp_encoder (Int32): Low-pass filtered integer stream  
        - /lp_accel (Float32): Low-pass filtered float stream
    """
    
    def __init__(self):
        super().__init__('python_processing_node')
        
        # Declare parameters with defaults
        self.declare_parameter('ma_window_size', 5)
        self.declare_parameter('lp_cutoff_hz', 10.0)
        self.declare_parameter('ma_window_duration_ms', 100.0)  # For time-based MA
        self.declare_parameter('use_time_based_ma', False)
        self.declare_parameter('fixed_point_bits', 16)  # Q-format fractional bits
        self.declare_parameter('timeout_seconds', 10.0)
        
        # Get parameter values
        self.ma_window_size = self.get_parameter('ma_window_size').get_parameter_value().integer_value
        self.lp_cutoff_hz = self.get_parameter('lp_cutoff_hz').get_parameter_value().double_value
        self.ma_window_duration_ms = self.get_parameter('ma_window_duration_ms').get_parameter_value().double_value
        self.use_time_based_ma = self.get_parameter('use_time_based_ma').get_parameter_value().bool_value
        self.fixed_point_bits = self.get_parameter('fixed_point_bits').get_parameter_value().integer_value
        self.timeout_seconds = self.get_parameter('timeout_seconds').get_parameter_value().double_value
        
        self.get_logger().info(f"Parameters: MA window={self.ma_window_size}, LP cutoff={self.lp_cutoff_hz}Hz, "
                              f"Time-based MA={self.use_time_based_ma}, FP bits={self.fixed_point_bits}")
        
        # Import filter modules (will fail if not built)
        self._init_filters()
        
        # Store timestamps for dt calculation
        self.last_encoder_time = None
        self.last_accel_time = None
        
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
        self.filtered_encoder_pub = self.create_publisher(Int32, 'filtered_encoder_count', 10)
        self.filtered_accel_pub = self.create_publisher(Float32, 'filtered_accel_x_mss', 10)
        self.ma_encoder_pub = self.create_publisher(Int32, 'ma_encoder', 10)
        self.ma_accel_pub = self.create_publisher(Float32, 'ma_accel', 10)
        self.lp_encoder_pub = self.create_publisher(Int32, 'lp_encoder', 10)
        self.lp_accel_pub = self.create_publisher(Float32, 'lp_accel', 10)
        
        self.get_logger().info("Python processing node initialized")
        self.get_logger().info("Subscribed to: /encoder_count, /accel_x_mss")
        self.get_logger().info("Publishing to: /filtered_encoder_count, /filtered_accel_x_mss, /ma_encoder, /ma_accel, /lp_encoder, /lp_accel")
    
    def _init_filters(self):
        """Initialize filter instances with error handling."""
        try:
            # Import and create moving average filters
            import py_moving_average as pma
            from py_moving_average.FixedMovingAverage.mediumbuffer import Double as MA_Double
            from py_moving_average.FixedMovingAverage.mediumbuffer import Integer as MA_Int
            
            self.ma_encoder = MA_Int(self.ma_window_size)
            self.ma_accel = MA_Double(self.ma_window_size)
            
            # If using time-based moving average
            if self.use_time_based_ma:
                from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Double as TD_MA_Double
                from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Integer as TD_MA_Int
                from datetime import timedelta
                
                self.ma_encoder = TD_MA_Int(self.ma_window_size, timedelta(milliseconds=self.ma_window_duration_ms))
                self.ma_accel = TD_MA_Double(self.ma_window_size, timedelta(milliseconds=self.ma_window_duration_ms))
            
            self.get_logger().info("Moving average filters created")
            
        except ImportError as e:
            self.get_logger().error(f"Failed to import moving average modules: {e}")
            raise
            
        try:
            # Import and create low-pass filters
            import py_filter
            
            # Select fixed-point filter based on fractional bits
            if self.fixed_point_bits == 8:
                self.lp_encoder = py_filter.FixedPointLowPassFilter_24_8(cutoff_freq_hz=self.lp_cutoff_hz, 
                                                                           fractional_bits=8, 
                                                                           timeout_seconds=self.timeout_seconds)
            elif self.fixed_point_bits == 16:
                self.lp_encoder = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=self.lp_cutoff_hz, 
                                                                           fractional_bits=16, 
                                                                           timeout_seconds=self.timeout_seconds)
            elif self.fixed_point_bits == 24:
                self.lp_encoder = py_filter.FixedPointLowPassFilter_8_24(cutoff_freq_hz=self.lp_cutoff_hz, 
                                                                          fractional_bits=24, 
                                                                          timeout_seconds=self.timeout_seconds)
            elif self.fixed_point_bits == 30:
                self.lp_encoder = py_filter.FixedPointLowPassFilter_2_30(cutoff_freq_hz=self.lp_cutoff_hz, 
                                                                          fractional_bits=30, 
                                                                          timeout_seconds=self.timeout_seconds)
            else:
                # Default to Q16.16
                self.lp_encoder = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=self.lp_cutoff_hz, 
                                                                           fractional_bits=16, 
                                                                           timeout_seconds=self.timeout_seconds)
            
            self.lp_accel = py_filter.FloatLowPassFilter_Double(cutoff_freq_hz=self.lp_cutoff_hz, 
                                                                timeout_seconds=self.timeout_seconds)
            
            self.get_logger().info("Low-pass filters created")
            self.get_logger().info(f"  Encoder filter: {type(self.lp_encoder).__name__} (Q{self.fixed_point_bits})")
            self.get_logger().info(f"  Accel filter: {type(self.lp_accel).__name__}")
            
        except ImportError as e:
            self.get_logger().error(f"Failed to import filter modules: {e}")
            raise
    
    def _get_timestamp_seconds(self, msg):
        """Extract timestamp from message header or use current time."""
        # ROS2 messages have header.stamp if they have a header
        if hasattr(msg, 'header') and hasattr(msg.header, 'stamp'):
            # Convert ROS2 time to seconds
            from rclpy.time import Time
            stamp = msg.header.stamp
            return stamp.nanoseconds / 1e9
        else:
            # Use system time as fallback
            import time
            return time.time()
    
    def encoder_callback(self, msg):
        """Callback for encoder (integer) stream."""
        import time
        
        current_time = time.time()
        value = msg.data
        
        # Calculate dt if we have a previous timestamp
        dt = None
        if self.last_encoder_time is not None:
            dt = current_time - self.last_encoder_time
        self.last_encoder_time = current_time
        
        # Apply moving average
        ma_result = self.ma_encoder.update(value)
        
        # Apply low-pass filter
        # For fixed-point filters, we need to handle dt properly
        if hasattr(self.lp_encoder, 'update'):
            if dt is not None and hasattr(self.lp_encoder, 'update'):
                # Use timestamp-aware update if available
                from datetime import datetime, timedelta
                timestamp = datetime.fromtimestamp(current_time)
                lp_result = self.lp_encoder.update(value, timestamp)
            else:
                # Use simple update
                lp_result = self.lp_encoder.update(value)
        else:
            lp_result = value  # Fallback
        
        # For now, just use moving average as filtered result
        # (In a real implementation, you might combine both)
        filtered_result = ma_result
        
        # Publish results
        self.ma_encoder_pub.publish(Int32(data=int(ma_result)))
        self.lp_encoder_pub.publish(Int32(data=int(lp_result)))
        self.filtered_encoder_pub.publish(Int32(data=int(filtered_result)))
        
        # Log occasionally
        if self.ma_encoder.currentSize() % 10 == 0:
            self.get_logger().debug(f"Encoder processing: raw={value}, ma={ma_result:.1f}, lp={lp_result}")
    
    def accel_callback(self, msg):
        """Callback for acceleration (float) stream."""
        import time
        
        current_time = time.time()
        value = msg.data
        
        # Calculate dt if we have a previous timestamp
        dt = None
        if self.last_accel_time is not None:
            dt = current_time - self.last_accel_time
        self.last_accel_time = current_time
        
        # Apply moving average
        ma_result = self.ma_accel.update(value)
        
        # Apply low-pass filter
        if hasattr(self.lp_accel, 'update'):
            if dt is not None and hasattr(self.lp_accel, 'update'):
                from datetime import datetime, timedelta
                timestamp = datetime.fromtimestamp(current_time)
                lp_result = self.lp_accel.update(value, timestamp)
            else:
                # Use simple update
                lp_result = self.lp_accel.update(value)
        else:
            lp_result = value  # Fallback
        
        # For now, just use moving average as filtered result
        filtered_result = ma_result
        
        # Publish results
        self.ma_accel_pub.publish(Float32(data=float(ma_result)))
        self.lp_accel_pub.publish(Float32(data=float(lp_result)))
        self.filtered_accel_pub.publish(Float32(data=float(filtered_result)))
        
        # Log occasionally
        if self.ma_accel.currentSize() % 10 == 0:
            self.get_logger().debug(f"Accel processing: raw={value:.3f}, ma={ma_result:.3f}, lp={lp_result:.3f}")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = PythonProcessingNode()
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