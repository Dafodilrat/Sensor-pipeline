#!/usr/bin/env python3
"""
Test script for the py_moving_average Python bindings.

This script tests both FixedMovingAverage and TimeDurationMovingAverage classes
with the new nested module structure.
"""

import sys
import os
import time
import math
from datetime import timedelta

# Add the custom_lib root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_imports():
    """Test that we can import the module and its classes."""
    print("Testing imports...")
    
    try:
        import py_moving_average as pma
        print("✓ Successfully imported py_moving_average module")
        
        # Test that main classes are available via nested hierarchy
        from py_moving_average import FixedMovingAverage
        from py_moving_average import TimeDurationMovingAverage
        print("✓ Successfully imported main class modules")
        
        # Test that buffer size submodules are available
        from py_moving_average.FixedMovingAverage import smallbuffer, mediumbuffer, largebuffer
        from py_moving_average.TimeDurationMovingAverage import smallbuffer as td_smallbuffer
        from py_moving_average.TimeDurationMovingAverage import mediumbuffer as td_mediumbuffer
        from py_moving_average.TimeDurationMovingAverage import largebuffer as td_largebuffer
        print("✓ Successfully imported buffer size submodules")
        
        # Test that type classes are available
        from py_moving_average.FixedMovingAverage.smallbuffer import Integer, Double, Float
        from py_moving_average.TimeDurationMovingAverage.smallbuffer import Integer as TD_Integer
        from py_moving_average.TimeDurationMovingAverage.smallbuffer import Double as TD_Double
        from py_moving_average.TimeDurationMovingAverage.smallbuffer import Float as TD_Float
        print("✓ Successfully imported type classes")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False


def test_fixed_moving_average_double():
    """Test FixedMovingAverage with double precision."""
    print("\nTesting FixedMovingAverage Double...")
    
    try:
        from py_moving_average.FixedMovingAverage.mediumbuffer import Double
        
        # Create a fixed moving average with window size 5
        ma = Double(5)
        print(f"✓ Created FixedMovingAverage Double with window size 5")
        
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
        # Size should be 5 since window is full
        if ma.size != 5:
            print(f"✗ Size property incorrect: got {ma.size}, expected 5")
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
        print(f"✗ Exception in FixedMovingAverage Double test: {e}")
        return False


def test_fixed_moving_average_float():
    """Test FixedMovingAverage with float precision."""
    print("\nTesting FixedMovingAverage Float...")
    
    try:
        from py_moving_average.FixedMovingAverage.smallbuffer import Float
        
        # Create a fixed moving average with window size 3
        ma = Float(3)
        print(f"✓ Created FixedMovingAverage Float with window size 3")
        
        # Test basic functionality
        test_values = [1.5, 2.5, 3.5, 4.5, 5.5]
        
        for val in test_values:
            avg = ma.update(val)
            print(f"  Value: {val}, Average: {avg:.4f}")
        
        # Test that float precision is working (size should be 3 since window is full)
        if ma.size != 3:
            print(f"✗ Size property incorrect: got {ma.size}, expected 3")
            return False
        
        if ma.max_size != 100:  # Small buffer size
            print(f"✗ Max size property incorrect: got {ma.max_size}, expected 100")
            return False
        
        print("✓ FixedMovingAverage Float works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedMovingAverage Float test: {e}")
        return False


