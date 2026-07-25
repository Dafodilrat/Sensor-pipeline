#!/usr/bin/env python3
"""
Comprehensive test suite for py_filter Python bindings.

Tests all the filter classes exposed through the Python bindings.
"""

import unittest
import sys
import os

# Add the filters directory to Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'filters'))

try:
    import py_filter
    print("Successfully imported py_filter module")
except ImportError as e:
    print(f"Failed to import py_filter: {e}")
    print("Make sure the module is built first with: cd custom_lib/filters && python setup.py build_ext --inplace")
    sys.exit(1)


class TestFixedPointLowPassFilter_16_16(unittest.TestCase):
    """Test FixedPointLowPassFilter_16_16 (Q16.16)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq_times_100 = 1000  # 10.00 Hz cutoff (as integer * 100)
        self.timeout_ns = 1000000000  # 1.0 seconds in nanoseconds
        self.filter = py_filter.FixedPointLowPassFilter_16_16(self.cutoff_freq_times_100, 16, self.timeout_ns)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        # cutoff_freq_times_100 is stored internally, not exposed as property
        self.assertEqual(self.filter.fractional_bits, 16)
        self.assertEqual(self.filter.timeout, self.timeout_ns)

    def test_basic_update(self):
        """Test basic update functionality."""
        # First update should return the input value
        result = self.filter.update(100)
        self.assertEqual(result, 100)

        # Second update should be filtered
        result = self.filter.update(200)
        # The result should be between 100 and 200 due to low-pass filtering
        self.assertGreaterEqual(result, 100)
        self.assertLessEqual(result, 200)

    def test_step_response(self):
        """Test step response of the filter."""
        self.filter = py_filter.FixedPointLowPassFilter_16_16(100, 16, 10000000000)  # 1.00 Hz, 10s timeout in ns
        
        # Start with 0
        result1 = self.filter.update(0)
        self.assertEqual(result1, 0)
        
        # Apply step to 1000
        result2 = self.filter.update(1000)
        # Should be between 0 and 1000
        self.assertGreaterEqual(result2, 0)
        self.assertLessEqual(result2, 1000)

    def test_reset(self):
        """Test reset functionality."""
        # First update
        self.filter.update(100)
        
        # Reset
        self.filter.reset()
        
        # After reset, next update should return the new value
        result = self.filter.update(200)
        self.assertEqual(result, 200)

    def test_set_cutoff(self):
        """Test setting cutoff frequency."""
        new_cutoff_times_100 = 2000  # 20.00 Hz
        self.filter.set_cutoff(new_cutoff_times_100)
        # No property to check, just verify it doesn't crash

    def test_set_timeout(self):
        """Test setting timeout."""
        new_timeout_ns = 5000000000  # 5.0 seconds in nanoseconds
        self.filter.set_timeout(new_timeout_ns)
        self.assertEqual(self.filter.timeout, new_timeout_ns)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q16.16, scale should be 2^16 = 65536
        self.assertEqual(self.filter.q_scale, 65536)

    def test_had_clamp(self):
        """Test clamping detection."""
        self.filter.update(100)
        # No clamping should occur with normal values
        self.assertFalse(self.filter.had_clamp())


class TestFixedPointLowPassFilter_24_8(unittest.TestCase):
    """Test FixedPointLowPassFilter_24_8 (Q24.8)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq_times_100 = 1000  # 10.00 Hz cutoff (as integer * 100)
        self.timeout_ns = 1000000000  # 1.0 seconds in nanoseconds
        self.filter = py_filter.FixedPointLowPassFilter_24_8(self.cutoff_freq_times_100, 8, self.timeout_ns)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.fractional_bits, 8)
        self.assertEqual(self.filter.timeout, self.timeout_ns)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q24.8, scale should be 2^8 = 256
        self.assertEqual(self.filter.q_scale, 256)


class TestFixedPointLowPassFilter_8_24(unittest.TestCase):
    """Test FixedPointLowPassFilter_8_24 (Q8.24)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq_times_100 = 1000  # 10.00 Hz cutoff (as integer * 100)
        self.timeout_ns = 1000000000  # 1.0 seconds in nanoseconds
        self.filter = py_filter.FixedPointLowPassFilter_8_24(self.cutoff_freq_times_100, 24, self.timeout_ns)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.fractional_bits, 24)
        self.assertEqual(self.filter.timeout, self.timeout_ns)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q8.24, scale should be 2^24 = 16777216
        self.assertEqual(self.filter.q_scale, 16777216)


class TestFixedPointLowPassFilter_2_30(unittest.TestCase):
    """Test FixedPointLowPassFilter_2_30 (Q2.30)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq_times_100 = 1000  # 10.00 Hz cutoff (as integer * 100)
        self.timeout_ns = 1000000000  # 1.0 seconds in nanoseconds
        self.filter = py_filter.FixedPointLowPassFilter_2_30(self.cutoff_freq_times_100, 30, self.timeout_ns)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.fractional_bits, 30)
        self.assertEqual(self.filter.timeout, self.timeout_ns)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q2.30, scale should be 2^30 = 1073741824
        self.assertEqual(self.filter.q_scale, 1073741824)


