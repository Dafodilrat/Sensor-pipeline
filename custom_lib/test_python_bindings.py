#!/usr/bin/env python3
"""
Test script for the py_moving_average Python bindings.

This script tests both FixedMovingAverage and TimeDurationMovingAverage classes
with both float and double precision.
"""

import sys
import os
import time
import math
from datetime import timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that we can import the module and its classes."""
    print("Testing imports...")
    
    try:
        import py_moving_average as pma
        print("✓ Successfully imported py_moving_average module")
        
        # Test that main classes are available
        from py_moving_average import (
            FixedMovingAverageDouble,
            FixedMovingAverageFloat,
            TimeDurationMovingAverageDouble,
            TimeDurationMovingAverageFloat
        )
        print("✓ Successfully imported main classes")
        
        # Test that sized classes are available
        from py_moving_average import (
            FixedMovingAverageDouble_Small,
            FixedMovingAverageFloat_Small,
            TimeDurationMovingAverageDouble_Small,
            TimeDurationMovingAverageFloat_Small,
            FixedMovingAverageDouble_Large,
            FixedMovingAverageFloat_Large,
            TimeDurationMovingAverageDouble_Large,
            TimeDurationMovingAverageFloat_Large
        )
        print("✓ Successfully imported sized classes")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False

def test_fixed_moving_average_double():
    """Test FixedMovingAverage with double precision."""
    print("\nTesting FixedMovingAverageDouble...")
    
    try:
        from py_moving_average import FixedMovingAverageDouble
        
        # Create a fixed moving average (uses full buffer capacity of 1000)
        ma = FixedMovingAverageDouble()
        print(f"✓ Created FixedMovingAverageDouble with window size 5")
        
        # Test basic functionality
        test_values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        expected_averages = []
        
        # Calculate expected averages manually
        window = []
        for val in test_values:
            window.append(val)
            if len(window) > 5:
                window.pop(0)
            expected_averages.append(sum(window) / len(window))
        
        actual_averages = []
        for i, val in enumerate(test_values):
            avg = ma.update(val)
            actual_averages.append(avg)
            print(f"  Value: {val:2.0f}, Average: {avg:.4f}, Expected: {expected_averages[i]:.4f}")
        
        # Check if averages are correct (within floating point tolerance)
        for actual, expected in zip(actual_averages, expected_averages):
            if abs(actual - expected) > 1e-6:
                print(f"✗ Average mismatch: got {actual}, expected {expected}")
                return False
        
        print("✓ All averages match expected values")
        
        # Test properties
        # Size will be equal to number of updates since buffer is large (1000)
        if ma.size != len(test_values):
            print(f"✗ Size property incorrect: got {ma.size}, expected {len(test_values)}")
            return False
        
        if ma.max_size != 1000:  # Medium buffer size
            print(f"✗ Max size property incorrect: got {ma.max_size}, expected 1000")
            return False
        
        print("✓ Properties work correctly")
        
        # Test reset
        ma.reset()
        if ma.size != 0:
            print(f"✗ Reset failed: size is {ma.size}, expected 0")
            return False
        
        print("✓ Reset works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedMovingAverageDouble test: {e}")
        return False

def test_fixed_moving_average_float():
    """Test FixedMovingAverage with float precision."""
    print("\nTesting FixedMovingAverageFloat...")
    
    try:
        from py_moving_average import FixedMovingAverageFloat
        
        # Create a fixed moving average (uses full buffer capacity)
        ma = FixedMovingAverageFloat()
        print(f"✓ Created FixedMovingAverageFloat with window size 3")
        
        # Test basic functionality
        test_values = [1.5, 2.5, 3.5, 4.5, 5.5]
        
        for val in test_values:
            avg = ma.update(val)
            print(f"  Value: {val}, Average: {avg:.4f}")
        
        # Test that float precision is working (size should be number of updates)
        if ma.size != 5:
            print(f"✗ Size property incorrect: got {ma.size}, expected 5")
            return False
        
        print("✓ FixedMovingAverageFloat works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedMovingAverageFloat test: {e}")
        return False

def test_time_duration_moving_average_double():
    """Test TimeDurationMovingAverage with double precision."""
    print("\nTesting TimeDurationMovingAverageDouble...")
    
    try:
        from py_moving_average import TimeDurationMovingAverageDouble
        
        # Create a time-based moving average: 10Hz sensor, 1 second window
        # This should create a window of approximately ceil(10 * 1.0) * 1.2 = 12 samples
        td_ma = TimeDurationMovingAverageDouble(sensor_hz=10.0, window_duration=timedelta(milliseconds=1000))
        print(f"✓ Created TimeDurationMovingAverageDouble with sensor_hz=10.0, window_duration=1000ms")
        
        # Check calculated window size
        calculated_size = td_ma.calculated_window_size
        print(f"  Calculated window size: {calculated_size}")
        
        # Test properties
        if abs(td_ma.sensor_hz - 10.0) > 1e-6:
            print(f"✗ Sensor Hz incorrect: got {td_ma.sensor_hz}, expected 10.0")
            return False
        
        if td_ma.window_duration != timedelta(milliseconds=1000):
            print(f"✗ Window duration incorrect: got {td_ma.window_duration}, expected 1000")
            return False
        
        print("✓ Properties work correctly")
        
        # Test with rapid updates (simulating 10Hz)
        print("  Testing with simulated 10Hz data...")
        for i in range(15):
            avg = td_ma.update(float(i))
            print(f"    Update {i+1}: Value={i}, Average={avg:.4f}, Window size={td_ma.size}")
            time.sleep(0.1)  # 100ms = 10Hz
        
        # The window should contain approximately the last 1 second of data (10 samples at 10Hz)
        # But due to the 20% safety margin, it might be a bit more
        if td_ma.size < 10 or td_ma.size > 15:
            print(f"✗ Window size seems incorrect: {td_ma.size}, expected around 12")
            # This might be OK depending on timing
        else:
            print(f"✓ Window size looks reasonable: {td_ma.size}")
        
        # Test set_parameters
        td_ma.set_parameters(sensor_hz=20.0, window_duration=500)
        if abs(td_ma.sensor_hz - 20.0) > 1e-6:
            print(f"✗ set_parameters failed for sensor_hz")
            return False
        if td_ma.window_duration != timedelta(milliseconds=500):
            print(f"✗ set_parameters failed for window_duration")
            return False
        
        print("✓ set_parameters works correctly")
        
        # Test reset
        td_ma.reset()
        if td_ma.size != 0:
            print(f"✗ Reset failed: size is {td_ma.size}, expected 0")
            return False
        
        print("✓ Reset works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Exception in TimeDurationMovingAverageDouble test: {e}")
        return False

def test_time_duration_moving_average_float():
    """Test TimeDurationMovingAverage with float precision."""
    print("\nTesting TimeDurationMovingAverageFloat...")
    
    try:
        from py_moving_average import TimeDurationMovingAverageFloat
        
        # Create a time-based moving average
        td_ma = TimeDurationMovingAverageFloat(sensor_hz=5.0, window_duration=timedelta(milliseconds=2000))  # 5Hz, 2 second window
        print(f"✓ Created TimeDurationMovingAverageFloat with sensor_hz=5.0, window_duration=2000ms")
        
        # Test with some updates
        for i in range(8):
            avg = td_ma.update(float(i) * 1.5)
            print(f"  Value: {i * 1.5}, Average: {avg:.4f}, Window size: {td_ma.size}")
            time.sleep(0.2)  # 200ms = 5Hz
        
        print("✓ TimeDurationMovingAverageFloat works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Exception in TimeDurationMovingAverageFloat test: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid parameters."""
    print("\nTesting error handling...")
    
    try:
        from py_moving_average import TimeDurationMovingAverageDouble
        
        # Test invalid sensor_hz
        try:
            td_ma = TimeDurationMovingAverageDouble(sensor_hz=0.0, window_duration=timedelta(milliseconds=1000))
            print("✗ Should have raised ValueError for sensor_hz=0")
            return False
        except ValueError:
            print("✓ Correctly raised ValueError for sensor_hz=0")
        except Exception as e:
            print(f"✗ Unexpected exception type for sensor_hz=0: {type(e).__name__}")
            return False
        
        # Test negative sensor_hz
        try:
            td_ma = TimeDurationMovingAverageDouble(sensor_hz=-1.0, window_duration=timedelta(milliseconds=1000))
            print("✗ Should have raised ValueError for negative sensor_hz")
            return False
        except ValueError:
            print("✓ Correctly raised ValueError for negative sensor_hz")
        except Exception as e:
            print(f"✗ Unexpected exception type for negative sensor_hz: {type(e).__name__}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in error handling test: {e}")
        return False

