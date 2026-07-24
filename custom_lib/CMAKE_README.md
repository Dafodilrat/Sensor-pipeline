# CMake Build System for naweRobotics Signal Processing Libraries

This directory contains a modern CMake-based build system for the naweRobotics signal processing libraries, including filters and running_data components.

## Prerequisites

- CMake 3.15 or higher
- C++17 compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- Python 3.7+ with development headers
- pybind11 (will be found via Python package or installed automatically)

## Quick Start

### Linux/macOS

```bash
# Create build directory
mkdir build && cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build all targets
cmake --build . -j$(nproc)

# Install (optional)
cmake --install . --prefix /path/to/install
```

### Windows

```cmd
mkdir build
cd build

cmake .. -G "Visual Studio 17 2022" -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

## CMake Options

| Option | Default | Description |
|--------|---------|-------------|
| `BUILD_TESTS` | OFF | Build test executables |
| `CMAKE_BUILD_TYPE` | (none) | Build type (Debug, Release, RelWithDebInfo) |
| `CMAKE_INSTALL_PREFIX` | /usr/local | Installation prefix |

## Build Targets

### Libraries
- `tools` - RingBuffer, FixedHeap, and FixedPriorityQueue implementations
- `filters` - Filter classes (BaseFilter, BaseIIRFilter, FixedPointLowPassFilter, FloatLowPassFilter)
- `running_data` - Running data classes (FixedMovingAverage, TimeDurationMovingAverage, MedianFilter)

### Python Modules
- `py_filter` - Python bindings for filter library (low-pass filters)
- `py_moving_average` - Python bindings for running data library (moving averages)
- `py_median_filter` - Python bindings for median filter (demonstrates extensibility)

## Using FPM

FPM (Fixed Point Math) is automatically downloaded via CMake's FetchContent:

```cmake
# Uses FetchContent to get FPM v0.13.0 from GitHub
include(FetchContent)
FetchContent_MakeAvailable(fpm)
```

### Alternative: System-wide FPM

If you have FPM installed system-wide:

1. Install FPM headers to `/usr/local/include/fpm` or similar
2. Modify CMakeLists.txt to use `find_package(fpm CONFIG)` instead

## Project Structure

```
custom_lib/
├── CMakeLists.txt              # Main CMake configuration
├── CMAKE_README.md            # This document
├── examples.py                # Common examples for all libraries
├── README_python.md           # Python bindings documentation
├── EXTENSIBILITY.md          # Extensibility demonstration documentation
├── tools/
│   ├── ring_buffer.hpp         # Ring buffer implementation
│   ├── fixed_heap.hpp          # Fixed-size heap implementation
│   └── fixed_priority_queue.hpp # Fixed-size priority queue
├── filters/
│   ├── lib/
│   │   ├── base_filter.hpp
│   │   ├── base_iir_filter.hpp
│   │   ├── float_low_pass_filter.hpp
│   │   └── fixed_point_low_pass_filter.hpp
│   ├── src/
│   │   ├── filter_bindings.cpp
│   │   └── py_filter_module.cpp
│   └── README.md              # Filters library documentation
├── running_data/
│   ├── lib/
│   │   ├── fixed_moving_average.hpp
│   │   ├── time_duration_moving_average.hpp
│   │   └── median_filter.hpp
│   ├── src/
│   │   ├── py_moving_average_bindings.cpp
│   │   ├── py_moving_average_module.cpp
│   │   ├── median_filter_bindings.cpp
│   │   └── py_median_filter_module.cpp
│   └── README.md              # Running data library documentation
└── test/
    ├── CMakeLists.txt
    ├── filters/
    │   └── test_*              # Filter test files
    └── running_data/
        └── test_*              # Running data test files
```

## Customizing the Build

### Change FPM Version

Edit the FetchContent declaration in CMakeLists.txt:

```cmake
FetchContent_Declare(
    fpm
    GIT_REPOSITORY https://github.com/MikePopoloski/fpm.git
    GIT_TAG v0.14.0  # Change to desired version
)
```

### Add New Filters or Moving Averages

1. Add header file to `filters/lib/` or `running_data/lib/`
2. Add source file to `filters/src/` or `running_data/src/` if needed
3. Update the corresponding library target in CMakeLists.txt
4. Add bindings if exposing to Python

**Note**: The architecture supports extensibility without modifying existing files. See `EXTENSIBILITY.md` for the median filter demonstration.

### Using as a Dependency

To use this library in another CMake project:

```cmake
# Option 1: Add as subdirectory
add_subdirectory(path/to/custom_lib)
target_link_libraries(your_target PRIVATE filters running_data tools)

# Option 2: Install and find
find_package(naweRoboticsFilters REQUIRED)
target_link_libraries(your_target PRIVATE 
    naweRobotics::filters 
    naweRobotics::running_data 
    naweRobotics::tools
)
```

## Examples

A comprehensive examples file is provided that demonstrates all library functionality:

```bash
# Run all examples
cd custom_lib
python examples.py

# Run specific demos
python examples.py Filters          # Only filters library demos
python examples.py Running          # Only running_data library demos
python examples.py Extensibility    # Extensibility demonstration

# Get help
python examples.py --help
```

The examples cover:
- Fixed-point and floating-point filters with various Q-formats
- Moving average filters (fixed and time-duration based)
- Noise filtering applications
- Integration between libraries
- Extensibility patterns

## Troubleshooting

### FPM not found

```
CMake Error: FetchContent failed to download fpm
```

Solution: Check your internet connection and Git accessibility.

### Python headers not found

```
CMake Error: Could NOT find Python3
```

Solution: Install Python development headers:
- Ubuntu: `sudo apt-get install python3-dev`
- CentOS: `sudo yum install python3-devel`
- macOS: Install from python.org or use Homebrew

### pybind11 not found

```
CMake Error: Could NOT find pybind11
```

Solution: Install via pip:
```bash
pip install pybind11
```

Or specify the path:
```cmake
set(pybind11_DIR /path/to/pybind11/cmake)
```

## Clean Build

```bash
# Remove build directory completely
rm -rf build

# Reconfigure from scratch
mkdir build && cd build
cmake ..
```
