#!/usr/bin/env python3
"""
Demonstration script for Python bindings of Moving Average Library.

This script shows how to use both FixedMovingAverage and TimeDurationMovingAverage
classes from Python.
"""

import time
from py_moving_average import (
    FixedMovingAverageDouble, 
    FixedMovingAverageFloat,
    TimeDurationMovingAverageDouble,
    TimeDurationMovingAverageFloat
)


def demo_fixed_moving_average():
    """Demonstrate FixedMovingAverage usage."""
    print("=" * 60)
    print("FIXED MOVING AVERAGE DEMO")
    print("=" * 60)
    
    # Create a fixed moving average with window size of 5
    print("Creating FixedMovingAverageDouble with window size = 5")
    ma = FixedMovingAverageDouble(5)
    
    print(f"Initial size: {ma.size}")
    print(f"Maximum capacity: {ma.max_size}")
    print()
    
    # Update with values and show running average
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    print("Updating with values 1.0 to 10.0:")
    
    for val in values:
        avg = ma.update(val)
        print(f"  Value: {val:2.0f}, Current Average: {avg:.4f}, Window Size: {ma.size}")
    
    print()
    
    # Test reset
    print("Resetting the moving average...")
    ma.reset()
    print(f"Size after reset: {ma.size}")
    print()


def demo_time_duration_moving_average():
    """Demonstrate TimeDurationMovingAverage usage."""
    print("=" * 60)
    print("TIME DURATION MOVING AVERAGE DEMO")
    print("=" * 60)
    
    # Create a time-based moving average: 10Hz sensor, 1 second window
    print("Creating TimeDurationMovingAverageDouble for 10Hz sensor with 1 second window")
    td_ma = TimeDurationMovingAverageDouble(sensor_hz=10.0, window_duration=1000)
    
    print(f"Sensor Hz: {td_ma.sensor_hz}")
    print(f"Window duration: {td_ma.window_duration}")
    print(f"Calculated window size: {td_ma.calculated_window_size}")
    print(f"Maximum capacity: {td_ma.max_size}")
    print()
    
    # Simulate sensor data at approximately 10Hz
    print("Simulating sensor data at ~10Hz:")
    
    for i in range(15):
        avg = td_ma.update(i)
        print(f"  Update {i+1}: Value={i:2.0f}, Average={avg:.4f}, Window Size={td_ma.size}")
        time.sleep(0.1)  # 100ms ≈ 10Hz
    
    print()
    
    # Test parameter updates
    print("Updating parameters to 20Hz, 0.5 second window...")
    td_ma.set_parameters(sensor_hz=20.0, window_duration=500)
    print(f"New sensor Hz: {td_ma.sensor_hz}")
    print(f"New window duration: {td_ma.window_duration}")
    print(f"New calculated window size: {td_ma.calculated_window_size}")
    print()
    
    # Reset and test again
    print("Resetting and starting fresh...")
    td_ma.reset()
    print(f"Size after reset: {td_ma.size}")
    print()


def demo_float_precision():
    """Demonstrate float precision versions."""
    print("=" * 60)
    print("FLOAT PRECISION DEMO")
    print("=" * 60)
    
    # Fixed moving average with float
    print("Creating FixedMovingAverageFloat with window size = 4")
    ma_float = FixedMovingAverageFloat(4)
    
    values = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    print("Updating with float values:")
    
    for val in values:
        avg = ma_float.update(val)
        print(f"  Value: {val}, Average: {avg:.4f}, Window Size: {ma_float.size}")
    
    print()
    
    # Time duration moving average with float
    print("Creating TimeDurationMovingAverageFloat")
    td_ma_float = TimeDurationMovingAverageFloat(sensor_hz=5.0, window_duration=2000)
    
    print(f"Sensor Hz: {td_ma_float.sensor_hz}")
    print(f"Window duration: {td_ma_float.window_duration}")
    print()
    
    print("Updating with float values:")
    for i in range(6):
        avg = td_ma_float.update(i * 1.5)
        print(f"  Value: {i * 1.5}, Average: {avg:.4f}, Window Size: {td_ma_float.size}")
    
    print()


def demo_buffer_sizes():
    """Demonstrate different buffer size variants."""
    print("=" * 60)
    print("BUFFER SIZE VARIANTS DEMO")
    print("=" * 60)
    
    from py_moving_average import (
        FixedMovingAverageDouble_Small,
        FixedMovingAverageDouble_Large
    )
    
    # Small buffer (100 samples)
    print("Creating FixedMovingAverageDouble_Small")
    ma_small = FixedMovingAverageDouble_Small(50)
    print(f"Max capacity: {ma_small.max_size}")
    
    # Large buffer (10000 samples)
    print("Creating FixedMovingAverageDouble_Large")
    ma_large = FixedMovingAverageDouble_Large(5000)
    print(f"Max capacity: {ma_large.max_size}")
    
    print()


def main():
    """Run all demonstrations."""
    demo_fixed_moving_average()
    demo_time_duration_moving_average()
    demo_float_precision()
    demo_buffer_sizes()
    
    print("=" * 60)
    print("DEMOS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
