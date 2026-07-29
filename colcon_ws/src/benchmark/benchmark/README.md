# Benchmark Package

This ROS2 package provides a benchmarking suite for the signal processing pipeline, specifically designed to address **Task 4.3** from the robotics software engineer assignment.

## Purpose

The `benchmark` package tests whether the mean average filter can keep up with high-rate sensor data streams, particularly:
- **IMU data at 200Hz** (primary focus)
- **Encoder data at default rate** (typically 50Hz)

## Package Structure

```
benchmark/
├── CMakeLists.txt          # CMake build configuration
├── package.xml            # ROS2 package manifest
├── setup.py               # Python package setup
├── setup.cfg              # Python package configuration
├── config/
│   └── benchmark_params.yaml  # Configurable benchmark parameters
├── resource/
│   └── benchmark          # ROS2 package resource
└── benchmark/
    ├── __init__.py         # Python package init
    ├── benchmark_py_node.py  # Python benchmark node
    ├── benchmark_node.cpp   # C++ benchmark node
    └── performance_comparison.py  # Standalone benchmark suite for Task 4.3
```

## Features

### 1. ROS2 Benchmark Node (C++)
- **Node Name**: `benchmark_node`
- **Subscribes to**: 
  - `/accel_x_mss` (Float32) - IMU acceleration data
  - `/encoder_count` (Int32) - Encoder position data
- **Publishes**:
  - `/filtered_accel_x_mss` - Filtered IMU data
  - `/filtered_encoder_count` - Filtered encoder data  
  - `/benchmark_stats` - Performance statistics
- **Filter Types**: Configurable moving average filters (fixed-size or time-based)

### 2. ROS2 Benchmark Node (Python)
- **Node Name**: `benchmark_py_node`
- **Same subscriptions and publications as C++ version**
- **Uses pybind11 bindings** to the standalone C++ library
- **Enables direct comparison** between C++ and Python performance

### 3. Standalone Performance Comparison Script
- **File**: `performance_comparison.py`
- **Purpose**: Task 4.3 - Benchmark table generation
- **Measures**:
  - Latency at different rates (10Hz, 200Hz, 2kHz, 20kHz)
  - Throughput performance
  - CPU utilization
  - Memory usage
- **Compares**: C++ vs Python-bound path performance
- **Identifies**: Bottlenecks at highest feasible rates

## Configuration

The package uses a YAML configuration file at `config/benchmark_params.yaml`:

```yaml
benchmark_node:
  ros__parameters:
    # IMU configuration (200Hz high-rate stream)
    imu:
      rate: 200.0
      noise_std: 0.05
      drop_rate: 0.005
      jitter_range: 0.1
    
    # Encoder configuration
    encoder:
      rate: 50.0
      drop_rate: 0.01
      jitter_range: 0.15
    
    # Mean Filter configuration
    mean_filter:
      window_size: 10
      use_time_based: false
      window_duration_ms: 50.0
      timeout_seconds: 5.0
    
    # Benchmark settings
    benchmark:
      test_duration: 30.0
      warmup_duration: 2.0
      measure_latency: true
      measure_throughput: true
      max_acceptable_latency_us: 1000
      expected_imu_rate: 200.0
      expected_encoder_rate: 50.0
      rate_tolerance_percent: 5.0
```

## Usage

### 1. Building the Package

```bash
# From the workspace root
colcon build --packages-select benchmark
source install/setup.bash
```

### 2. Running the C++ Benchmark Node

```bash
# With default parameters
ros2 run benchmark benchmark_node

# With custom configuration
ros2 run benchmark benchmark_node --ros-args --params-file /path/to/custom_config.yaml
```

### 3. Running the Python Benchmark Node

```bash
# With default parameters (uses benchmark_params.yaml from package)
ros2 run benchmark benchmark_py_node

# With custom configuration
ros2 run benchmark benchmark_py_node --ros-args --params-file /path/to/custom_config.yaml
```

### 4. Running the Performance Comparison Suite (Standalone)

```bash
# Run the complete benchmark suite for Task 4.3
python3 /path/to/benchmark/benchmark/performance_comparison.py
```

## Expected Output

### ROS2 Nodes
Both C++ and Python nodes will output:
- Filter initialization information
- Real-time statistics every second (configurable)
- Latency warnings if processing exceeds acceptable limits
- Final assessment of whether the mean filter can keep up with 200Hz

### Performance Comparison Script
The standalone script provides:
1. **Performance by rate**: Throughput and latency at different frequencies
2. **Bottleneck analysis**: Identifies what limits performance at highest rates
3. **C++ vs Python comparison**: Shows speedup factors
4. **Final assessment**: Explicit answer to "Can the mean filter keep up with 200Hz?"

## Integration with Existing Pipeline

This package integrates with the existing signal processing pipeline:

```
sensor_streamer (generates data)
    ├── accel_x_mss (Float32) --> benchmark_node --> filtered_accel_x_mss
    └── encoder_count (Int32)  --> benchmark_node --> filtered_encoder_count
```

The benchmark node can be connected to either:
- **Synthetic data generator** from `sensor_streamer` package
- **Replay node** that replay the `sensor_log.csv` data

## Task 4.3 Deliverables

This package provides all the necessary components for **Task 4.3 - Benchmark table**:

✅ **Latency measurements** at increasing data rates
✅ **Throughput measurements** for moving-average filter  
✅ **C++ vs Python comparison** using pybind11
✅ **Bottleneck identification** with detailed analysis
✅ **High-rate testing** at 200Hz (IMU) and beyond
✅ **Configurable parameters** via YAML file

## Dependencies

- **ROS2** (tested with Humble, Foxy, Jazzy)
- **rclcpp** (for C++ node)
- **rclpy** (for Python node)
- **std_msgs** (for message types)
- **sensor_streamer** (for data source)
- **nawe_robotics_lib** (standalone signal processing library)
- **pybind11** (for Python bindings)
- **psutil** (for performance monitoring - only for standalone benchmark)

## Installation Notes

1. Ensure the custom signal processing library (`nawe_robotics_lib`) is built and accessible
2. Set `CUSTOM_LIB_PATH` environment variable if the library is not in default locations
3. For Python nodes, ensure PYTHONPATH includes the location of the compiled Python bindings

## Performance Expectations

Based on the fixed-point, no-allocation design of the signal processing library:

- **200Hz IMU data**: Should be easily achievable with < 5% CPU utilization
- **2kHz data**: Should be feasible on modern hardware
- **20kHz data**: Likely to be the upper limit, with bottleneck being CPU core utilization

The C++ implementation should be significantly faster than Python (typically 10-100x), with the main bottleneck at highest rates being CPU bound rather than memory or I/O bound.