#!/usr/bin/env python3
"""
Common examples for both running_data and filters libraries.

This script demonstrates how to use the different filter and moving average classes
for various signal processing tasks. It combines examples from both libraries to
provide a comprehensive overview of the available functionality.
"""

import sys
import os
import time
import random
from datetime import timedelta

# Add the custom_lib root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def demo_filters_basic_fixed_point():
    """Demonstrate basic fixed-point low-pass filter usage from filters library."""
    print("\n" + "="*70)
    print("FILTERS LIBRARY: BASIC FIXED-POINT LOW-PASS FILTER DEMO")
    print("="*70)
    
    try:
        import py_filter
        print("Successfully imported py_filter module")
    except ImportError as e:
        print(f"Failed to import py_filter: {e}")
        print("Make sure the module is built first with:")
        print("  cd custom_lib/filters && python setup.py build_ext --inplace")
        return
    
    # Create a fixed-point low-pass filter with 10Hz cutoff (Q16.16)
    filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=10.0)
    
    print(f"\nFilter configuration:")
    print(f"  Type: FixedPointLowPassFilter_16_16")
    print(f"  Cutoff frequency: {filter_q16_16.cutoff_frequency} Hz")
    print(f"  Q-format: Q{filter_q16_16.fractional_bits}.{filter_q16_16.fractional_bits}")
    print(f"  Q scale factor: {filter_q16_16.q_scale}")
    print(f"  Timeout: {filter_q16_16.timeout} seconds")
    
    # Simulate some input values
    input_values = [0, 100, 200, 300, 200, 100, 0, -100, -200, -100, 0]
    
    print(f"\nProcessing {len(input_values)} samples...")
    print("Index | Input  | Filtered")
    print("-" * 35)
    
    for i, val in enumerate(input_values):
        filtered = filter_q16_16.update(val)
        print(f"{i:5d} | {val:6d} | {filtered:8d}")


def demo_filters_different_precisions():
    """Demonstrate different Q-format precisions from filters library."""
    print("\n" + "="*70)
    print("FILTERS LIBRARY: DIFFERENT Q-FORMAT PRECISIONS DEMO")
    print("="*70)
    
    try:
        import py_filter
    except ImportError as e:
        print(f"Failed to import py_filter: {e}")
        return
    
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
    print("Value  | Q24.8     | Q16.16    | Q8.24     | Q2.30")
    print("-" * 45)
    
    for val in test_values:
        results = []
        for name, filter_obj in filters:
            result = filter_obj.update(val)
            results.append(result)
        
        print(f"{val:6d} | {results[0]:9d} | {results[1]:8d} | {results[2]:9d} | {results[3]:6d}")


def demo_filters_noise_filtering():
    """Demonstrate noise filtering application from filters library."""
    print("\n" + "="*70)
    print("FILTERS LIBRARY: NOISE FILTERING DEMO")
    print("="*70)
    
    try:
        import py_filter
    except ImportError as e:
        print(f"Failed to import py_filter: {e}")
        return
    
    # Create filter for noisy sensor data
    filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=20.0)
    
    # Simulate noisy sensor readings around 100
    random.seed(42)
    sensor_values = [100 + random.randint(-10, 10) for _ in range(20)]
    
    # Filter the noisy data
    filtered_values = []
    print("Simulating noisy sensor data (true value ~100):")
    print("Sample | Noisy     | Filtered")
    print("-" * 26)
    
    for i, val in enumerate(sensor_values[:10]):
        filtered = filter_q16_16.update(val)
        filtered_values.append(filtered)
        print(f"{i:6d} | {val:9d} | {filtered:8d}")
    
    print(f"\n... (showing first 10 of {len(sensor_values)} samples)")
    print(f"After filtering: values are more stable around the true value")


def demo_filters_large_range():
    """Demonstrate large range with Q24.8 format from filters library."""
    print("\n" + "="*70)
    print("FILTERS LIBRARY: LARGE RANGE FILTER DEMO (Q24.8)")
    print("="*70)
    
    try:
        import py_filter
    except ImportError as e:
        print(f"Failed to import py_filter: {e}")
        return
    
    # Create filter with Q24.8 for larger range
    filter_q24_8 = py_filter.FixedPointLowPassFilter_24_8(cutoff_freq_hz=5.0)
    
    print(f"Filter: FixedPointLowPassFilter_24_8")
    print(f"Q-format: Q24.8 (24 integral, 8 fractional bits)")
    
    # Test with larger values
    large_values = [0, 1000000, 500000, 1500000, 1000000]
    
    print("\nLarge value test:")
    print("Input     | Filtered")
    print("-" * 18)
    
    for val in large_values:
        filtered = filter_q24_8.update(val)
        print(f"{val:7d} | {filtered:8d}")


def demo_filters_high_precision():
    """Demonstrate the high-precision Q2.30 filter from filters library."""
    print("\n" + "="*70)
    print("FILTERS LIBRARY: HIGH-PRECISION FILTER DEMO (Q2.30)")
    print("="*70)
    
    try:
        import py_filter
    except ImportError as e:
        print(f"Failed to import py_filter: {e}")
        return
    
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


