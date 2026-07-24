# Running Data Library

This directory contains the C++ moving average implementations with Python bindings using pybind11.

## Directory Structure

```
custom_lib/running_data/
├── lib/                         # C++ header files
│   ├── fixed_moving_average.hpp
│   ├── median_filter.hpp
│   └── time_duration_moving_average.hpp
├── src/                        # Python bindings source
│   ├── median_filter_bindings.cpp
│   ├── py_median_filter_module.cpp
│   ├── py_moving_average_bindings.cpp
│   └── py_moving_average_module.cpp
└── setup.py                    # Build script for the Python module
```

## Examples

See the common examples file in the parent directory:
- `custom_lib/examples.py` - Comprehensive examples for both filters and running_data libraries

To run examples:
```bash
cd custom_lib
python examples.py                    # Run all demos
python examples.py Running          # Run running_data demos only
python examples.py "Moving Average" # Run specific demo
```

## Building

### Build the Python Module

```bash
cd custom_lib/running_data
python setup.py build_ext --inplace
```

### Prerequisites

- Python 3.7 or higher
- pip
- C++17 compatible compiler
- pybind11 (will be installed automatically if not present)

## Available Classes

### FixedMovingAverage

Template-based moving average filter with configurable window size (by sample count).

Available buffer sizes:
- **smallbuffer** - Max 100 samples
- **mediumbuffer** - Max 1000 samples  
- **largebuffer** - Max 10000 samples

Available types:
- `Integer` - int32_t values
- `Float` - float values
- `Double` - double values

### TimeDurationMovingAverage

Time-based moving average that behaves correctly under jittered/dropped samples.

Features:
- Configurable window by time duration
- Handles non-uniform sampling correctly
- Removes expired samples based on actual timestamps

Available buffer sizes and types are the same as FixedMovingAverage.

## Usage

### Fixed Moving Average

```python
import py_moving_average as pma
from py_moving_average.FixedMovingAverage.mediumbuffer import Double

# Create a fixed moving average with window size 5
ma = Double(5)

# Update with values
avg1 = ma.update(1.0)
avg2 = ma.update(2.0)
avg3 = ma.update(3.0)

# Access properties
print(f"Current size: {ma.size}")
print(f"Max size: {ma.max_size}")

# Reset
ma.reset()
```

### Time Duration Moving Average

```python
from datetime import timedelta
from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Double

# Create a time-based moving average
# window_size: max number of samples to store
# window_duration: time window for averaging
td_ma = Double(100, timedelta(milliseconds=1000))

# Update with values
avg = td_ma.update(100.5)

# Set new window duration
ma.set_window_duration(timedelta(milliseconds=500))
```

## Median Filter

A median filter implementation that demonstrates the library's extensibility.

```cpp
// In C++
#include "running_data/lib/median_filter.hpp"

// Create a median filter with window size 5
MedianFilter<int, 5> filter;

// Update with values
int result1 = filter.update(10);
int result2 = filter.update(20);
```

```python
# In Python
import py_median_filter

filter = py_median_filter.MedianFilterInt5()
result = filter.update(10)
```
