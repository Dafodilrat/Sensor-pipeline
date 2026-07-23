# Python Bindings for Filter Library

This directory contains Python bindings for the C++ filter classes using pybind11.

## Directory Structure

```
custom_lib/filters/
├── lib/                         # C++ header files
│   ├── base_filter.hpp
│   ├── base_iir_filter.hpp
│   ├── fixed_point_low_pass_filter.hpp
│   ├── float_low_pass_filter.hpp
│   └── low_pass_filter.hpp
├── src/                        # Python bindings source
│   ├── filter_bindings.cpp     # Individual filter bindings
│   └── py_filter_module.cpp    # Main module definition
├── setup.py                    # Build script for the Python module
├── example_usage.py            # Example usage scripts
└── README_python.md            # This file
```

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
filter = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=10.0)

# Update with integer values
result = filter.update(100)  # Returns 100
result = filter.update(200)  # Returns filtered value between 100-200

# Access properties
print(f"Cutoff: {filter.cutoff_frequency} Hz")
print(f"Q-format: Q{filter.fractional_bits}.{filter.fractional_bits}")
print(f"Q scale: {filter.q_scale}")
```

### Available Classes

| Class | Q-Format | Integral | Fractional | Description |
|-------|----------|----------|-----------|-------------|
| `FixedPointLowPassFilter_24_8` | Q24.8 | 24 bits | 8 bits | Large range, lower precision |
| `FixedPointLowPassFilter_16_16` | Q16.16 | 16 bits | 16 bits | Balanced precision (default) |
| `FixedPointLowPassFilter_8_24` | Q8.24 | 8 bits | 24 bits | Higher precision, lower range |
| `FixedPointLowPassFilter_2_30` | Q2.30 | 2 bits | 30 bits | Maximum precision |
| `FloatLowPassFilter_Double` | - | - | - | Double precision float |
| `FloatLowPassFilter_Float` | - | - | - | Single precision float |

**Note:** All fixed-point filters use `int32_t` storage with `int64_t` calculations due to fpm library constraints.

### Float Filter Example

```python
float_filter = py_filter.FloatLowPassFilter_Double(cutoff_freq_hz=5.0)
result = float_filter.update(100.5)  # Returns 100.5
```

## Different Q-Format Precisions

```python
# Large range, lower precision
filter_q24_8 = py_filter.FixedPointLowPassFilter_24_8(cutoff_freq_hz=10.0)

# Balanced precision (default)
filter_q16_16 = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=10.0)

# High precision, smaller range
filter_q8_24 = py_filter.FixedPointLowPassFilter_8_24(cutoff_freq_hz=10.0)

# Maximum precision, smallest range
filter_q2_30 = py_filter.FixedPointLowPassFilter_2_30(cutoff_freq_hz=10.0)
```

## Running Examples

```bash
cd custom_lib/filters
python example_usage.py
```

## Constructor Parameters

### FixedPointLowPassFilter Classes

```python
FixedPointLowPassFilter_24_8(
    cutoff_freq_hz: float,      # Cutoff frequency in Hz (required)
    fractional_bits: int = 8,  # Q-format fractional bits
    timeout_seconds: float = 10.0  # Timeout for reset on large dt gaps
)
```

**Note:** The fractional_bits parameter is optional and defaults to the value in the class name, but can be overridden if needed.

## Methods and Properties

### FixedPointLowPassFilter Classes

- `update(new_value: int) -> int` - Add a new value and return filtered result
- `update_with_timestamp(new_value: int, timestamp, is_clamped: bool = None) -> int` - Update with explicit timestamp
- `reset()` - Reset filter state
- `set_cutoff_frequency(cutoff_freq_hz: float)` - Update cutoff frequency
- `set_timeout(timeout_seconds: float)` - Update timeout
- `get_cutoff_frequency() -> float` - Get current cutoff frequency
- `get_timeout() -> float` - Get current timeout
- `get_current_output_double() -> float` - Get current output as double
- `get_fractional_bits() -> int` - Get Q-format fractional bits
- `get_q_scale() -> int` - Get Q-format scale factor (2^fractional_bits)

**Properties:**
- `cutoff_frequency: float` (read-only)
- `timeout: float` (read-only)
- `fractional_bits: int` (read-only)
- `q_scale: int` (read-only)

### FloatLowPassFilter Classes

- `update(new_value: float) -> float` - Add a new value and return filtered result
- `reset()` - Reset filter state
- `set_cutoff_frequency(cutoff_freq_hz: float)` - Update cutoff frequency
- `set_timeout(timeout_seconds: float)` - Update timeout
- `get_cutoff_frequency() -> float` - Get current cutoff frequency
- `get_timeout() -> float` - Get current timeout
- `get_current_output() -> float` - Get current output

**Properties:**
- `cutoff_frequency: float` (read-only)
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
filter = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=20.0)

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
filter1 = py_filter.FixedPointLowPassFilter32(cutoff_freq_hz=10.0)
filter2 = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=10.0)
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