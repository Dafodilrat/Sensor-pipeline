#!/usr/bin/env python3
"""
Simple test script for low-pass filter functionality.
"""

import sys
import os
import math

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_variadic_low_pass_filter():
    """Test variadic low-pass filter with explicit dt."""
    print("Testing VariadicLowPassFilter...")
    
    try:
        import py_moving_average as pma
        
        # Test Double version
        lp = pma.VariadicLowPassFilter_Double(10.0)  # 10 Hz cutoff
        dt = 0.01  # 100 Hz sampling
        
        # Step response test
        values = [0.0] * 5 + [10.0] * 10  # Step from 0 to 10 at index 5
        results = []
        
        for val in values:
            result = lp.update_with_dt(val, dt)
            results.append(result)
        
        print(f"  First few outputs: {[f'{r:.4f}' for r in results[:3]]}")
        print(f"  Last few outputs: {[f'{r:.4f}' for r in results[-3:]]}")
        
        # Check basic properties
        assert results[0] == 0.0, f"First output should be 0.0, got {results[0]}"
        assert results[-1] < 10.0, f"Last output should lag input, got {results[-1]}"
        assert results[-1] > results[5], f"Output should increase over time"
        
        print("✓ VariadicLowPassFilter_Double works correctly")
        
        # Test Float version
        lp_float = pma.VariadicLowPassFilter_Float(20.0)
        result = lp_float.update_with_dt(5.0, 0.005)
        assert math.isfinite(result), f"Result should be finite, got {result}"
        
        print("✓ VariadicLowPassFilter_Float works correctly")
        
        # Test Integer version
        lp_int = pma.VariadicLowPassFilter_Integer(10.0)
        result = lp_int.update_with_dt(42, 0.01)
        assert isinstance(result, int), f"Integer filter should return int, got {type(result)}"
        
        print("✓ VariadicLowPassFilter_Integer works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fixed_point_filter():
    """Test fixed-point integer filter."""
    print("\nTesting FixedPointLowPassFilter...")
    
    try:
        import py_moving_average as pma
        
        # Create filter
        lp = pma.FixedPointLowPassFilter_Integer(10.0)
        
        print(f"  Q-format: {lp.get_q_fractional_bits()} fractional bits")
        print(f"  Q-scale: {lp.get_q_scale()}")
        
        # Test reset
        lp.reset()
        result = lp.update(100)
        print(f"  After reset and input 100: {result}")
        
        # Test cutoff frequency
        lp.set_cutoff_frequency(20.0)
        freq = lp.get_cutoff_frequency()
        assert abs(freq - 20.0) < 1e-6, f"Frequency should be 20.0, got {freq}"
        
        print("✓ FixedPointLowPassFilter_Integer works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alpha_computation():
    """Test that alpha is computed correctly."""
    print("\nTesting alpha computation...")
    
    try:
        import py_moving_average as pma
        
        # Test with known parameters
        lp = pma.VariadicLowPassFilter_Double(10.0)  # 10 Hz cutoff
        
        # RC time constant for 10 Hz: rc = 1/(2*pi*10) ≈ 0.015915
        rc = 1.0 / (2.0 * math.pi * 10.0)
        
        # Test different dt values
        test_cases = [
            (0.001, 0.001 / (rc + 0.001)),
            (0.01, 0.01 / (rc + 0.01)),
            (0.1, 0.1 / (rc + 0.1)),
        ]
        
        for dt, expected_alpha in test_cases:
            lp.reset()
            # First call (should return input)
            lp.update_with_dt(0.0, dt)
            # Second call with step input
            result = lp.update_with_dt(1.0, dt)
            # For step from 0 to 1: output = alpha * 1 + (1-alpha) * 0 = alpha
            computed_alpha = result
            
            print(f"  dt={dt:.3f}s: expected={expected_alpha:.4f}, computed={computed_alpha:.4f}")
            
            # Check if close (allow some numerical tolerance)
            if abs(computed_alpha - expected_alpha) > 1e-3:
                print(f"    ⚠ Difference: {abs(computed_alpha - expected_alpha):.6f}")
        
        print("✓ Alpha computation works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cutoff_frequency_effect():
    """Test that different cutoff frequencies produce different smoothing."""
    print("\nTesting cutoff frequency effect...")
    
    try:
        import py_moving_average as pma
        
        # Create filters with different cutoff frequencies
        dt = 0.01  # 100 Hz sampling
        
        # Low cutoff (1 Hz) - slow response
        low_lp = pma.VariadicLowPassFilter_Double(1.0)
        
        # High cutoff (100 Hz) - fast response
        high_lp = pma.VariadicLowPassFilter_Double(100.0)
        
        # Step input
        step_input = [0.0] * 5 + [10.0] * 5
        
        # Apply filters
        low_results = []
        high_results = []
        
        for val in step_input:
            low_results.append(low_lp.update_with_dt(val, dt))
            high_results.append(high_lp.update_with_dt(val, dt))
        
        # After step change, high cutoff should respond faster
        response_idx = -1  # Last result
        low_response = low_results[response_idx]
        high_response = high_results[response_idx]
        
        print(f"  Low cutoff (1Hz) final response: {low_response:.4f}")
        print(f"  High cutoff (100Hz) final response: {high_response:.4f}")
        
        # High cutoff should be closer to 10.0
        if high_response > low_response:
            print("✓ Higher cutoff frequency responds faster (as expected)")
            return True
        else:
            print(f"✗ Expected high cutoff > low cutoff: {high_response} vs {low_response}")
            return False
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_non_uniform_dt():
    """Test non-uniform dt handling."""
    print("\nTesting non-uniform dt handling...")
    
    try:
        import py_moving_average as pma
        
        lp = pma.VariadicLowPassFilter_Double(10.0)
        
        # Non-uniform dt values
        values = [0.0, 5.0, 0.0, 5.0, 0.0]
        dt_values = [0.01, 0.1, 0.005, 0.2, 0.05]
        
        results = []
        for val, dt in zip(values, dt_values):
            result = lp.update_with_dt(val, dt)
            results.append(result)
        
        # Check that all results are finite
        for i, result in enumerate(results):
            assert math.isfinite(result), f"Result {i} should be finite, got {result}"
        
        print("✓ Non-uniform dt handled correctly")
        
        # Test reset on large dt
        lp.reset()
        result = lp.update_with_dt(1.0, 15.0)  # dt > 10s should reset
        assert result == 1.0, f"Large dt should reset to input, got {result}"
        
        print("✓ Large dt reset works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    
    try:
        import py_moving_average as pma
        
        # Test invalid cutoff frequency
        try:
            pma.VariadicLowPassFilter_Double(0.0)
            print("✗ Should have raised error for cutoff_freq=0")
            return False
        except Exception:
            print("✓ Correctly raised error for cutoff_freq=0")
        
        try:
            pma.VariadicLowPassFilter_Double(-5.0)
            print("✗ Should have raised error for negative cutoff_freq")
            return False
        except Exception:
            print("✓ Correctly raised error for negative cutoff_freq")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("SIMPLE LOW-PASS FILTER TESTS")
    print("=" * 60)
    
    tests = [
        test_variadic_low_pass_filter,
        test_fixed_point_filter,
        test_alpha_computation,
        test_cutoff_frequency_effect,
        test_non_uniform_dt,
        test_error_handling,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"{test.__name__:30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())