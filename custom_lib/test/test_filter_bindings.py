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
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.FixedPointLowPassFilter_16_16(self.cutoff_freq, 16, self.timeout)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.cutoff_frequency, self.cutoff_freq)
        self.assertEqual(self.filter.timeout, self.timeout)
        self.assertEqual(self.filter.fractional_bits, 16)

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
        self.filter = py_filter.FixedPointLowPassFilter_16_16(1.0, 16, 10.0)  # Lower cutoff for smoother response
        
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

    def test_set_cutoff_frequency(self):
        """Test setting cutoff frequency."""
        new_cutoff = 20.0
        self.filter.set_cutoff_frequency(new_cutoff)
        self.assertEqual(self.filter.cutoff_frequency, new_cutoff)

    def test_set_timeout(self):
        """Test setting timeout."""
        new_timeout = 5.0
        self.filter.set_timeout(new_timeout)
        self.assertEqual(self.filter.timeout, new_timeout)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q16.16, scale should be 2^16 = 65536
        self.assertEqual(self.filter.q_scale, 65536)

    def test_get_current_output_double(self):
        """Test getting current output as double."""
        self.filter.update(100)
        output = self.filter.get_current_output_double()
        self.assertIsInstance(output, float)
        self.assertAlmostEqual(output, 100.0, places=1)


class TestFixedPointLowPassFilter_24_8(unittest.TestCase):
    """Test FixedPointLowPassFilter_24_8 (Q24.8)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.FixedPointLowPassFilter_24_8(self.cutoff_freq, 8, self.timeout)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.cutoff_frequency, self.cutoff_freq)
        self.assertEqual(self.filter.timeout, self.timeout)
        self.assertEqual(self.filter.fractional_bits, 8)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q24.8, scale should be 2^8 = 256
        self.assertEqual(self.filter.q_scale, 256)


class TestFixedPointLowPassFilter_8_24(unittest.TestCase):
    """Test FixedPointLowPassFilter_8_24 (Q8.24)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.FixedPointLowPassFilter_8_24(self.cutoff_freq, 24, self.timeout)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.cutoff_frequency, self.cutoff_freq)
        self.assertEqual(self.filter.timeout, self.timeout)
        self.assertEqual(self.filter.fractional_bits, 24)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q8.24, scale should be 2^24 = 16777216
        self.assertEqual(self.filter.q_scale, 16777216)


class TestFixedPointLowPassFilter_2_30(unittest.TestCase):
    """Test FixedPointLowPassFilter_2_30 (Q2.30)"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.FixedPointLowPassFilter_2_30(self.cutoff_freq, 30, self.timeout)

    def test_construction(self):
        """Test that filter can be constructed."""
        self.assertIsNotNone(self.filter)
        self.assertEqual(self.filter.cutoff_frequency, self.cutoff_freq)
        self.assertEqual(self.filter.timeout, self.timeout)
        self.assertEqual(self.filter.fractional_bits, 30)

    def test_q_scale(self):
        """Test Q scale factor."""
        # For Q2.30, scale should be 2^30 = 1073741824
        self.assertEqual(self.filter.q_scale, 1073741824)


class TestFloatLowPassFilterDouble(unittest.TestCase):
    """Test FloatLowPassFilter_Double"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.FloatLowPassFilter_Double(self.cutoff_freq, self.timeout)

    def test_basic_update(self):
        """Test basic update functionality."""
        # First update should return the input value
        result = self.filter.update(100.5)
        self.assertAlmostEqual(result, 100.5, places=5)

    def test_step_response(self):
        """Test step response of the filter."""
        self.filter = py_filter.FloatLowPassFilter_Double(1.0, 10.0)  # Lower cutoff
        
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

    def test_set_cutoff_frequency(self):
        """Test setting cutoff frequency."""
        new_cutoff = 20.0
        self.filter.set_cutoff_frequency(new_cutoff)
        self.assertEqual(self.filter.cutoff_frequency, new_cutoff)

    def test_set_timeout(self):
        """Test setting timeout."""
        new_timeout = 5.0
        self.filter.set_timeout(new_timeout)
        self.assertEqual(self.filter.timeout, new_timeout)

    def test_get_current_output(self):
        """Test getting current output."""
        self.filter.update(100.5)
        output = self.filter.get_current_output()
        self.assertIsInstance(output, float)
        self.assertAlmostEqual(output, 100.5, places=5)


class TestFloatLowPassFilterFloat(unittest.TestCase):
    """Test FloatLowPassFilter_Float"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cutoff_freq = 10.0  # 10 Hz cutoff
        self.timeout = 1.0
        self.filter = py_filter.FloatLowPassFilter_Float(self.cutoff_freq, self.timeout)

    def test_basic_update(self):
        """Test basic update functionality."""
        result = self.filter.update(100.5)
        self.assertAlmostEqual(result, 100.5, places=5)


class TestFilterComparison(unittest.TestCase):
    """Test comparisons between different filter types"""

    def test_fixed_vs_float_convergence(self):
        """Test that fixed-point and float filters produce similar results."""
        cutoff = 10.0
        test_values = [0, 100, 50, 150, 100, 50, 0]
        
        fixed_filter = py_filter.FixedPointLowPassFilter_16_16(cutoff, 16, 10.0)
        float_filter = py_filter.FloatLowPassFilter_Double(cutoff, 10.0)
        
        for val in test_values:
            fixed_result = fixed_filter.update(val)
            float_result = float_filter.update(float(val))
            self.assertLess(abs(fixed_result - float_result), 5.0)

    def test_different_precision_filters(self):
        """Test different Q-format filters with same input."""
        cutoff = 5.0
        test_values = [0, 1000, 500, 1500, 1000]
        
        filter_q24_8 = py_filter.FixedPointLowPassFilter_24_8(cutoff, 8, 10.0)
        filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff, 16, 10.0)
        filter_q8_24 = py_filter.FixedPointLowPassFilter_8_24(cutoff, 24, 10.0)
        filter_q2_30 = py_filter.FixedPointLowPassFilter_2_30(cutoff, 30, 10.0)
        
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
            py_filter.FixedPointLowPassFilter_16_16(0.0)

    def test_negative_cutoff_raises(self):
        """Test that negative cutoff frequency raises an exception."""
        with self.assertRaises(Exception):
            py_filter.FixedPointLowPassFilter_16_16(-10.0)

    def test_zero_timeout_raises(self):
        """Test that zero timeout raises an exception."""
        with self.assertRaises(Exception):
            py_filter.FixedPointLowPassFilter_16_16(10.0, 16, 0.0)

    def test_negative_timeout_raises(self):
        """Test that negative timeout raises an exception."""
        with self.assertRaises(Exception):
            py_filter.FixedPointLowPassFilter_16_16(10.0, 16, -1.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