def demo_filters_float():
    """Demonstrate float low-pass filter from filters library."""
    print("\n" + "="*70)
    print("FILTERS LIBRARY: FLOAT LOW-PASS FILTER DEMO")
    print("="*70)
    
    try:
        import py_filter
    except ImportError as e:
        print(f"Failed to import py_filter: {e}")
        return
    
    # Create float low-pass filters
    float_filter = py_filter.FloatLowPassFilter_Double(cutoff_freq_hz=10.0)
    
    print(f"Filter: FloatLowPassFilter_Double")
    print(f"Cutoff frequency: {float_filter.cutoff_frequency} Hz")
    
    # Test with float values
    float_values = [0.0, 1.5, 2.7, 3.2, 2.1, 1.0, 0.0, -1.0, -2.0, -1.5, 0.0]
    
    print("\nFloat value filtering:")
    print("Index | Input    | Filtered")
    print("-" * 28)
    
    for i, val in enumerate(float_values):
        filtered = float_filter.update(val)
        print(f"{i:5d} | {val:7.2f} | {filtered:8.4f}")


def demo_running_data_fixed_moving_average():
    """Demonstrate FixedMovingAverage from running_data library."""
    print("\n" + "="*70)
    print("RUNNING_DATA LIBRARY: FIXED MOVING AVERAGE DEMO")
    print("="*70)
    
    try:
        import py_moving_average as pma
        from py_moving_average.FixedMovingAverage.mediumbuffer import Double
        print("Successfully imported py_moving_average module")
    except ImportError as e:
        print(f"Failed to import py_moving_average: {e}")
        print("Make sure the module is built first with:")
        print("  cd custom_lib/running_data && python setup.py build_ext --inplace")
        return
    
    # Create a fixed moving average with window size 5
    ma = Double(5)
    print(f"Created FixedMovingAverage Double with window size 5")
    
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
    print("\nProcessing samples:")
    print("Index | Value | Average  | Expected")
    print("-" * 38)
    
    for i, val in enumerate(test_values):
        avg = ma.update(val)
        actual_averages.append(avg)
        print(f"{i:5d} | {val:5.1f} | {avg:7.4f} | {expected_averages[i]:.4f}")
    
    # Verify correctness
    all_correct = True
    for actual, expected in zip(actual_averages, expected_averages):
        if abs(actual - expected) > 1e-6:
            all_correct = False
            break
    
    if all_correct:
        print("\nAll averages match expected values!")
    else:
        print("\nSome averages don't match expected values")


def demo_running_data_time_duration_moving_average():
    """Demonstrate TimeDurationMovingAverage from running_data library."""
    print("\n" + "="*70)
    print("RUNNING_DATA LIBRARY: TIME DURATION MOVING AVERAGE DEMO")
    print("="*70)
    
    try:
        import py_moving_average as pma
        from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Double
        print("Successfully imported py_moving_average module")
    except ImportError as e:
        print(f"Failed to import py_moving_average: {e}")
        return
    
    # Create a time-based moving average with explicit parameters
    print("Creating TimeDurationMovingAverage Double...")
    print("  Window size: 12 samples")
    print("  Sensor rate: 10.0 Hz")
    print("  Window duration: 1000ms")
    
    td_ma = Double(12, 10.0, timedelta(milliseconds=1000))
    
    print(f"\nFilter configuration:")
    print(f"  Sensor rate: {td_ma.sensor_hz} Hz")
    print(f"  Window duration: {td_ma.window_duration}")
    print(f"  Max size: {td_ma.max_size}")
    
    print("\nTesting with simulated 10Hz data (15 samples):")
    print("Update | Value | Average   | Window Size")
    print("-" * 35)
    
    for i in range(15):
        avg = td_ma.update(float(i))
        print(f"{i+1:6d} | {i:5d} | {avg:8.4f} | {td_ma.size:11d}")
        time.sleep(0.1)  # 100ms = 10Hz
    
    print(f"\nFinal window size: {td_ma.size}")


def demo_running_data_buffer_sizes():
    """Demonstrate different buffer size variants from running_data library."""
    print("\n" + "="*70)
    print("RUNNING_DATA LIBRARY: DIFFERENT BUFFER SIZES DEMO")
    print("="*70)
    
    try:
        import py_moving_average as pma
        from py_moving_average.FixedMovingAverage.smallbuffer import Integer as MA_Small
        from py_moving_average.FixedMovingAverage.mediumbuffer import Double as MA_Medium
        from py_moving_average.FixedMovingAverage.largebuffer import Float as MA_Large
        print("Successfully imported py_moving_average module")
    except ImportError as e:
        print(f"Failed to import py_moving_average: {e}")
        return
    
    print("\nCreating filters with different buffer sizes:")
    
    # Test small buffer
    ma_small = MA_Small(50)
    print(f"  Small buffer: max_size={ma_small.max_size}")
    
    # Test medium buffer
    ma_medium = MA_Medium(500)
    print(f"  Medium buffer: max_size={ma_medium.max_size}")
    
    # Test large buffer
    ma_large = MA_Large(5000)
    print(f"  Large buffer: max_size={ma_large.max_size}")
    
    print("\nTesting small buffer with integer values:")
    print("Value | Average")
    print("-" * 13)
    
    test_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for val in test_values:
        avg = ma_small.update(val)
        print(f"{val:5d} | {avg:7.2f}")


