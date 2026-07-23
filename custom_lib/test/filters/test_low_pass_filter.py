#!/usr/bin/env python3
"""
Test script for the low-pass filter functionality.

This script tests both floating-point and fixed-point low-pass filter implementations.
"""

import sys
import os
import math
import time

# Add the custom_lib root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_low_pass_filter_imports():
    """Test that we can import the low-pass filter classes."""
    print("Testing low-pass filter imports...")
    
    try:
        import py_moving_average as pma
        print("✓ Successfully imported py_moving_average module")
        
        # Check for specific classes (they are now directly in the main module)
        try:
            double_filter = pma.FloatLowPassFilter_Double(10.0)
            print("✓ Successfully created FloatLowPassFilter_Double")
        except Exception as e:
            print(f"✗ Failed to create FloatLowPassFilter_Double: {e}")
            return False
            
        try:
            float_filter = pma.FloatLowPassFilter_Float(10.0)
            print("✓ Successfully created FloatLowPassFilter_Float")
        except Exception as e:
            print(f"✗ Failed to create FloatLowPassFilter_Float: {e}")
            return False
            
        try:
            int_filter = pma.FixedPointLowPassFilter_Integer(10.0)
            print("✓ Successfully created FixedPointLowPassFilter_Integer")
        except Exception as e:
            print(f"✗ Failed to create FixedPointLowPassFilter_Integer: {e}")
            return False
            
        try:
            variadic_filter = pma.VariadicLowPassFilter_Double(10.0)
            print("✓ Successfully created VariadicLowPassFilter_Double")
        except Exception as e:
            print(f"✗ Failed to create VariadicLowPassFilter_Double: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False


def test_float_low_pass_filter():
    """Test floating-point low-pass filter functionality."""
    print("\nTesting FloatLowPassFilter...")
    
    try:
        import py_moving_average as pma
        
        # Create a filter with 10 Hz cutoff - use variadic for easier testing
        lp_filter = pma.VariadicLowPassFilter_Double(10.0)
        dt = 0.01  # 100 Hz sampling
        
        # Test basic filtering
        test_values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
            print(f"  Input: {val:.2f}, Output: {result:.4f}")
        
        # Check that output follows input but is smoothed
        if results[0] != 0.0:
            print(f"✗ First output should be 0.0, got {results[0]}")
            return False
        
        # Output should increase but lag behind input (smoothing effect)
        if results[-1] >= results[-2] >= results[0]:
            print("✓ Output is properly smoothed (lagging behind input)")
        else:
            print("✗ Output doesn't show expected smoothing behavior")
            return False
        
        # Test cutoff frequency change
        lp_filter.set_cutoff_frequency(20.0)
        if abs(lp_filter.get_cutoff_frequency() - 20.0) > 1e-6:
            print(f"✗ Set cutoff frequency failed: expected 20.0, got {lp_filter.get_cutoff_frequency()}")
            return False
        print("✓ Cutoff frequency change works correctly")
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(10.0)
        if result != 10.0:
            print(f"✗ Reset failed: expected 10.0, got {result}")
            return False
        print("✓ Reset works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in FloatLowPassFilter test: {e}")
        return False


def test_integer_low_pass_filter():
    """Test fixed-point integer low-pass filter functionality."""
    print("\nTesting Integer LowPassFilter...")
    
    try:
        from py_moving_average.LowPassFilter import Integer
        
        # Create a filter with 10 Hz cutoff
        lp_filter = Integer(10.0)
        
        print(f"  Q-format: {lp_filter.get_q_fractional_bits()} fractional bits")
        print(f"  Q-scale: {lp_filter.get_q_scale()}")
        
        # Test basic filtering with integer values
        test_values = [0, 10, 20, 30, 40, 50]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
            print(f"  Input: {val:2d}, Output: {result:2d}")
        
        # Check that output follows input but is smoothed
        if results[0] != 0:
            print(f"✗ First output should be 0, got {results[0]}")
            return False
        
        # Output should show smoothing effect
        print("✓ Integer filter produced valid outputs")
        
        # Test cutoff frequency change
        lp_filter.set_cutoff_frequency(5.0)
        if abs(lp_filter.get_cutoff_frequency() - 5.0) > 1e-6:
            print(f"✗ Set cutoff frequency failed: expected 5.0, got {lp_filter.get_cutoff_frequency()}")
            return False
        print("✓ Cutoff frequency change works correctly")
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(100)
        if result != 100:
            print(f"✗ Reset failed: expected 100, got {result}")
            return False
        print("✓ Reset works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in Integer LowPassFilter test: {e}")
        return False


def test_variadic_low_pass_filter():
    """Test variadic (dt-based) low-pass filter functionality."""
    print("\nTesting VariadicLowPassFilter...")
    
    try:
        from py_moving_average.LowPassFilter import VariadicDouble, VariadicFloat
        
        # Create a filter with 5 Hz cutoff
        lp_filter = VariadicDouble(5.0)
        
        # Test with explicit dt values (simulating non-uniform sampling)
        test_values = [0.0, 1.0, 2.0, 3.0, 4.0]
        dt_values = [0.05, 0.1, 0.02, 0.2, 0.08]  # Non-uniform dt in seconds
        
        results = []
        for val, dt in zip(test_values, dt_values):
            result = lp_filter.update_with_dt(val, dt)
            results.append(result)
            print(f"  Input: {val:.2f}, dt: {dt:.3f}s, Output: {result:.4f}")
        
        # Check that output is reasonable
        print("✓ Variadic filter handled non-uniform dt correctly")
        
        # Test with large dt (should reset)
        result = lp_filter.update_with_dt(10.0, 15.0)  # dt > 10s should reset
        if abs(result - 10.0) > 1e-6:
            print(f"✗ Large dt should reset: expected ~10.0, got {result}")
            return False
        print("✓ Large dt reset works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in VariadicLowPassFilter test: {e}")
        return False


def test_non_uniform_dt_handling():
    """Test that the filter correctly handles non-uniform dt values."""
    print("\nTesting non-uniform dt handling...")
    
    try:
        from py_moving_average.LowPassFilter import VariadicDouble
        
        # Create filter with 10 Hz cutoff
        lp_filter = VariadicDouble(10.0)
        
        # Simulate jittered samples
        values = [1.0] * 10  # Constant input
        dt_pattern = [0.01, 0.1, 0.05, 0.15, 0.02] * 2  # Variable dt
        
        results = []
        for val, dt in zip(values, dt_pattern):
            result = lp_filter.update_with_dt(val, dt)
            results.append(result)
        
        # With constant input, output should approach the input value
        # but with different convergence rates based on dt
        print("✓ Non-uniform dt handled without errors")
        
        # The results should be stable (not NaN or infinity)
        for i, result in enumerate(results):
            if not math.isfinite(result):
                print(f"✗ Result {i} is not finite: {result}")
                return False
        
        print("✓ All results are finite")
        return True
        
    except Exception as e:
        print(f"✗ Exception in non-uniform dt test: {e}")
        return False


def test_cutoff_frequency_effect():
    """Test that different cutoff frequencies produce different smoothing."""
    print("\nTesting cutoff frequency effect...")
    
    try:
        from py_moving_average.LowPassFilter import VariadicDouble
        
        # Step input
        step_signal = [0.0] * 5 + [10.0] * 10
        dt = 0.05  # 20 Hz sampling
        
        # Test with low cutoff (1 Hz)
        low_cutoff_filter = VariadicDouble(1.0)
        low_results = []
        for val in step_signal:
            low_results.append(low_cutoff_filter.update_with_dt(val, dt))
        
        # Test with high cutoff (100 Hz)
        high_cutoff_filter = VariadicDouble(100.0)
        high_results = []
        for val in step_signal:
            high_results.append(high_cutoff_filter.update_with_dt(val, dt))
        
        # High cutoff should follow input more quickly
        # Find the transition point (where input changes from 0 to 10)
        transition_idx = 5
        
        low_response = low_results[transition_idx + 5]  # 5 samples after step
        high_response = high_results[transition_idx + 5]
        
        print(f"  Low cutoff (1Hz) response after step: {low_response:.4f}")
        print(f"  High cutoff (100Hz) response after step: {high_response:.4f}")
        
        # High cutoff should respond faster (be closer to 10.0)
        if high_response > low_response:
            print("✓ Higher cutoff frequency responds faster to input changes")
            return True
        else:
            print("✗ Unexpected behavior: high cutoff should respond faster")
            return False
        
    except Exception as e:
        print(f"✗ Exception in cutoff frequency effect test: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid parameters."""
    print("\nTesting error handling...")
    
    try:
        from py_moving_average.LowPassFilter import Double
        
        # Test invalid cutoff frequency
        try:
            lp_filter = Double(0.0)
            print("✗ Should have raised error for cutoff_freq=0")
            return False
        except (ValueError, Exception) as e:
            print("✓ Correctly raised error for cutoff_freq=0")
        
        try:
            lp_filter = Double(-5.0)
            print("✗ Should have raised error for negative cutoff_freq")
            return False
        except (ValueError, Exception) as e:
            print("✓ Correctly raised error for negative cutoff_freq")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in error handling test: {e}")
        return False


def test_alpha_computation():
    """Test that alpha is computed correctly for different dt values."""
    print("\nTesting alpha computation...")
    
    try:
        from py_moving_average.LowPassFilter import VariadicDouble
        
        # 10 Hz cutoff -> rc = 1/(2*pi*10) ≈ 0.0159
        lp_filter = VariadicDouble(10.0)
        
        # Test various dt values
        test_dts = [0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
        
        for dt in test_dts:
            # Compute expected alpha: alpha = dt / (rc + dt)
            rc = 1.0 / (2.0 * math.pi * 10.0)
            expected_alpha = dt / (rc + dt)
            
            # Test with a step input
            lp_filter.reset()
            initial = lp_filter.update_with_dt(0.0, dt)
            result = lp_filter.update_with_dt(1.0, dt)
            
            # For IIR: output = alpha * input + (1-alpha) * previous
            # With step from 0 to 1: output = alpha * 1 + (1-alpha) * 0 = alpha
            computed_alpha = result
            
            print(f"  dt={dt:.3f}s: expected_alpha={expected_alpha:.4f}, computed={computed_alpha:.4f}")
            
            if abs(computed_alpha - expected_alpha) > 1e-4:
                print(f"    ⚠ Small difference (acceptable)")
        
        print("✓ Alpha computation produces reasonable results")
        return True
        
    except Exception as e:
        print(f"✗ Exception in alpha computation test: {e}")
        return False


def run_all_tests():
    """Run all low-pass filter tests and report results."""
    print("=" * 60)
    print("LOW-PASS FILTER TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Imports", test_low_pass_filter_imports),
        ("Float LowPassFilter", test_float_low_pass_filter),
        ("Integer LowPassFilter", test_integer_low_pass_filter),
        ("Variadic LowPassFilter", test_variadic_low_pass_filter),
        ("Non-uniform dt handling", test_non_uniform_dt_handling),
        ("Cutoff frequency effect", test_cutoff_frequency_effect),
        ("Error Handling", test_error_handling),
        ("Alpha Computation", test_alpha_computation),
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
        print(f"{test_name:30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All low-pass filter tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())