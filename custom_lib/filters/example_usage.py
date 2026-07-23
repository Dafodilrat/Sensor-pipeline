#!/usr/bin/env python3
"""
Example usage of the py_filter Python bindings.

This script demonstrates how to use the different filter classes
for various signal processing tasks.
"""

import sys
import os

# Add the filters directory to Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    import py_filter
    print("Successfully imported py_filter module")
except ImportError as e:
    print(f"Failed to import py_filter: {e}")
    print("Make sure the module is built first with: cd custom_lib/filters && python setup.py build_ext --inplace")
    sys.exit(1)


def demo_basic_fixed_point_filter():
    """Demonstrate basic fixed-point low-pass filter usage."""
    print("\n" + "="*60)
    print("BASIC FIXED-POINT LOW-PASS FILTER DEMO")
    print("="*60)
    
    # Create a fixed-point low-pass filter with 10Hz cutoff (Q16.16)
    filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=10.0)
    
    print(f"Filter configuration:")
    print(f"  Type: FixedPointLowPassFilter_16_16")
    print(f"  Cutoff frequency: {filter_q16_16.cutoff_frequency} Hz")
    print(f"  Q-format: Q{filter_q16_16.fractional_bits}.{filter_q16_16.fractional_bits}")
    print(f"  Q scale factor: {filter_q16_16.q_scale}")
    print(f"  Timeout: {filter_q16_16.timeout} seconds")
    
    # Simulate some input values
    input_values = [0, 100, 200, 300, 200, 100, 0, -100, -200, -100, 0]
    
    print(f"\nProcessing {len(input_values)} samples...")
    print("Index | Input  | Filtered")
    print("-" * 30)
    
    for i, val in enumerate(input_values):
        filtered = filter_q16_16.update(val)
        print(f"{i:5d} | {val:6d} | {filtered:8d}")


def demo_different_precisions():
    """Demonstrate different Q-format precisions."""
    print("\n" + "="*60)
    print("DIFFERENT Q-FORMAT PRECISIONS DEMO")
    print("="*60)
    
    cutoff = 5.0
    test_values = [1000, 500, 1500, 1000]
    
    # Create filters with different Q-formats
    filters = [
        ("Q24.8", py_filter.FixedPointLowPassFilter_24_8(cutoff, 8, 10.0)),
        ("Q16.16", py_filter.FixedPointLowPassFilter_16_16(cutoff, 16, 10.0)),
        ("Q8.24", py_filter.FixedPointLowPassFilter_8_24(cutoff, 24, 10.0)),
        ("Q2.30", py_filter.FixedPointLowPassFilter_2_30(cutoff, 30, 10.0)),
    ]
    
    print("Testing different Q-format precisions with same inputs:")
    print("Value  | Q24.8   | Q16.16  | Q8.24   | Q2.30")
    print("-" * 40)
    
    for val in test_values:
        results = []
        for name, filter_obj in filters:
            result = filter_obj.update(val)
            results.append(result)
        
        print(f"{val:6d} | {results[0]:7d} | {results[1]:7d} | {results[2]:7d} | {results[3]:6d}")


def demo_noise_filtering():
    """Demonstrate noise filtering application."""
    print("\n" + "="*60)
    print("NOISE FILTERING DEMO")
    print("="*60)
    
    import random
    
    # Create filter for noisy sensor data
    filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=20.0)  # 20Hz cutoff
    
    # Simulate noisy sensor readings around 100
    random.seed(42)
    sensor_values = [100 + random.randint(-10, 10) for _ in range(20)]
    
    # Filter the noisy data
    filtered_values = []
    print("Simulating noisy sensor data (true value ~100):")
    print("Sample | Noisy     | Filtered")
    print("-" * 26)
    
    for i, val in enumerate(sensor_values[:10]):  # Show first 10 samples
        filtered = filter_q16_16.update(val)
        filtered_values.append(filtered)
        print(f"{i:6d} | {val:9d} | {filtered:8d}")
    
    print(f"\n... (showing first 10 of {len(sensor_values)} samples)")
    print(f"After filtering: values are more stable around the true value")


def demo_large_range():
    """Demonstrate large range with Q24.8 format."""
    print("\n" + "="*60)
    print("LARGE RANGE FILTER DEMO (Q24.8)")
    print("="*60)
    
    # Create filter with Q24.8 for larger range
    filter_q24_8 = py_filter.FixedPointLowPassFilter_24_8(cutoff_freq_hz=5.0)
    
    print(f"Filter: FixedPointLowPassFilter_24_8")
    print(f"Q-format: Q24.8 (24 integral, 8 fractional bits)")
    
    # Test with larger values
    large_values = [0, 1000000, 500000, 1500000, 1000000]
    
    print("\nLarge value test:")
    print("Input    | Filtered")
    print("-" * 16)
    
    for val in large_values:
        filtered = filter_q24_8.update(val)
        print(f"{val:7d} | {filtered:8d}")


def demo_high_precision():
    """Demonstrate the high-precision Q2.30 filter."""
    print("\n" + "="*60)
    print("HIGH-PRECISION FILTER DEMO (Q2.30)")
    print("="*60)
    
    # Create high-precision filter - maximum fractional bits for int32_t
    filter_q2_30 = py_filter.FixedPointLowPassFilter_2_30(cutoff_freq_hz=2.0, fractional_bits=30)
    
    print(f"Filter: FixedPointLowPassFilter_2_30")
    print(f"Q-format: Q2.30 (2 integral, 30 fractional bits)")
    
    # Test with small increments to show precision
    values = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0]
    
    print("\nSmall signal test (values: 0-5):")
    print("Input | Filtered")
    print("-" * 15)
    
    for val in values:
        filtered = filter_q2_30.update(val)
        print(f"{val:5d} | {filtered:7d}")


def main():
    """Run all demos."""
    print("PY_FILTER PYTHON BINDINGS DEMOS")
    print("=" * 60)
    
    demos = [
        ("Basic Fixed-Point Filter", demo_basic_fixed_point_filter),
        ("Different Precisions", demo_different_precisions),
        ("High-Precision", demo_high_precision),
        ("Noise Filtering", demo_noise_filtering),
        ("Large Range", demo_large_range),
    ]
    
    # Run all demos or allow selection
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        # Run specific demo
        demo_name = sys.argv[1]
        for name, demo_func in demos:
            if demo_name.lower() in name.lower():
                demo_func()
                return
        print(f"Demo '{demo_name}' not found")
    else:
        # Run all demos
        for name, demo_func in demos:
            try:
                demo_func()
            except Exception as e:
                print(f"Error running {name}: {e}")
    
    print("\n" + "="*60)
    print("DEMOS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
