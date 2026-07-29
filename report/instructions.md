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
ros2 run sensor_streamer sensor_play --replay sensor_log.csv
```

### Replay with Custom CSV File

```bash
# Replay from a custom CSV file path
ros2 run sensor_streamer sensor_play --replay /path/to/your/sensor_data.csv
```

### Synthetic Data Generation (Alternative to Replay)

```bash
# Generate synthetic data using default configuration
ros2 run sensor_streamer sensor_play

# Use custom YAML configuration
ros2 run sensor_streamer sensor_play --config config/synthetic_params.yaml
```

### Replay Command-line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--replay` | str | None | Path to CSV file for replay mode |
| `--config` | str | `config/synthetic_params.yaml` | Path to YAML config file for synthetic mode |

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
# Low-pass filter with 7.0 Hz cutoff, default timeout (10.0s)
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0

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

## 3. Complete Pipeline Execution Commands

### Pipeline with Real Data Replay (Benchmark Configuration)

This configuration matches the data analysis in the report and uses the ~150ms dropout gap data:

```bash
# Terminal 1: Replay publisher (uses original sensor_log.csv)
ros2 run sensor_streamer sensor_play --replay sensor_log.csv

# Terminal 2: C++ Low-Pass Processing with 7.0 Hz cutoff
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 3: C++ Fixed Moving Average Processing with 32 samples
ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 4: C++ Time-Duration Moving Average Processing with 500ms window
ros2 run signal_processing_cpp time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15

# Terminal 5: Python Low-Pass Processing with 7.0 Hz cutoff
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 6: Python Fixed Moving Average with 32 samples
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 7: Python Time-Duration Moving Average with 500ms window
ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

### Full Pipeline with Synthetic Data

```bash
# Terminal 1: Synthetic publisher with custom configuration
ros2 run sensor_streamer sensor_play --config config/synthetic_params.yaml

# Terminal 2: C++ Low-Pass Filter
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 3: C++ Fixed Moving Average Filter
ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 4: C++ Time-Duration Moving Average Filter
ros2 run signal_processing_cpp time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15

# Terminal 5: Python Low-Pass Filter
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 6: Python Fixed Moving Average
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 7: Python Time-Duration Moving Average
ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

---

## 4. Benchmark Commands

### Running Benchmarks with Launch Files (Recommended)

Use the provided launch files for complete benchmark setups:

```bash
# Run low-pass filter benchmark with all dependencies
ros2 launch benchmark benchmark_low_pass.launch.py

# Run low-pass filter benchmark with custom cutoff frequency
ros2 launch benchmark benchmark_low_pass.launch.py lp_cutoff_hz:=5.0

# Run low-pass filter benchmark with custom duration
ros2 launch benchmark benchmark_low_pass.launch.py test_duration:=60.0

# Run low-pass filter benchmark with all custom parameters
ros2 launch benchmark benchmark_low_pass.launch.py \
    lp_cutoff_hz:=7.0 \
    timeout_seconds:=0.15 \
    test_duration:=30.0 \
    warmup_duration:=2.0
```

### Running Individual Node Benchmarks

The benchmark nodes are designed to test performance with specific parameters:

```bash
# Run fixed moving average benchmark at 200 Hz
# Note: Use the benchmark package if available
ros2 run benchmark benchmark_node --ros-args -p filter_type:=fixed_ma -p expected_rate:=200.0 -p test_duration:=10.0 -p measure_latency:=true
```

### Manual Benchmarking with Replay Data

For manual benchmarking using the sensor replay:

```bash
# Terminal 1: Start replay at known rate
ros2 run sensor_streamer sensor_play --replay sensor_log.csv

# Terminal 2: Start the node to benchmark (example: fixed moving average)
ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 3: Monitor performance (use ROS 2 tools)
ros2 topic hz /accel_x_mss
ros2 topic hz /fixed_ma_accel
```

---

## 5. Verification Commands

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

# Python fixed moving average outputs  
ros2 topic echo /fixed_ma_encoder
ros2 topic echo /fixed_ma_accel

# Python time-duration moving average outputs
ros2 topic echo /time_ma_encoder
ros2 topic echo /time_ma_accel
```

#### Low-Pass Filter Outputs
```bash
# C++ low-pass filter outputs
ros2 topic echo /lp_encoder
ros2 topic echo /lp_accel

# Python low-pass filter outputs
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

## 6. Dense Pipeline Commands (All Nodes Together)

### Complete Benchmark Pipeline (7 Terminals)

```bash
# Terminal 1: Data source
ros2 run sensor_streamer sensor_play --replay sensor_log.csv

# Terminal 2: C++ Low-Pass Filter
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 3: C++ Fixed Moving Average Filter  
ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 4: C++ Time-Duration Moving Average Filter
ros2 run signal_processing_cpp time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15

# Terminal 5: Python Low-Pass Filter
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 6: Python Fixed Moving Average
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 7: Python Time-Duration Moving Average
ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

---

## 7. Quick Start Scripts

### Save as `run_benchmark.sh`
```bash
#!/bin/bash
# Quick script to start the benchmark pipeline

# Start replay in background
ros2 run sensor_streamer sensor_play --replay sensor_log.csv &
REPLAY_PID=$!

# Give replay time to start
sleep 2

# Start processing nodes
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15 &
ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15 &
ros2 run signal_processing_cpp time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15 &
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15 &

# Monitor topics
ros2 topic list
ros2 topic hz /accel_x_mss
ros2 topic hz /fixed_ma_accel
ros2 topic hz /time_ma_accel
ros2 topic hz /lp_accel

# Cleanup on exit
kill $REPLAY_PID
```

---

## 8. Topic Name Reference

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

## 9. Common Issues and Fixes

###ROS 2 Environment Not Sourced
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

## Configuration Summary

- **Sample Rate**: 200 Hz (for IMU data in sensor_log.csv)
- **Timeout**: 150ms (0.15 seconds) - matches dropout gap in data
- **Moving Average Window**: 32 samples (~160ms at 200 Hz)
- **Time-Duration MA Window**: 500ms maximum duration
- **Low-Pass Cutoff**: 7.0 Hz (preserves signal below ~6 Hz, attenuates above ~8.5 Hz)