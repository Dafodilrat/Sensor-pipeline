# Python Bindings for Filter Library

This document provides detailed documentation for the Python bindings of the C++ filter classes using pybind11.

> **Note**: This file has been moved from `custom_lib/filters/README_python.md` to `custom_lib/README_python.md` for better organization.

## Directory Structure

```
custom_lib/filters/
├── lib/                         # C++ header files
│   ├── fixed_point_low_pass_filter.hpp
│   └── low_pass_iir_filter.hpp
├── src/                        # Python bindings source
│   ├── filter_bindings.cpp     # Individual filter bindings
│   └── py_filter_module.cpp    # Main module definition
├── setup.py                    # Build script for the Python module
└── README.md                   # Filter library overview
```

See also:
- `custom_lib/running_data/` - Moving average implementations
- `custom_lib/examples.py` - Common examples for both libraries

## Building the Python Module

### Prerequisites

- Python 3.7 or higher
- pip
- C++17 compatible compiler
- pybind11 (will be installed automatically if not present)

### Build Command

```bash
cd custom_lib/filters
python setup.py build_ext --inplace
```

## Usage

### Basic Fixed-Point Filter

```python
import py_filter

# Create a fixed-point low-pass filter with 10Hz cutoff (Q16.16)
# IMPORTANT: cutoff_freq_times_100 is an INTEGER representing Hz * 100
# For 10.00 Hz, use 1000. No floating-point values allowed - this is pure fixed-point.
filter = py_filter.FixedPointLowPassFilter_16_16(1000)  # 10.00 Hz cutoff

# Update with integer values
result = filter.update(100)  # Returns 100
result = filter.update(200)  # Returns filtered value between 100-200

# Access properties
print(f"Q-format: Q{filter.fractional_bits}.{filter.fractional_bits}")
print(f"Q scale: {filter.q_scale}")
print(f"Timeout: {filter.timeout} ns")
```

### Available Classes

| Class | Q-Format | Integral | Fractional | Description |
|-------|----------|----------|-----------|-------------|
| `FixedPointLowPassFilter_24_8` | Q24.8 | 24 bits | 8 bits | Large range, lower precision |
| `FixedPointLowPassFilter_16_16` | Q16.16 | 16 bits | 16 bits | Balanced precision (default) |
| `FixedPointLowPassFilter_8_24` | Q8.24 | 8 bits | 24 bits | Higher precision, lower range |
| `FixedPointLowPassFilter_2_30` | Q2.30 | 2 bits | 30 bits | Maximum precision |
| `LowPassIIRFilter_Double` | - | - | - | Double precision float |
| `LowPassIIRFilter_Float` | - | - | - | Single precision float |

**Note:** All fixed-point filters use `int32_t` storage with `int64_t` calculations due to fpm library constraints.

### IIR Float Filter Example

```python
float_filter = py_filter.LowPassIIRFilter_Double(cutoff_freq=5.0)
result = float_filter.update(100.5)  # Returns 100.5
```

## Different Q-Format Precisions

```python
# IMPORTANT: All cutoff_freq_times_100 parameters are INTEGERS (Hz * 100)
# No floating-point values allowed - this is pure fixed-point.

# Large range, lower precision
filter_q24_8 = py_filter.FixedPointLowPassFilter_24_8(1000)  # 10.00 Hz

# Balanced precision (default)
filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(1000)  # 10.00 Hz

# High precision, smaller range
filter_q8_24 = py_filter.FixedPointLowPassFilter_8_24(1000)  # 10.00 Hz

# Maximum precision, smallest range
filter_q2_30 = py_filter.FixedPointLowPassFilter_2_30(1000)  # 10.00 Hz
```

## Running Examples

For comprehensive examples covering both filters and running_data libraries, see:

```bash
cd custom_lib
python examples.py                    # Run all demos
python examples.py Filters          # Run filters demos only
python examples.py Running          # Run running_data demos only
```

The `example_usage.py` file has been consolidated into the common `examples.py` file.

## Constructor Parameters

### FixedPointLowPassFilter Classes

```python
FixedPointLowPassFilter_24_8(
    cutoff_freq_times_100: int,      # Cutoff frequency * 100 as INTEGER (required)
                                   # e.g., 1000 = 10.00 Hz, 500 = 5.00 Hz
                                   # NO FLOATING-POINT ALLOWED - pure fixed-point
    fractional_bits: int = 8,     # Q-format fractional bits
    timeout_ns: int = 0           # Timeout in nanoseconds (0 = no timeout)
)
```

**Note:** The fractional_bits parameter is optional and defaults to the value in the class name, but can be overridden if needed.