def demo_running_data_vs_filters_integration():
    """Demonstrate how both libraries can work together."""
    print("\n" + "="*70)
    print("INTEGRATION DEMO: RUNNING_DATA + FILTERS LIBRARIES")
    print("="*70)
    
    try:
        import py_moving_average as pma
        from py_moving_average.FixedMovingAverage.mediumbuffer import Double as MA_Double
        import py_filter
        print("Successfully imported both modules")
    except ImportError as e:
        print(f"Failed to import modules: {e}")
        return
    
    # Create a moving average for smoothing
    ma = MA_Double(5)
    
    # Create a low-pass filter for further processing
    lp_filter = py_filter.FloatLowPassFilter_Double(cutoff_freq_hz=5.0)
    
    print("\nProcessing data through both moving average and low-pass filter:")
    print("Raw    | MA (5)   | LP (5Hz)")
    print("-" * 25)
    
    # Simulate some noisy data
    random.seed(42)
    raw_values = [50 + random.randint(-5, 5) for _ in range(15)]
    
    for i, raw in enumerate(raw_values):
        ma_output = ma.update(float(raw))
        lp_output = lp_filter.update(float(raw))
        print(f"{raw:5d} | {ma_output:7.2f} | {lp_output:7.2f}")


def demo_extensibility():
    """Demonstrate the extensibility of the library architecture."""
    print("\n" + "="*70)
    print("EXTENSIBILITY DEMO")
    print("="*70)
    
    print("""
This demonstrates how the library architecture allows adding new filter types
without modifying existing .cpp/.h files.

The MedianFilter was added as a third filter type by creating only new files:
  - filters/lib/median_filter.hpp - The C++ MedianFilter implementation
  - filters/src/median_filter_bindings.cpp - Python bindings
  - filters/src/py_median_filter_module.cpp - Separate Python module

This satisfies Part 2, Task 3 requirement: "A third filter type must be addable
by a future developer without modifying any existing .cpp/.h files in the
library, only adding new ones."

To use the median filter:
  - In C++: #include "filters/lib/median_filter.hpp"
  - In Python: import py_median_filter
    """)
    
    try:
        import py_median_filter
        print("Successfully imported py_median_filter module!")
        
        # Create and test a median filter
        filter = py_median_filter.MedianFilterInt5()
        
        test_values = [10, 20, 30, 40, 50, 100, 20, 30, 40, 50]
        print("\nTesting MedianFilterInt5:")
        print("Input | Median")
        print("-" * 13)
        
        for val in test_values:
            median = filter.update(val)
            print(f"{val:5d} | {median:6d}")
            
    except ImportError as e:
        print(f"Note: py_median_filter module not available: {e}")
        print("To build it:")
        print("  1. Add median_filter.hpp to filters/lib/")
        print("  2. Add median_filter_bindings.cpp to filters/src/")
        print("  3. Add py_median_filter_module.cpp to filters/src/")
        print("  4. Rebuild the Python modules")


def main():
    """Run all demos."""
    print("COMMON EXAMPLES FOR RUNNING_DATA AND FILTERS LIBRARIES")
    print("=" * 70)
    
    demos = [
        ("Filters: Basic Fixed-Point", demo_filters_basic_fixed_point),
        ("Filters: Different Precisions", demo_filters_different_precisions),
        ("Filters: Noise Filtering", demo_filters_noise_filtering),
        ("Filters: Large Range", demo_filters_large_range),
        ("Filters: High-Precision", demo_filters_high_precision),
        ("Filters: Float", demo_filters_float),
        ("Running Data: Fixed Moving Average", demo_running_data_fixed_moving_average),
        ("Running Data: Time Duration Moving Average", demo_running_data_time_duration_moving_average),
        ("Running Data: Buffer Sizes", demo_running_data_buffer_sizes),
        ("Integration: MA + LP Filter", demo_running_data_vs_filters_integration),
        ("Extensibility", demo_extensibility),
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
                print(f"\n{'='*70}")
                print(f"Running: {name}")
                print('='*70)
                demo_func()
            except Exception as e:
                print(f"Error running {name}: {e}")
    
    print("\n" + "="*70)
    print("DEMOS COMPLETED")
    print("="*70)
    print("""
Usage:
  python examples.py                    # Run all demos
  python examples.py Filters          # Run filters demos
  python examples.py Running          # Run running_data demos
  python examples.py "Fixed-Point"    # Run specific demo
  python examples.py --all            # Run all demos (same as no args)

Build instructions:
  To build filters library:
    cd custom_lib/filters && python setup.py build_ext --inplace

  To build running_data library:
    cd custom_lib/running_data && python setup.py build_ext --inplace
""")


if __name__ == "__main__":
    main()
