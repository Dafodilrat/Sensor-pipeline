# Benchmark & Signal Processing Execution Guide

This guide provides all the commands needed to run benchmarks, sensor data replay, and signal processing nodes for performance testing and validation.

---

## Prerequisites

Ensure you have completed the following setup:

```bash
# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash

# Source workspace (in Docker or local development)
source /workspace/colcon_ws/install/setup.bash
```

---

## 1. Sensor Data Replay

### Basic Replay from CSV

```bash
# Replay sensor_log.csv with original timestamps (preserves jitter and dropouts)
ros2 launch sensor_streamer replay.launch.py csv:=sensor_log.csv
```

### Replay with Custom CSV File

```bash
# Replay from a custom CSV file path
ros2 launch sensor_streamer replay.launch.py csv:=/path/to/your/sensor_data.csv
```

### Synthetic Data Generation (Alternative to Replay)

```bash
# Generate synthetic data using default configuration
ros2 launch sensor_streamer synthetic_sensor.launch.py

# Use custom YAML configuration
ros2 launch sensor_streamer synthetic_sensor.launch.py config_file:=config/synthetic_params.yaml

# Override specific parameters
ros2 launch sensor_streamer synthetic_sensor.launch.py imu_rate:=500.0 encoder_rate:=10.0
```

#### Example YAML Configuration

Here is an example YAML configuration file format for the synthetic sensor. You can create your own file and pass it with `--config`:

```yaml
synthetic_sensor:
  ros__parameters:
    # Shared motion parameters (supports any number of elements)
    amplitudes:
      - 1.0
      - 0.3
      - 0.1
    frequencies:
      - 0.5
      - 1.5
      - 3.0
    phases:
      - 0.0
      - 0.0
      - 0.0
    wheel_circumference: 0.203
    counts_per_revolution: 4096
    seed: 42

    # IMU settings
    imu:
      rate: 2000.0
      noise_std: 0.00
      drop_rate: 0.000
      jitter_range: 0.0

    # Encoder settings
    encoder:
      rate: 1.0
      drop_rate: 0.00
      jitter_range: 0.00
```

**Note:** The `synthetic_sensor: ros__parameters:` wrapper is required for ROS 2 parameter file compatibility.

### Launch File Arguments

#### Replay Launch (`replay.launch.py`)
| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `csv` | str | *required* | Path to CSV file for replay |
| `namespace` | str | `''` | ROS namespace for sensor topics |

#### Synthetic Sensor Launch (`synthetic_sensor.launch.py`)
| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `config_file` | str | `config/synthetic_params.yaml` | Path to YAML config file |
| `namespace` | str | `''` | ROS namespace for sensor topics |
| `seed` | int | `42` | Random seed for repeatable data |
| `imu_rate` | float | `2000.0` | IMU publish rate in Hz |
| `encoder_rate` | float | `1.0` | Encoder publish rate in Hz |

### Published Topics (Replay Mode)
- `/encoder_count` (std_msgs/Int32) - Encoder counts from wheel rotation
- `/accel_x_mss` (std_msgs/Float32) - IMU X-axis acceleration in m/s²

---

## 2. Signal Processing Nodes

### C++ Processing Nodes

#### C++ Fixed Moving Average Filter
```bash
# Fixed moving average with 32 samples, 150ms timeout
ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15
```

#### C++ Time-Duration Moving Average Filter
```bash
# Time-duration moving average with 500ms window, 150ms timeout
ros2 run signal_processing_cpp time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

#### C++ Low-Pass Filter
```bash
# Low-pass filter with 7.0 Hz cutoff, 150ms timeout
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15
```

### Python Processing Nodes

#### Python Low-Pass Filter
```bash
# Low-pass filter with 7.0 Hz cutoff, 150ms timeout
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15
```

#### Python Fixed Moving Average
```bash
# Fixed moving average with 32 samples, 150ms timeout
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15
```

#### Python Time-Duration Moving Average
```bash
# Time-duration moving average with 500ms window, 150ms timeout
ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

---

## 3. Benchmark Commands

### Running Benchmarks with Launch Files (Recommended)

Use the provided launch files for complete benchmark setups:

