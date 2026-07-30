# Execution Instructions for All Nodes

## Prerequisites

Ensure the ROS 2 environment is sourced:
```bash
source /opt/ros/jazzy/setup.bash
source /workspace/colcon_ws/install/setup.bash
```

---

## 1. Data Publisher Node (`sensor_streamer`)

The `sensor_streamer` package provides a flexible data publisher that supports both synthetic data generation and real CSV data replay. It uses ROS 2 parameters loaded from YAML configuration files for synthetic mode.

### Synthetic data mode (default):
```bash
# Use default synthetic params from config/synthetic_params.yaml
ros2 run sensor_streamer sensor_play

# Or specify custom YAML config
ros2 run sensor_streamer sensor_play --config config/synthetic_params.yaml
```

### Replay mode (pushes real data from sensor_log.csv):
```bash
ros2 run sensor_streamer sensor_play --replay sensor_log.csv
```

### Command-line arguments for sensor_play:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--replay` | str | None | Path to CSV file for replay mode. When specified, runs `ReplayDataNode` |
| `--config` | str | `config/synthetic_params.yaml` | Path to YAML config file for synthetic mode. When specified, runs `SyntheticDataNode` with custom params |

### ReplayDataNode Parameters:
- Automatically loads CSV with columns: `timestamp_s`, `encoder_count`, `accel_x_mss`
- Publishes at original timestamps from CSV to preserve real timing including jitter and dropout gaps

### Published topics (both modes):
- `/encoder_count` (std_msgs/Int32) - Integer stream (encoder counts from wheel rotation)
- `/accel_x_mss` (std_msgs/Float32) - Floating-point stream (IMU X-axis acceleration in m/s²)

### Synthetic YAML Configuration Template:

All synthetic data parameters are configurable via YAML. The default configuration file is at `colcon_ws/src/sensor_streamer/config/synthetic_params.yaml`:

```yaml
synthetic_sensor:
  ros__parameters:
    # Shared motion parameters (for generating sine wave patterns)
    amplitudes: [1.0, 0.3, 0.1]          # Amplitude for each sine wave component
    frequencies: [0.5, 1.5, 3.0]         # Frequency (Hz) for each sine wave
    phases: [0.0, 0.0, 0.0]             # Phase offset (radians) for each component
    wheel_circumference: 0.203         # Wheel circumference in meters
    counts_per_revolution: 4096        # Encoder counts per full revolution

    # IMU settings (high rate)
    imu:
      rate: 200.0                       # Publish rate in Hz
      noise_std: 0.05                 # Standard deviation of Gaussian noise added to acceleration
      drop_rate: 0.005                # Probability (0-1) of randomly dropping a sample
      jitter_range: 0.1               # ±20% jitter as fraction of period (0.1 = ±10%)

    # Encoder settings (lower rate)
    encoder:
      rate: 50.0                        # Publish rate in Hz  
      drop_rate: 0.01                 # Probability (0-1) of randomly dropping a sample
      jitter_range: 0.15              # ±30% jitter as fraction of period (0.15 = ±15%)
```

### Synthetic node parameters (loaded from YAML):

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `amplitudes` | float[] | Amplitude for each sine wave component in the motion model | `[1.0, 0.3, 0.1]` |
| `frequencies` | float[] | Frequency (Hz) for each sine wave component | `[0.5, 1.5, 3.0]` |
| `phases` | float[] | Phase offset (radians) for each component | `[0.0, 0.0, 0.0]` |
| `wheel_circumference` | float | Wheel circumference in meters (for encoder count calculation) | `0.203` |
| `counts_per_revolution` | int | Encoder counts per full revolution | `4096` |
| `imu.rate` | float | IMU publish rate in Hz | `200.0` |
| `imu.noise_std` | float | Standard deviation of Gaussian noise for IMU | `0.05` |
| `imu.drop_rate` | float | IMU sample drop probability (0-1) | `0.005` |
| `imu.jitter_range` | float | IMU jitter as fraction of period (±value) | `0.1` |
| `encoder.rate` | float | Encoder publish rate in Hz | `50.0` |
| `encoder.drop_rate` | float | Encoder sample drop probability (0-1) | `0.01` |
| `encoder.jitter_range` | float | Encoder jitter as fraction of period (±value) | `0.15` |

---

## 2. C++ Processing Node (`signal_processing_cpp`)

The C++ processing nodes use **hardcoded topic names** (not configurable via command-line). Filter parameters are configurable via ROS 2 parameters.

### Moving Average Filter Node:
```bash
# With ROS 2 parameters
ros2 run signal_processing_cpp mean_filter_node --ros-args -p ma_window_size:=32 -p use_time_based_ma:=true -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

### Low-Pass Filter Node:
```bash
# With ROS 2 parameters
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p fixed_point_bits:=16 -p timeout_seconds:=0.15
```

### C++ Node Parameters:

**`mean_filter_node` (Moving Average):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ma_window_size` | int | 5 | Number of samples for fixed-size moving average |
| `ma_window_duration_ms` | float | 100.0 | Window duration in milliseconds for time-based MA |
| `use_time_based_ma` | bool | false | If true, uses TimeDurationMovingAverage; if false, uses FixedMovingAverage |
| `timeout_seconds` | float | 10.0 | Filter state timeout for handling dropout gaps (seconds) |

