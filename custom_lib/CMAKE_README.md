# CMake Build System for naweRobotics Filters

This directory contains a modern CMake-based build system for the naweRobotics filter library.

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
- `tools` - RingBuffer implementation
- `filters` - Filter classes (BaseFilter, BaseIIRFilter, FixedPointLowPassFilter, FloatLowPassFilter)
- `moving_avg` - Moving average classes (FixedMovingAverage, TimeDurationMovingAverage)

### Python Modules
- `py_filter` - Python bindings for filter library
- `py_moving_average` - Python bindings for moving average library

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
├── tools/
│   └── ring_buffer.hpp         # Ring buffer implementation
├── filters/
│   ├── lib/
│   │   ├── base_filter.hpp
│   │   ├── base_iir_filter.hpp
│   │   ├── float_low_pass_filter.hpp
│   │   └── fixed_point_low_pass_filter.hpp
│   └── src/
│       ├── filter_bindings.cpp
│       └── py_filter_module.cpp
├── moving_avg/
│   ├── lib/
│   │   ├── fixed_moving_average.hpp
│   │   └── time_duration_moving_average.hpp
│   └── src/
│       ├── py_moving_average_bindings.cpp
│       └── py_moving_average_module.cpp
└── test/
    └── CMakeLists.txt
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

### Add New Filters

1. Add header file to `filters/lib/`
2. Add source file to `filters/src/` if needed
3. Update the `filters` library target in CMakeLists.txt
4. Add bindings if exposing to Python

### Using as a Dependency

To use this library in another CMake project:

```cmake
# Option 1: Add as subdirectory
add_subdirectory(path/to/custom_lib)
target_link_libraries(your_target PRIVATE filters moving_avg)

# Option 2: Install and find
find_package(naweRoboticsFilters REQUIRED)
target_link_libraries(your_target PRIVATE naweRobotics::filters)
```

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
