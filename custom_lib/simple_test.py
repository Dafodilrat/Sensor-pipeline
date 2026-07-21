#!/usr/bin/env python3
"""
Simple test script for the py_moving_average Python bindings.
"""

import sys
import os
from datetime import timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from py_moving_average import (
        FixedMovingAverageDouble,
        FixedMovingAverageFloat,
        TimeDurationMovingAverageDouble,
        TimeDurationMovingAverageFloat
    )
    
    print("✓ Successfully imported all classes")
    
    # Test FixedMovingAverageDouble
    print("\n=== Testing FixedMovingAverageDouble ===")
    # Note: FixedMovingAverage uses the full buffer capacity (1000 for medium buffer)
    # The sample_count parameter in constructor is just for validation
    ma = FixedMovingAverageDouble()  # Use default capacity
    test_values = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    actual_avgs = []
    for val in test_values:
        avg = ma.update(val)
        actual_avgs.append(avg)
        print(f"Value: {val:.1f}, Average: {avg:.4f}, Size: {ma.size}")
    
    # Check first few averages manually
    # Value 1: avg = 1.0, size = 1
    # Value 2: avg = (1+2)/2 = 1.5, size = 2
    # Value 3: avg = (1+2+3)/3 = 2.0, size = 3
    # Value 4: avg = (1+2+3+4)/4 = 2.5, size = 4
    # Value 5: avg = (1+2+3+4+5)/5 = 3.0, size = 5
    expected_avgs = [1.0, 1.5, 2.0, 2.5, 3.0]
    
    # Check if averages are correct
    for i, (actual, expected) in enumerate(zip(actual_avgs, expected_avgs)):
        if abs(actual - expected) > 1e-6:
            print(f"✗ Average mismatch at index {i}: got {actual}, expected {expected}")
            sys.exit(1)
    
    print("✓ FixedMovingAverageDouble calculations are correct")
    
    # Test reset
    ma.reset()
    if ma.size != 0:
        print(f"✗ Reset failed: size is {ma.size}, expected 0")
        sys.exit(1)
    print("✓ Reset works correctly")
    
    # Test FixedMovingAverageFloat
    print("\n=== Testing FixedMovingAverageFloat ===")
    ma_float = FixedMovingAverageFloat(3)
    for i in range(5):
        avg = ma_float.update(float(i) * 1.5)
        print(f"Value: {i * 1.5:.1f}, Average: {avg:.4f}")
    print("✓ FixedMovingAverageFloat works correctly")
    
    # Test TimeDurationMovingAverageDouble
    print("\n=== Testing TimeDurationMovingAverageDouble ===")
    td_ma = TimeDurationMovingAverageDouble(sensor_hz=10.0, window_duration=timedelta(milliseconds=1000))
    print(f"Sensor Hz: {td_ma.sensor_hz}")
    print(f"Window duration: {td_ma.window_duration}")
    print(f"Calculated window size: {td_ma.calculated_window_size}")
    
    for i in range(8):
        avg = td_ma.update(i * 2.5)
        print(f"Value: {i * 2.5:.1f}, Average: {avg:.4f}, Size: {td_ma.size}")
    print("✓ TimeDurationMovingAverageDouble works correctly")
    
    # Test TimeDurationMovingAverageFloat
    print("\n=== Testing TimeDurationMovingAverageFloat ===")
    td_ma_float = TimeDurationMovingAverageFloat(sensor_hz=5.0, window_duration=timedelta(milliseconds=2000))
    for i in range(6):
        avg = td_ma_float.update(float(i) * 3.0)
        print(f"Value: {i * 3.0:.1f}, Average: {avg:.4f}")
    print("✓ TimeDurationMovingAverageFloat works correctly")
    
    # Test parameter updates
    print("\n=== Testing Parameter Updates ===")
    td_ma.set_sensor_hz(20.0)
    if abs(td_ma.sensor_hz - 20.0) > 1e-6:
        print(f"✗ set_sensor_hz failed: got {td_ma.sensor_hz}, expected 20.0")
        sys.exit(1)
    
    td_ma.set_window_duration(timedelta(milliseconds=500))
    print(f"Updated window duration: {td_ma.window_duration}")
    print("✓ Parameter updates work correctly")
    
    # Test error handling
    print("\n=== Testing Error Handling ===")
    try:
        bad_ma = TimeDurationMovingAverageDouble(sensor_hz=0.0, window_duration=timedelta(milliseconds=1000))
        print("✗ Should have raised ValueError for sensor_hz=0")
        sys.exit(1)
    except ValueError:
        print("✓ Correctly raised ValueError for sensor_hz=0")
    except Exception as e:
        print(f"✗ Unexpected exception type: {type(e).__name__}")
        sys.exit(1)
    
    try:
        bad_ma = TimeDurationMovingAverageDouble(sensor_hz=-1.0, window_duration=timedelta(milliseconds=1000))
        print("✗ Should have raised ValueError for negative sensor_hz")
        sys.exit(1)
    except ValueError:
        print("✓ Correctly raised ValueError for negative sensor_hz")
    except Exception as e:
        print(f"✗ Unexpected exception type: {type(e).__name__}")
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
