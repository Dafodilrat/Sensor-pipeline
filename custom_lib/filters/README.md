# Filters Library

This directory contains the C++ filter implementations with Python bindings using pybind11.

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
└── setup.py                    # Build script for the Python module
```

## Examples

See the common examples file in the parent directory:
- `custom_lib/examples.py` - Comprehensive examples for both filters and running_data libraries

To run examples:
```bash
cd custom_lib
python examples.py                    # Run all demos
python examples.py Filters          # Run filters demos only
python examples.py "Fixed-Point"    # Run specific demo
```

## Documentation

- [Python Bindings Documentation](../README_python.md) - Detailed documentation for Python bindings
- [Extensibility Demonstration](../EXTENSIBILITY.md) - How to add new filter types

## Building

### Build the Python Module

```bash
cd custom_lib/filters
python setup.py build_ext --inplace
```

### Prerequisites

- Python 3.7 or higher
- pip
- C++17 compatible compiler
- pybind11 (will be installed automatically if not present)

## Usage

### Basic Fixed-Point Filter

```python
import py_filter

# Create a fixed-point low-pass filter with 10Hz cutoff (Q16.16)
filter = py_filter.FixedPointLowPassFilter_16_16(cutoff_freq_hz=10.0)

# Update with integer values
result = filter.update(100)
result = filter.update(200)
```

### Float Filter

```python
import py_filter

float_filter = py_filter.FloatLowPassFilter_Double(cutoff_freq_hz=5.0)
result = float_filter.update(100.5)
```

## Available Classes

| Class | Q-Format | Description |
|-------|----------|-------------|
| `FixedPointLowPassFilter_24_8` | Q24.8 | Large range, lower precision |
| `FixedPointLowPassFilter_16_16` | Q16.16 | Balanced precision (default) |
| `FixedPointLowPassFilter_8_24` | Q8.24 | Higher precision, lower range |
| `FixedPointLowPassFilter_2_30` | Q2.30 | Maximum precision |
| `FloatLowPassFilter_Double` | - | Double precision float |
| `FloatLowPassFilter_Float` | - | Single precision float |

Note: All fixed-point filters use `int32_t` storage with `int64_t` calculations.