**IMPORTANT:** The `cutoff_freq_times_100` parameter MUST be an integer. This is a pure fixed-point filter that uses NO floating-point operations. To specify 10.00 Hz, use 1000 (10.00 * 100).

## Methods and Properties

### FixedPointLowPassFilter Classes

- `update(new_value: int) -> int` - Add a new value and return filtered result
- `reset()` - Reset filter state
- `had_clamp() -> bool` - Check if clamping occurred on last update
- `set_cutoff(cutoff_freq_times_100: int)` - Update cutoff frequency (integer * 100)
- `set_timeout(timeout_ns: int)` - Update timeout in nanoseconds
- `get_timeout() -> int` - Get current timeout in nanoseconds
- `get_fractional_bits() -> int` - Get Q-format fractional bits
- `get_q_scale() -> int` - Get Q-format scale factor (2^fractional_bits)
- `get_rc_raw() -> int` - Get RC time constant in raw Q16.16 format
- `has_timeout() -> bool` - Check if timeout is enabled

**Properties:**
- `fractional_bits: int` (read-only)
- `q_scale: int` (read-only)
- `timeout: int` (read-only)

### LowPassIIRFilter Classes

- `update(new_value: float) -> float` - Add a new value and return filtered result
- `reset()` - Reset filter state
- `set_cutoff(cutoff_freq: float)` - Update cutoff frequency
- `get_cutoff() -> float` - Get current cutoff frequency
- `set_timeout(timeout_seconds: float)` - Update timeout
- `get_timeout() -> float` - Get current timeout
- `get_last_dt() -> float` - Get last time delta
- `get_alpha() -> float` - Get current alpha value
- `has_timeout() -> bool` - Check if timeout is enabled

**Properties:**
- `cutoff: float` (read-only, via get_cutoff())
- `timeout: float` (read-only)

## Mathematical Background

The low-pass filters implement the following IIR filter equation:

```
output = alpha * input + (1 - alpha) * previous_output
```

Where:
- `alpha = dt / (rc + dt)`
- `rc = 1 / (2 * pi * cutoff_freq)`
- `dt` is the time delta between samples

### Fixed-Point Implementation Details

- Uses [fpm library](https://github.com/SergeRgb/FxPointMath) for fixed-point arithmetic
- All calculations are performed in integer arithmetic (no floating-point)
- Supports saturation to prevent overflow
- Rounding: round to nearest (controlled by fpm's rounding mode)

## Choosing the Right Q-Format

| Use Case | Recommended Q-Format | Reason |
|----------|---------------------|---------|
| General purpose filtering | Q16.16 | Good balance of range and precision |
| Large signal ranges | Q24.8 | Higher integral range for larger signals |
| High precision small signals | Q2.30 | Maximum fractional precision |
| Sensor data filtering | Q16.16 | Good balance for typical sensor ranges |
| Audio processing | Q8.24 | Higher precision for better audio quality |

## Range Analysis

| Q-Format | Maximum Positive Value | Minimum Negative Value |
|----------|------------------------|------------------------|
| Q24.8 | +8,388,607 | -8,388,608 |
| Q16.16 | +32,767 | -32,768 |
| Q8.24 | +127 | -128 |
| Q2.30 | +1 | -2 |

## Example: Sensor Noise Filtering

```python
import py_filter
import random

# Create filter for noisy sensor data
# cutoff_freq_times_100 = 2000 = 20.00 Hz
filter = py_filter.FixedPointLowPassFilter_16_16(2000)

# Simulate noisy sensor readings
random.seed(42)
sensor_values = [100 + random.randint(-10, 10) for _ in range(50)]

# Filter the noisy data
filtered_values = []
for val in sensor_values:
    filtered = filter.update(val)
    filtered_values.append(filtered)

# Results show significantly reduced noise
print("Original:", sensor_values[:10])
print("Filtered:", filtered_values[:10])
```

## Backward Compatibility

For backward compatibility, the old name `FixedPointLowPassFilter32` is still available as an alias for `FixedPointLowPassFilter_16_16`.

```python
# These are equivalent
# cutoff_freq_times_100 = 1000 = 10.00 Hz
filter1 = py_filter.FixedPointLowPassFilter32(1000)
filter2 = py_filter.FixedPointLowPassFilter_16_16(1000)
```

## Troubleshooting

### ImportError: No module named 'py_filter'

Make sure you've built the module:
```bash
cd custom_lib/filters
python setup.py build_ext --inplace
```

### Compilation errors

Ensure you have:
- C++17 compiler (g++ 7+, clang++ 5+, MSVC 2017+)
- Python development headers
- pybind11 installed

On Ubuntu/Debian:
```bash
sudo apt-get install build-essential python3-dev
```

The Python bindings for the fixed-point low pass filter are now complete and ready to use!