class TestLowPassIIRFilterDouble(unittest.TestCase):
    """Test LowPassIIRFilter_Double"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.LowPassIIRFilter_Double(self.cutoff_freq, self.timeout)

    def test_basic_update(self):
        """Test basic update functionality."""
        # First update should return the input value (or close to it)
        result = self.filter.update(100.5)
        self.assertAlmostEqual(result, 100.5, places=5)

    def test_step_response(self):
        """Test step response of the filter."""
        self.filter = py_filter.LowPassIIRFilter_Double(1.0, 1.0)  # Lower cutoff, with timeout
        
        # Start with 0
        result1 = self.filter.update(0.0)
        self.assertAlmostEqual(result1, 0.0, places=5)
        
        # Apply step to 1000
        result2 = self.filter.update(1000.0)
        # Should be between 0 and 1000
        self.assertGreaterEqual(result2, 0.0)
        self.assertLessEqual(result2, 1000.0)

    def test_reset(self):
        """Test reset functionality."""
        # First update
        self.filter.update(100.0)
        
        # Reset
        self.filter.reset()
        
        # After reset, next update should return the new value
        result = self.filter.update(200.0)
        self.assertAlmostEqual(result, 200.0, places=5)

    def test_set_cutoff(self):
        """Test setting cutoff frequency."""
        new_cutoff = 20.0
        self.filter.set_cutoff(new_cutoff)
        self.assertEqual(self.filter.get_cutoff(), new_cutoff)

    def test_set_timeout(self):
        """Test setting timeout."""
        new_timeout = 5.0
        self.filter.set_timeout(new_timeout)
        self.assertEqual(self.filter.get_timeout(), new_timeout)

    def test_has_timeout(self):
        """Test timeout status."""
        # Filter has timeout
        self.assertTrue(self.filter.has_timeout())
        
        # Create filter without timeout
        no_timeout_filter = py_filter.LowPassIIRFilter_Double(10.0, -1.0)
        self.assertFalse(no_timeout_filter.has_timeout())

    def test_get_alpha(self):
        """Test getting alpha value."""
        self.filter.update(100.0)
        alpha = self.filter.get_alpha()
        self.assertIsInstance(alpha, float)
        self.assertGreaterEqual(alpha, 0.0)
        self.assertLessEqual(alpha, 1.0)


class TestLowPassIIRFilterFloat(unittest.TestCase):
    """Test LowPassIIRFilter_Float"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.LowPassIIRFilter_Float(self.cutoff_freq, self.timeout)

    def test_basic_update(self):
        """Test basic update functionality."""
        result = self.filter.update(100.5)
        self.assertAlmostEqual(result, 100.5, places=5)


class TestFilterComparison(unittest.TestCase):
    """Test comparisons between different filter types"""

    def test_fixed_vs_float_convergence(self):
        """Test that fixed-point and float filters produce similar results."""
        cutoff_hz = 10.0
        test_values = [0, 100, 50, 150, 100, 50, 0]
        
        # Fixed-point uses cutoff * 100 as integer, float uses Hz as double
        fixed_filter = py_filter.FixedPointLowPassFilter_16_16(1000, 16, 10000000000)  # 10.00 Hz, 10s timeout
        float_filter = py_filter.LowPassIIRFilter_Double(cutoff_hz, 10.0)
        
        for val in test_values:
            fixed_result = fixed_filter.update(val)
            float_result = float_filter.update(float(val))
            self.assertLess(abs(fixed_result - float_result), 5.0)

    def test_different_precision_filters(self):
        """Test different Q-format filters with same input."""
        cutoff_times_100 = 500  # 5.00 Hz
        test_values = [0, 1000, 500, 1500, 1000]
        timeout_ns = 10000000000  # 10.0 seconds
        
        filter_q24_8 = py_filter.FixedPointLowPassFilter_24_8(cutoff_times_100, 8, timeout_ns)
        filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff_times_100, 16, timeout_ns)
        filter_q8_24 = py_filter.FixedPointLowPassFilter_8_24(cutoff_times_100, 24, timeout_ns)
        filter_q2_30 = py_filter.FixedPointLowPassFilter_2_30(cutoff_times_100, 30, timeout_ns)
        
        for val in test_values:
            result_q24_8 = filter_q24_8.update(val)
            result_q16_16 = filter_q16_16.update(val)
            result_q8_24 = filter_q8_24.update(val)
            result_q2_30 = filter_q2_30.update(val)
            
            self.assertGreaterEqual(result_q24_8, 0)
            self.assertGreaterEqual(result_q16_16, 0)
            self.assertGreaterEqual(result_q8_24, 0)
            self.assertGreaterEqual(result_q2_30, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_zero_cutoff_raises(self):
        """Test that zero cutoff frequency raises an exception."""
        with self.assertRaises(Exception):
            py_filter.FixedPointLowPassFilter_16_16(0)  # 0.00 Hz

    def test_negative_cutoff_raises(self):
        """Test that negative cutoff frequency raises an exception."""
        with self.assertRaises(Exception):
            py_filter.FixedPointLowPassFilter_16_16(-1000)  # -10.00 Hz

    def test_zero_timeout_disabled(self):
        """Test that zero timeout disables timeout (no exception)."""
        # Zero timeout means no timeout - should not raise
        filter_no_timeout = py_filter.FixedPointLowPassFilter_16_16(1000, 16, 0)  # 10.00 Hz, 0ns timeout
        self.assertFalse(filter_no_timeout.has_timeout())

    def test_negative_timeout_disabled(self):
        """Test that negative timeout is treated as disabled (no exception)."""
        # Negative timeout should be treated as 0 (no timeout)
        filter_no_timeout = py_filter.FixedPointLowPassFilter_16_16(1000, 16, -1)  # 10.00 Hz, -1ns timeout
        self.assertFalse(filter_no_timeout.has_timeout())


if __name__ == '__main__':
    unittest.main(verbosity=2)