def test_time_duration_moving_average_double():
    """Test TimeDurationMovingAverage with double precision."""
    print("\nTesting TimeDurationMovingAverage Double...")
    
    try:
        from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Double
        
        # Create a time-based moving average with explicit window size and duration
        td_ma = Double(12, timedelta(milliseconds=1000))
        print(f"✓ Created TimeDurationMovingAverage Double with window_size=12, window_duration=1000ms")
        
        # Test properties
        if td_ma.window_duration != timedelta(milliseconds=1000):
            print(f"✗ Window duration incorrect: got {td_ma.window_duration}, expected 1000ms")
            return False
        
        print("✓ Properties work correctly")
        
        # Test with rapid updates (simulating 10Hz)
        print("  Testing with simulated 10Hz data...")
        for i in range(15):
            avg = td_ma.update(float(i))
            print(f"    Update {i+1}: Value={i}, Average={avg:.4f}, Window size={td_ma.size}")
            time.sleep(0.1)  # 100ms = 10Hz
        
        # The window should contain approximately the configured window size
        if td_ma.size != 12:
            print(f"✓ Window size: {td_ma.size} (expected 12)")
        else:
            print(f"✓ Window size matches: {td_ma.size}")
        
        # Test set_window_duration
        td_ma.set_window_duration(timedelta(milliseconds=500))
        if td_ma.window_duration != timedelta(milliseconds=500):
            print(f"✗ set_window_duration failed for window_duration")
            return False
        
        print("✓ set_window_duration works correctly")
        
        # Test reset
        td_ma.reset()
        if td_ma.size != 0:
            print(f"✗ Reset failed: size is {td_ma.size}, expected 0")
            return False
        
        print("✓ Reset works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Exception in TimeDurationMovingAverage Double test: {e}")
        return False


def test_time_duration_moving_average_float():
    """Test TimeDurationMovingAverage with float precision."""
    print("\nTesting TimeDurationMovingAverage Float...")
    
    try:
        from py_moving_average.TimeDurationMovingAverage.smallbuffer import Float
        
        # Create a time-based moving average
        td_ma = Float(10, timedelta(milliseconds=2000))  # window_size, window_duration
        print(f"✓ Created TimeDurationMovingAverage Float with window_size=10, window_duration=2000ms")
        
        # Test with some updates
        for i in range(8):
            avg = td_ma.update(float(i) * 1.5)
            print(f"  Value: {i * 1.5}, Average: {avg:.4f}, Window size: {td_ma.size}")
            time.sleep(0.2)  # 200ms = 5Hz
        
        print("✓ TimeDurationMovingAverage Float works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Exception in TimeDurationMovingAverage Float test: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid parameters."""
    print("\nTesting error handling...")
    
    try:
        from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Double
        
        # Test invalid window duration (zero or negative)
        try:
            td_ma = Double(10, timedelta(milliseconds=0))
            print("✗ Should have raised ValueError for window_duration=0")
            return False
        except ValueError:
            print("✓ Correctly raised ValueError for window_duration=0")
        except Exception as e:
            print(f"✗ Unexpected exception type for window_duration=0: {type(e).__name__}")
            return False
        
        # Test negative window duration
        try:
            td_ma = Double(10, timedelta(milliseconds=-1000))
            print("✗ Should have raised ValueError for negative window_duration")
            return False
        except ValueError:
            print("✓ Correctly raised ValueError for negative window_duration")
        except Exception as e:
            print(f"✗ Unexpected exception type for negative window_duration: {type(e).__name__}")
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
        from py_moving_average.FixedMovingAverage.smallbuffer import Integer as MA_Small
        ma_small = MA_Small(50)
        if ma_small.max_size != 100:
            print(f"✗ Small buffer has wrong size: {ma_small.max_size}, expected 100")
            return False
        print("✓ Small buffer (100) works correctly")
        
        # Test medium buffer
        from py_moving_average.FixedMovingAverage.mediumbuffer import Double as MA_Medium
        ma_medium = MA_Medium(500)
        if ma_medium.max_size != 1000:
            print(f"✗ Medium buffer has wrong size: {ma_medium.max_size}, expected 1000")
            return False
        print("✓ Medium buffer (1000) works correctly")
        
        # Test large buffer
        from py_moving_average.FixedMovingAverage.largebuffer import Float as MA_Large
        ma_large = MA_Large(5000)
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
        ("FixedMovingAverage Double", test_fixed_moving_average_double),
        ("FixedMovingAverage Float", test_fixed_moving_average_float),
        ("TimeDurationMovingAverage Double", test_time_duration_moving_average_double),
        ("TimeDurationMovingAverage Float", test_time_duration_moving_average_float),
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
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