**`lp_node` (Low-Pass Filter):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lp_cutoff_hz` | float | 10.0 | Cutoff frequency in Hz |
| `fixed_point_bits` | int | 16 | Fixed-point precision: 8 = Q24.8, 16 = Q16.16 |
| `timeout_seconds` | float | 10.0 | Filter state timeout for handling dropout gaps (seconds) |

### Hardcoded Topic Names (C++ nodes):
- Subscribes to: `/encoder_count` (Int32), `/accel_x_mss` (Float32)
- Publishes to: `/mean_encoder` (Int32), `/mean_accel` (Float32) for MA node, or `/lp_encoder` (Int32), `/lp_accel` (Float32) for LP node

---

## 3. Python Processing Node (`signal_processing_py`)

The Python processing nodes are split into separate nodes for each filter type (unlike the C++ nodes which are separate). They also use **hardcoded topic names** with configurable filter parameters via ROS 2 parameters.

### Low-Pass Filter Node:
```bash
# With ROS 2 parameters
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15
```

### Fixed Moving Average Node:
```bash
# With ROS 2 parameters
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15
```

### Time-Duration Moving Average Node:
```bash
# With ROS 2 parameters
ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

### Python Node Parameters:

**`lp_node` (Low-Pass Filter):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lp_cutoff_hz` | float | 10.0 | Cutoff frequency in Hz |
| `timeout_seconds` | float | 10.0 | Filter state timeout for handling dropout gaps (seconds) |

**`fixed_ma_node` (Fixed Moving Average):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ma_window_size` | int | 5 | Number of samples for fixed-size moving average |
| `timeout_seconds` | float | 0.15 | Filter state timeout for handling dropout gaps (seconds) |

**`time_ma_node` (Time-Duration Moving Average):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ma_window_size` | int | 5 | Maximum number of samples in the time window |
| `ma_window_duration_ms` | float | 200.0 | Time window duration in milliseconds |
| `timeout_seconds` | float | 0.15 | Filter state timeout for handling dropout gaps (seconds) |

**Hardcoded Topic Names (Python nodes):**
- Subscribes to: `/encoder_count` (Int32), `/accel_x_mss` (Float32) for all nodes
- Publishes to: `/lp_encoder` (Int32), `/lp_accel` (Float32) for LP node; `/fixed_ma_encoder` (Int32), `/fixed_ma_accel` (Float32) for fixed MA node; `/time_ma_encoder` (Int32), `/time_ma_accel` (Float32) for time MA node

---

## 4. Complete Pipeline Execution

### With Synthetic Data and Custom YAML Config:

```bash
# Terminal 1: Publisher with custom synthetic config
ros2 run sensor_streamer sensor_play --config config/synthetic_params.yaml

# Terminal 2: C++ Processing - Low-Pass Filter
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 3: C++ Processing - Moving Average Filter
ros2 run signal_processing_cpp mean_filter_node --ros-args -p ma_window_size:=32 -p use_time_based_ma:=true -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15

# Terminal 4: Python Processing - Low-Pass Filter
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0 -p timeout_seconds:=0.15

# Terminal 5: Python Processing - Fixed Moving Average
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32 -p timeout_seconds:=0.15

# Terminal 6: Python Processing - Time-Duration Moving Average
ros2 run signal_processing_py time_ma_node --ros-args -p ma_window_size:=32 -p ma_window_duration_ms:=500.0 -p timeout_seconds:=0.15
```

### With Real Data Replay (matching analysis in Data Analysis section):

```bash
# Terminal 1: Replay publisher (uses original sensor_log.csv)
ros2 run sensor_streamer sensor_play --replay sensor_log.csv

# Terminal 2: C++ Low-Pass Processing
ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=7.0

# Terminal 3: C++ Moving Average Processing
ros2 run signal_processing_cpp mean_filter_node --ros-args -p ma_window_size:=32 -p use_time_based_ma:=true -p ma_window_duration_ms:=500.0

# Terminal 4: Python Low-Pass Processing
ros2 run signal_processing_py lp_node --ros-args -p lp_cutoff_hz:=7.0

# Terminal 5: Python Fixed Moving Average Processing
ros2 run signal_processing_py fixed_ma_node --ros-args -p ma_window_size:=32
```

---

## Verification Commands

```bash
# View available topics
ros2 topic list

# Monitor specific topics
ros2 topic echo /encoder_count
ros2 topic echo /accel_x_mss
ros2 topic echo /lp_encoder
ros2 topic echo /lp_accel
ros2 topic echo /mean_encoder
ros2 topic echo /mean_accel
ros2 topic echo /fixed_ma_encoder
ros2 topic echo /fixed_ma_accel
ros2 topic echo /time_ma_encoder
ros2 topic echo /time_ma_accel

# Compare C++ and Python outputs numerically
# (Both use same underlying C++ library via pybind11, so outputs should match)
python3 -c "import py_filter; import py_moving_average; print('Verify matching outputs')"
```