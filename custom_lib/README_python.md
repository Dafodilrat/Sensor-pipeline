# Python Bindings for Moving Average Library

This directory contains Python bindings for the C++ `FixedMovingAverage` and `TimeDurationMovingAverage` classes using pybind11.

## Directory Structure

```
custom_lib/
├── mavg.hpp                 # C++ header with moving average classes
├── mavg.cpp                 # C++ implementation (includes header)
├── ring_buffer.hpp          # Ring buffer implementation
├── python_bindings.cpp      # Python bindings using pybind11
├── setup.py                 # Build script for the Python module
├── test_python_bindings.py  # Comprehensive test suite
└── README_python.md          # This file
```

## Building the Python Module

### Prerequisites

- Python 3.7 or higher
- pip
- C++17 compatible compiler
- pybind11 (will be installed automatically if not present)

### Installation

1. **Install dependencies:**
   ```bash
   pip install pybind11 setuptools
   ```

2. **Build and install in development mode:**
   ```bash
   cd custom_lib
   pip install -e .
   ```

3. **Or build manually:**
   ```bash
   python setup.py build_ext --inplace
   ```

### Alternative: Install system-wide

```bash
python setup.py install
```

## Usage

### Basic Import

```python
# Import the main module
import py_moving_average as pma

# Import specific classes
from py_moving_average.main import (
    FixedMovingAverageDouble,
    FixedMovingAverageFloat,
    TimeDurationMovingAverageDouble,
    TimeDurationMovingAverageFloat
)
```

### FixedMovingAverage Example

```python
from py_moving_average.main import FixedMovingAverageDouble

# Create a moving average (uses full buffer capacity)
ma = FixedMovingAverageDouble()  # Uses 1000 sample buffer by default

# Update with values and get current average
values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
averages = []

for val in values:
    avg = ma.update(val)
    averages.append(avg)
    print(f"Value: {val:2.0f}, Average: {avg:.4f}, Window size: {ma.size}")

# Reset the moving average
ma.reset()
print(f"After reset, window size: {ma.size}")
```

### TimeDurationMovingAverage Example

```python
import time
from py_moving_average.main import TimeDurationMovingAverageDouble

# Create a time-based moving average for 100Hz sensor with 1 second window
td_ma = TimeDurationMovingAverageDouble(sensor_hz=100.0, window_duration=1000)

print(f"Calculated window size: {td_ma.calculated_window_size}")
print(f"Sensor Hz: {td_ma.sensor_hz}")
print(f"Window duration: {td_ma.window_duration} ms")

# Simulate 100Hz data
for i in range(200):
    avg = td_ma.update(i)
    print(f"Update {i+1}: Value={i}, Average={avg:.4f}, Window size={td_ma.size}")
    time.sleep(0.01)  # 10ms = 100Hz

# Update parameters
ma.set_sensor_hz(200.0)  # Change to 200Hz
ma.set_window_duration(500)  # Change to 0.5 second window
```

### Available Classes

#### FixedMovingAverage

- **FixedMovingAverageDouble_Medium** - Double precision, 1000 sample buffer
- **FixedMovingAverageFloat_Medium** - Float precision, 1000 sample buffer
- **FixedMovingAverageDouble_Small** - Double precision, 100 sample buffer
- **FixedMovingAverageFloat_Small** - Float precision, 100 sample buffer
- **FixedMovingAverageDouble_Large** - Double precision, 10000 sample buffer
- **FixedMovingAverageFloat_Large** - Float precision, 10000 sample buffer

#### TimeDurationMovingAverage

- **TimeDurationMovingAverageDouble_Medium** - Double precision, 1000 sample buffer
- **TimeDurationMovingAverageFloat_Medium** - Float precision, 1000 sample buffer
- **TimeDurationMovingAverageDouble_Small** - Double precision, 100 sample buffer
- **TimeDurationMovingAverageFloat_Small** - Float precision, 100 sample buffer
- **TimeDurationMovingAverageDouble_Large** - Double precision, 10000 sample buffer
- **TimeDurationMovingAverageFloat_Large** - Float precision, 10000 sample buffer

### Constructor Parameters

#### FixedMovingAverage

```python
FixedMovingAverageDouble(sample_count=1000)
```
- `sample_count`: Validation parameter - ensures it doesn't exceed buffer capacity (default: buffer capacity)
- Note: The actual buffer size is determined by the template parameter and cannot be changed at runtime

#### TimeDurationMovingAverage

```python
# With both sensor rate and window duration
TimeDurationMovingAverageDouble(sensor_hz, window_duration)
```
- `sensor_hz`: Expected sample rate in Hz (samples per second)
- `window_duration`: Time window for averaging in milliseconds

### Methods and Properties

#### FixedMovingAverage

- `update(new_value)` - Add a new value and return current average
- `reset()` - Clear all stored values
- `current_size() / size` - Current number of samples in window (property)
- `capacity() / max_size` - Maximum capacity of window (property)

#### TimeDurationMovingAverage

- `update(new_value)` - Add a new value and return current average
- `reset()` - Clear all stored values
- `set_parameters(sensor_hz, window_duration)` - Update both parameters
- `set_sensor_hz(sensor_hz)` - Update sensor rate
- `set_window_duration(window_duration)` - Update window duration
- `current_size() / size` - Current number of samples in window (property)
- `get_sensor_hz() / sensor_hz` - Current sensor rate in Hz (property)
- `get_window_duration() / window_duration` - Current window duration in ms (property)
- `get_calculated_window_size() / calculated_window_size` - Optimal window size (property)
- `capacity() / max_size` - Maximum capacity of window (property)

## Running Tests

```bash
# Make sure the module is built first
python test_python_bindings.py
```

The test suite includes:
- Import tests
- FixedMovingAverage with double and float precision
- TimeDurationMovingAverage with double and float precision
- Error handling
- Different buffer sizes

## Troubleshooting

### ImportError: No module named 'py_moving_average'

Make sure you've built the module:
```bash
cd custom_lib
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

On macOS:
```bash
xcode-select --install
```

### Permission errors

Try building with user permissions or use a virtual environment.