#### Low-Pass Filter Benchmark
```bash
# Run low-pass filter benchmark with all custom parameters
ros2 launch benchmark benchmark_low_pass.launch.py \
    lp_cutoff_hz:=7.0 \
    timeout_seconds:=0.15 \
    test_duration:=30.0 \
    warmup_duration:=2.0 \
    imu_rate:=200.0
```

#### Mean Filter Benchmark
```bash
# Run mean filter benchmark with all custom parameters
ros2 launch benchmark benchmark_mean_filter.launch.py \
    ma_window_size:=32 \
    ma_timeout_seconds:=0.15 \
    test_duration:=30.0 \
    warmup_duration:=2.0 \
    imu_rate:=200.0 \
```

> **Note:** Results are stored under the results directory at the root of the ROS workspace.

---

## 4. Verification Commands

### Check Topic List
```bash
ros2 topic list
```

### Monitor Input Topics
```bash
# Original sensor data
ros2 topic echo /encoder_count
ros2 topic echo /accel_x_mss
```

### Monitor Processed Topics

#### Moving Average Outputs
```bash
# C++ fixed moving average outputs
ros2 topic echo /fixed_ma_encoder
ros2 topic echo /fixed_ma_accel

# C++ time-duration moving average outputs
ros2 topic echo /time_ma_encoder
ros2 topic echo /time_ma_accel
```

#### Low-Pass Filter Outputs
```bash
# C++ low-pass filter outputs
ros2 topic echo /lp_encoder
ros2 topic echo /lp_accel
```

### Rate Monitoring
```bash
# Monitor input rates
ros2 topic hz /encoder_count
ros2 topic hz /accel_x_mss

# Monitor processing rates
ros2 topic hz /fixed_ma_encoder
ros2 topic hz /fixed_ma_accel
ros2 topic hz /time_ma_encoder
ros2 topic hz /time_ma_accel
ros2 topic hz /lp_encoder
ros2 topic hz /lp_accel
```

---

## 5. Topic Name Reference

### Input Topics (Published by sensor_streamer)
| Topic | Type | Description |
|-------|------|-------------|
| `/encoder_count` | std_msgs/Int32 | Encoder counts from wheel rotation |
| `/accel_x_mss` | std_msgs/Float32 | IMU X-axis acceleration in m/s² |

### Output Topics by Node

#### C++ Nodes (signal_processing_cpp)
| Node | Output Topics | Description |
|------|---------------|-------------|
| `fixed_ma_node` | `/fixed_ma_encoder`, `/fixed_ma_accel` | Fixed window moving average filtered outputs |
| `time_ma_node` | `/time_ma_encoder`, `/time_ma_accel` | Time-duration moving average filtered outputs |
| `lp_node` | `/lp_encoder`, `/lp_accel` | Low-pass filtered outputs |

#### Python Nodes (signal_processing_py)
| Node | Output Topics | Description |
|------|---------------|-------------|
| `lp_node` | `/lp_encoder`, `/lp_accel` | Low-pass filtered outputs |
| `fixed_ma_node` | `/fixed_ma_encoder`, `/fixed_ma_accel` | Fixed moving average outputs |
| `time_ma_node` | `/time_ma_encoder`, `/time_ma_accel` | Time-duration moving average outputs |

---

## 6. Common Issues and Fixes

### ROS 2 Environment Not Sourced
```bash
source /opt/ros/jazzy/setup.bash
source /workspace/colcon_ws/install/setup.bash
```

### Nodes Not Found
```bash
# Ensure workspace is built
cd /workspace/colcon_ws
colcon build
source install/setup.bash
```

### CSV File Not Found
```bash
# Copy sensor_log.csv to the correct location or specify full path
ros2 run sensor_streamer sensor_play --replay /full/path/to/sensor_log.csv
```

### Topic Mismatch
```bash
# All nodes expect these exact topic names:
# Input: /encoder_count, /accel_x_mss
# Verify publisher is using these names
ros2 topic list
```

---

## 7. Configuration Summary

- **Sample Rate**: 200 Hz (for IMU data in sensor_log.csv)
- **Timeout**: 150ms (0.15 seconds) - matches dropout gap in data
- **Moving Average Window**: 32 samples (~160ms at 200 Hz)
- **Time-Duration MA Window**: 500ms maximum duration
- **Low-Pass Cutoff**: 7.0 Hz (preserves signal below ~6 Hz, attenuates above ~8.5 Hz)