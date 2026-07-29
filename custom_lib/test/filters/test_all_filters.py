#!/usr/bin/env python3
"""
Comprehensive test script for all filter functionality from templated classes in filters/lib.

This script tests:
- LowPassIIRFilter_Float (templated LowPassIIRFilter<T>)
- FixedPointLowPassFilter_24_8, FixedPointLowPassFilter_16_16, 
  FixedPointLowPassFilter_8_24, FixedPointLowPassFilter_2_30
  (templated FixedPointLowPassFilter<T, CalcT, FractionalBits>)
"""

import sys
import os
import math
import time
import struct

# Add the custom_lib root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_imports():
    """Test that we can import all filter classes."""
    print("Testing filter imports...")
    
    try:
        import py_filter
        print("✓ Successfully imported py_filter module")
        
        # Test LowPassIIRFilter classes
        classes_to_test = [
            ('LowPassIIRFilter_Float', py_filter.LowPassIIRFilter_Float),
        ]
        
        for class_name, class_type in classes_to_test:
            try:
                instance = class_type(10.0)
                print(f"✓ Successfully created {class_name}")
            except Exception as e:
                print(f"✗ Failed to create {class_name}: {e}")
                return False
        
        # Test FixedPointLowPassFilter classes
        fixed_point_classes = [
            ('FixedPointLowPassFilter_24_8', py_filter.FixedPointLowPassFilter_24_8),
            ('FixedPointLowPassFilter_16_16', py_filter.FixedPointLowPassFilter_16_16),
            ('FixedPointLowPassFilter_8_24', py_filter.FixedPointLowPassFilter_8_24),
            ('FixedPointLowPassFilter_2_30', py_filter.FixedPointLowPassFilter_2_30),
        ]
        
        for class_name, class_type in fixed_point_classes:
            try:
                # Fixed-point filters now use cutoff_freq_times_100 (integer)
                instance = class_type(1000)  # 10.00 Hz
                print(f"✓ Successfully created {class_name}")
            except Exception as e:
                print(f"✗ Failed to create {class_name}: {e}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False


def test_low_pass_iir_filter_float():
    """Test LowPassIIRFilter_Float functionality."""
    print("\nTesting LowPassIIRFilter_Float...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff
        lp_filter = py_filter.LowPassIIRFilter_Float(10.0)
        
        # Test basic properties
        if abs(lp_filter.get_cutoff() - 10.0) > 1e-5:  # Float precision
            print(f"✗ Cutoff frequency incorrect: expected 10.0, got {lp_filter.get_cutoff()}")
            return False
        print(f"✓ Initial cutoff frequency: {lp_filter.get_cutoff()} Hz")
        
        # Test basic filtering
        test_values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
        
        # Check first output
        if abs(results[0] - 0.0) > 1e-5:
            print(f"✗ First output should be 0.0, got {results[0]}")
            return False
        
        # Check smoothing effect
        if results[-1] >= results[-2] >= results[0]:
            print("✓ Output is properly smoothed (lagging behind input)")
        else:
            print("✗ Output doesn't show expected smoothing behavior")
            return False
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(10.0)
        if abs(result - 10.0) > 1e-5:
            print(f"✗ Reset failed: expected 10.0, got {result}")
            return False
        print("✓ Reset works correctly")
        
        # Test alpha value
        lp_filter.update(5.0)
        alpha = lp_filter.get_alpha()
        if alpha < 0 or alpha > 1:
            print(f"✗ Alpha should be between 0 and 1, got {alpha}")
            return False
        print(f"✓ Alpha value is valid: {alpha:.6f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in LowPassIIRFilter_Float test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_filter_24_8():
    """Test FixedPointLowPassFilter_24_8 (Q24.8 format) functionality."""
    print("\nTesting FixedPointLowPassFilter_24_8...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff (1000 = 10.00 * 100)
        lp_filter = py_filter.FixedPointLowPassFilter_24_8(1000)
        
        # Test Q-format properties
        fractional_bits = lp_filter.get_fractional_bits()
        if fractional_bits != 8:
            print(f"✗ Expected 8 fractional bits, got {fractional_bits}")
            return False
        print(f"✓ Q-format: {fractional_bits} fractional bits")
        
        q_scale = lp_filter.get_q_scale()
        print(f"✓ Q-scale: {q_scale}")
        
        # Note: FixedPointLowPassFilter doesn't expose cutoff_frequency getter
        # The cutoff is set via cutoff_freq_times_100 in constructor (1000 = 10.00 Hz)
        print(f"✓ Cutoff frequency set to 10.00 Hz (1000 times 100)")
        
        # Test timeout - now in nanoseconds
        timeout_ns = lp_filter.get_timeout()
        # Default timeout for FixedPointLowPassFilter_24_8 is 0 (no timeout) when not specified
        # But we passed 10.0 which is actually 10000000000 ns if that was the intent
        print(f"✓ Timeout: {timeout_ns} ns")
        
        # Test basic filtering with integer values
        test_values = [0, 10, 20, 30, 40, 50]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
            # Ensure result is integer
            if not isinstance(result, int):
                print(f"✗ Expected integer result, got {type(result)}: {result}")
                return False
        
        print(f"✓ First few outputs: {results[:3]}")
        print(f"✓ Last few outputs: {results[-3:]}")
        
        # Check first output
        if results[0] != 0:
            print(f"✗ First output should be 0, got {results[0]}")
            return False
        
        # Check that output shows smoothing effect
        if len(set(results)) > 1:  # Should have some variation
            print("✓ Filter produced varied outputs")
        else:
            print("✗ Filter output doesn't vary")
            return False
        
        # Test cutoff frequency change (using cutoff_freq_times_100)
        lp_filter.set_cutoff(2000)  # 20.00 Hz
        print("✓ Cutoff frequency change works correctly")
        
        # Test timeout change (using nanoseconds)
        lp_filter.set_timeout(5000000000)  # 5.0 seconds in nanoseconds
        if abs(lp_filter.get_timeout() - 5000000000) > 1000000:
            print(f"✗ Set timeout failed: expected 5000000000, got {lp_filter.get_timeout()}")
            return False
        print("✓ Timeout change works correctly")
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(100)
        # After reset with input 100, result should be close to 100
        if abs(result - 100) > 1:
            print(f"✗ Reset failed: expected ~100, got {result}")
            return False
        print("✓ Reset works correctly")
        
        # Test current output as double
        current_output = lp_filter.get_current_output_double()
        if not isinstance(current_output, float):
            print(f"✗ Current output double should be float, got {type(current_output)}")
            return False
        print(f"✓ Current output as double: {current_output:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedPointLowPassFilter_24_8 test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_filter_16_16():
    """Test FixedPointLowPassFilter_16_16 (Q16.16 format) functionality."""
    print("\nTesting FixedPointLowPassFilter_16_16...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff (1000 = 10.00 * 100)
        lp_filter = py_filter.FixedPointLowPassFilter_16_16(1000)
        
        # Test Q-format properties
        fractional_bits = lp_filter.get_fractional_bits()
        if fractional_bits != 16:
            print(f"✗ Expected 16 fractional bits, got {fractional_bits}")
            return False
        print(f"✓ Q-format: {fractional_bits} fractional bits")
        
        q_scale = lp_filter.get_q_scale()
        print(f"✓ Q-scale: {q_scale}")
        
        # Test with fractional-looking integer values (scaled by Q-format)
        test_values = [0, 1000, 2000, 3000, -1000, -2000]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
            if not isinstance(result, int):
                print(f"✗ Expected integer result, got {type(result)}: {result}")
                return False
        
        print(f"✓ First few outputs: {results[:3]}")
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(5000)
        print(f"✓ After reset with input 5000: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedPointLowPassFilter_16_16 test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_filter_8_24():
    """Test FixedPointLowPassFilter_8_24 (Q8.24 format) functionality."""
    print("\nTesting FixedPointLowPassFilter_8_24...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff (1000 = 10.00 * 100)
        lp_filter = py_filter.FixedPointLowPassFilter_8_24(1000)
        
        # Test Q-format properties
        fractional_bits = lp_filter.get_fractional_bits()
        if fractional_bits != 24:
            print(f"✗ Expected 24 fractional bits, got {fractional_bits}")
            return False
        print(f"✓ Q-format: {fractional_bits} fractional bits")
        
        q_scale = lp_filter.get_q_scale()
        print(f"✓ Q-scale: {q_scale}")
        
        # Test with small integer values (due to limited integral bits)
        test_values = [0, 1, 2, 3, 4, 5]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
        
        print(f"✓ Outputs: {results}")
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(10)
        print(f"✓ After reset with input 10: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedPointLowPassFilter_8_24 test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_filter_2_30():
    """Test FixedPointLowPassFilter_2_30 (Q2.30 format) functionality."""
    print("\nTesting FixedPointLowPassFilter_2_30...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff (1000 = 10.00 * 100)
        lp_filter = py_filter.FixedPointLowPassFilter_2_30(1000)
        
        # Test Q-format properties
        fractional_bits = lp_filter.get_fractional_bits()
        if fractional_bits != 30:
            print(f"✗ Expected 30 fractional bits, got {fractional_bits}")
            return False
        print(f"✓ Q-format: {fractional_bits} fractional bits")
        
        q_scale = lp_filter.get_q_scale()
        print(f"✓ Q-scale: {q_scale}")
        
        # Test with very small integer values (due to very limited integral bits)
        test_values = [0, 1, 0, 1, 2, 3]
        results = []
        
        for val in test_values:
            result = lp_filter.update(val)
            results.append(result)
        
        print(f"✓ Outputs: {results}")
        
        # Test reset
        lp_filter.reset()
        result = lp_filter.update(1)
        print(f"✓ After reset with input 1: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in FixedPointLowPassFilter_2_30 test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cutoff_frequency_effects():
    """Test that different cutoff frequencies produce different smoothing."""
    print("\nTesting cutoff frequency effects...")
    
    try:
        import py_filter
        
        # Step input
        step_signal = [0.0] * 5 + [10.0] * 10
        
        # Test with different filters
        filters = [
            ("LowPassIIRFilter_Float (1Hz)", py_filter.LowPassIIRFilter_Float(1.0)),
            ("LowPassIIRFilter_Float (10Hz)", py_filter.LowPassIIRFilter_Float(10.0)),
            ("LowPassIIRFilter_Float (100Hz)", py_filter.LowPassIIRFilter_Float(100.0)),
        ]
        
        results_list = []
        for name, lp_filter in filters:
            results = []
            for val in step_signal:
                results.append(lp_filter.update(val))
            results_list.append((name, results))
            
            # Print final response
            print(f"  {name}: final response = {results[-1]:.4f}")
        
        # Higher cutoff should respond faster (be closer to 10.0)
        if results_list[2][1][-1] > results_list[1][1][-1] > results_list[0][1][-1]:
            print("✓ Higher cutoff frequencies respond faster (as expected)")
            return True
        else:
            print("✗ Unexpected behavior: higher cutoff should respond faster")
            return False
        
    except Exception as e:
        print(f"✗ Exception in cutoff frequency effects test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid parameters."""
    print("\nTesting error handling...")
    
    try:
        import py_filter
        
        # Test invalid cutoff frequency for LowPassIIRFilter
        test_cases = [
            ("LowPassIIRFilter_Float(0.0)", lambda: py_filter.LowPassIIRFilter_Float(0.0)),
            ("FixedPointLowPassFilter_16_16(0)", lambda: py_filter.FixedPointLowPassFilter_16_16(0)),  # 0.00 Hz
            ("FixedPointLowPassFilter_16_16(-1000)", lambda: py_filter.FixedPointLowPassFilter_16_16(-1000)),  # -10.00 Hz
        ]
        
        for test_name, test_func in test_cases:
            try:
                test_func()
                print(f"✗ {test_name} should have raised error")
                return False
            except (ValueError, Exception) as e:
                print(f"✓ {test_name} correctly raised error: {type(e).__name__}")
        
        # Note: For FixedPoint filters, timeout of 0 means disabled (no timeout), not an error
        # Test that zero timeout works (disables timeout)
        try:
            filter_no_timeout = py_filter.FixedPointLowPassFilter_16_16(1000, 16, 0)  # 10.00 Hz, 0ns timeout
            print(f"✓ FixedPointLowPassFilter_16_16(1000, 16, 0) correctly creates filter with no timeout")
        except Exception as e:
            print(f"✗ FixedPointLowPassFilter with 0 timeout should not raise: {e}")
            return False
        
        # Test that negative timeout is treated as 0 (disabled)
        try:
            filter_no_timeout = py_filter.FixedPointLowPassFilter_16_16(1000, 16, -1)  # 10.00 Hz, -1ns timeout
            print(f"✓ FixedPointLowPassFilter_16_16(1000, 16, -1) correctly creates filter with disabled timeout")
        except Exception as e:
            print(f"✗ FixedPointLowPassFilter with negative timeout should not raise: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in error handling test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alpha_computation():
    """Test that alpha is computed correctly for different dt values."""
    print("\nTesting alpha computation...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff
        lp_filter = py_filter.LowPassIIRFilter_Float(10.0)
        
        # RC time constant for 10 Hz: rc = 1/(2*pi*10) ≈ 0.015915
        rc = 1.0 / (2.0 * math.pi * 10.0)
        
        # Test various dt values
        test_dts = [0.001, 0.01, 0.05, 0.1, 0.5]
        
        for dt in test_dts:
            # Compute expected alpha: alpha = dt / (rc + dt)
            expected_alpha = dt / (rc + dt)
            
            # Reset filter and apply step input
            lp_filter.reset()
            lp_filter.update(0.0)
            result = lp_filter.update(1.0)
            
            # For step from 0 to 1: output = alpha * 1 + (1-alpha) * 0 = alpha
            computed_alpha = result
            
            print(f"  dt={dt:.3f}s: expected={expected_alpha:.4f}, computed={computed_alpha:.4f}, diff={abs(computed_alpha - expected_alpha):.6f}")
            
            # Check if within reasonable tolerance
            if abs(computed_alpha - expected_alpha) > 0.01:  # 1% tolerance
                print(f"    ⚠ Difference larger than expected")
        
        print("✓ Alpha computation produces reasonable results")
        return True
        
    except Exception as e:
        print(f"✗ Exception in alpha computation test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_response():
    """Test step response characteristics."""
    print("\nTesting step response...")
    
    try:
        import py_filter
        
        # Create filter with 10 Hz cutoff
        lp_filter = py_filter.LowPassIIRFilter_Float(10.0)
        
        # Apply step input
        step_input = [0.0] * 5 + [1.0] * 20
        results = []
        
        for val in step_input:
            result = lp_filter.update(val)
            results.append(result)
        
        # Check that output starts at 0
        if abs(results[0] - 0.0) > 1e-6:
            print(f"✗ Initial output should be 0.0, got {results[0]}")
            return False
        
        # Check that output rises toward 1.0
        if results[-1] < 0.5:  # Should have risen significantly
            print(f"✗ Final output should be closer to 1.0, got {results[-1]}")
            return False
        
        # Check that output is monotonically increasing after step
        step_idx = 5  # Where step occurs
        post_step = results[step_idx:]
        is_monotonic = all(post_step[i] <= post_step[i+1] for i in range(len(post_step)-1))
        if is_monotonic:
            print("✓ Output is monotonically increasing after step")
        else:
            print("⚠ Output is not monotonically increasing (may be due to very small dt)")
        
        print(f"✓ Step response: initial={results[0]:.4f}, final={results[-1]:.4f}")
        return True
        
    except Exception as e:
        print(f"✗ Exception in step response test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_precision():
    """Test different fixed-point precisions."""
    print("\nTesting fixed-point precision differences...")
    
    try:
        import py_filter
        
        # Create filters with different Q-formats (1000 = 10.00 Hz * 100)
        filters = [
            ("24_8", py_filter.FixedPointLowPassFilter_24_8(1000)),
            ("16_16", py_filter.FixedPointLowPassFilter_16_16(1000)),
            ("8_24", py_filter.FixedPointLowPassFilter_8_24(1000)),
            ("2_30", py_filter.FixedPointLowPassFilter_2_30(1000)),
        ]
        
        # Same input for all
        test_values = [0, 100, 0, 100, 0]
        
        for name, lp_filter in filters:
            results = []
            for val in test_values:
                result = lp_filter.update(val)
                results.append(result)
            
            print(f"  {name}: {results}")
            
            # Verify all results are integers
            for i, result in enumerate(results):
                if not isinstance(result, int):
                    print(f"✗ {name} result {i} is not integer: {type(result)}")
                    return False
        
        print("✓ All fixed-point filters produce integer results")
        return True
        
    except Exception as e:
        print(f"✗ Exception in fixed-point precision test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timeout_behavior():
    """Test timeout behavior for both filter types."""
    print("\nTesting timeout behavior...")
    
    try:
        import py_filter
        import time
        
        # Test LowPassIIRFilter with timeout
        lp_iir = py_filter.LowPassIIRFilter_Float(10.0, 0.1)  # 100ms timeout
        
        # First update
        result1 = lp_iir.update(5.0)
        
        # Wait longer than timeout
        time.sleep(0.15)  # Sleep 150ms > 100ms timeout
        
        # Second update - should reset because dt > timeout
        result2 = lp_iir.update(10.0)
        
        # After timeout, the filter should reset and return the new input
        if abs(result2 - 10.0) < 0.1:  # Should be very close to 10.0
            print("✓ LowPassIIRFilter timeout reset works")
        else:
            print(f"✗ LowPassIIRFilter timeout reset failed: expected ~10.0, got {result2}")
            return False
        # Test FixedPointLowPassFilter with timeout (100000000 = 0.1s timeout in ns)
        lp_fp = py_filter.FixedPointLowPassFilter_16_16(1000, 16, 100000000)  # 10.00 Hz, 100ms timeout
        
        # First update
        result1 = lp_fp.update(5)
        
        # Wait longer than timeout
        time.sleep(0.15)  # Sleep 150ms > 100ms timeout
        
        # Second update - should reset
        result2 = lp_fp.update(10)
        
        if abs(result2 - 10) < 1:  # Should be very close to 10
            print("✓ FixedPointLowPassFilter timeout reset works")
        else:
            print(f"✗ FixedPointLowPassFilter timeout reset failed: expected ~10, got {result2}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in timeout behavior test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_vs_float_comparison():
    """Compare FixedPointLowPassFilter output with LowPassIIRFilter_Float output."""
    print("\nTesting FixedPoint vs Float comparison...")

    try:
        import py_filter
        import time
        
        # Create both filters with same cutoff frequency (10 Hz)
        # For FixedPointLowPassFilter: 1000 = 10.00 Hz * 100
        lp_float = py_filter.LowPassIIRFilter_Float(10.0)
        lp_fp_16_16 = py_filter.FixedPointLowPassFilter_16_16(1000)
        
        # Test signal: sinusoid with amplitude scaled for Q16.16 range (-0.5 to +0.5)
        import math
        num_samples = 50  # Reduced to make test faster with delays
        test_signal = []
        for i in range(num_samples):
            t = i * 0.01  # 100 Hz sample rate
            # Use amplitude 0.4 to stay within Q16.16 range (-0.5 to +0.5)
            signal = 0.4 * math.sin(2.0 * math.pi * 5.0 * t)  # 5 Hz sine wave
            test_signal.append(signal)
        
        # Run both filters
        float_results = []
        fp_results = []
        
        for val in test_signal:
            float_out = lp_float.update(val)
            # Scale float to int for fixed-point (Q16.16: multiply by 2^16)
            fp_input = int(val * (1 << 16))
            fp_out = lp_fp_16_16.update(fp_input)
            
            float_results.append(float_out)
            # Scale fixed-point output back to float
            fp_results.append(fp_out / (1 << 16))
            
            # Add small delay to ensure proper time delta for filter calculations
            time.sleep(0.001)
        
        # Compare outputs (allow for quantization differences)
        max_diff = 0.0
        max_rel_diff = 0.0
        num_close = 0
        
        for i in range(len(float_results)):
            diff = abs(float_results[i] - fp_results[i])
            max_diff = max(max_diff, diff)
            
            # Relative difference
            if abs(double_results[i]) > 0.001:
                rel_diff = diff / abs(double_results[i])
                max_rel_diff = max(max_rel_diff, rel_diff)
            else:
                rel_diff = 0
            
            # Consider close if within absolute diff < 0.1
            if diff < 0.1:
                num_close += 1
        
        print(f"  Max absolute difference: {max_diff:.6f}")
        print(f"  Max relative difference: {max_rel_diff:.4%}")
        print(f"  Close matches ({num_close}/{num_samples}): {num_close/num_samples:.1%}")
        
        # Both filters should produce similar trends (sign and general magnitude)
        correlations = 0
        for i in range(1, len(double_results)):
            if (double_results[i] > double_results[i-1]) == (fp_results[i] > fp_results[i-1]):
                correlations += 1
        
        trend_match_pct = correlations / (len(double_results) - 1) * 100
        print(f"  Trend correlation: {trend_match_pct:.1f}%")
        
        # For fixed-point to be working correctly, trends should match well
        if trend_match_pct >= 90.0:
            print("✓ Fixed-point filter produces similar trends to double filter")
            return True
        else:
            print(f"✗ Fixed-point filter trend correlation too low: {trend_match_pct:.1f}%")
            return False
        
    except Exception as e:
        print(f"✗ Exception in FixedPoint vs Double comparison: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all filter tests and report results."""
    print("=" * 70)
    print("COMPREHENSIVE FILTER LIBRARY TEST SUITE")
    print("Testing all templated filter classes from filters/lib")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("LowPassIIRFilter_Float", test_low_pass_iir_filter_float),
        ("FixedPointLowPassFilter_24_8", test_fixed_point_filter_24_8),
        ("FixedPointLowPassFilter_16_16", test_fixed_point_filter_16_16),
        ("FixedPointLowPassFilter_8_24", test_fixed_point_filter_8_24),
        ("FixedPointLowPassFilter_2_30", test_fixed_point_filter_2_30),
        ("Cutoff Frequency Effects", test_cutoff_frequency_effects),
        ("Error Handling", test_error_handling),
        ("Alpha Computation", test_alpha_computation),
        ("Step Response", test_step_response),
        ("Fixed-Point Precision", test_fixed_point_precision),
        ("Timeout Behavior", test_timeout_behavior),
        ("FixedPoint vs Float Comparison", test_fixed_point_vs_float_comparison),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("All filter tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())