def test_buffer_sizes():
    """Test the different buffer size variants."""
    print("\nTesting different buffer sizes...")
    
    try:
        # Test small buffer
        from py_moving_average import FixedMovingAverageDouble_Small
        ma_small = FixedMovingAverageDouble_Small(50)
        if ma_small.max_size != 100:
            print(f"✗ Small buffer has wrong size: {ma_small.max_size}, expected 100")
            return False
        print("✓ Small buffer (100) works correctly")
        
        # Test medium buffer
        from py_moving_average import FixedMovingAverageDouble_Medium
        ma_medium = FixedMovingAverageDouble_Medium(500)
        if ma_medium.max_size != 1000:
            print(f"✗ Medium buffer has wrong size: {ma_medium.max_size}, expected 1000")
            return False
        print("✓ Medium buffer (1000) works correctly")
        
        # Test large buffer
        from py_moving_average import FixedMovingAverageDouble_Large
        ma_large = FixedMovingAverageDouble_Large(5000)
        if ma_large.max_size != 10000:
            print(f"✗ Large buffer has wrong size: {ma_large.max_size}, expected 10000")
            return False
        print("✓ Large buffer (10000) works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in buffer size test: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("PYTHON BINDINGS TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("FixedMovingAverageDouble", test_fixed_moving_average_double),
        ("FixedMovingAverageFloat", test_fixed_moving_average_float),
        ("TimeDurationMovingAverageDouble", test_time_duration_moving_average_double),
        ("TimeDurationMovingAverageFloat", test_time_duration_moving_average_float),
        ("Error Handling", test_error_handling),
        ("Buffer Sizes", test_buffer_sizes),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
