# Design Decisions

## Project Structure

```
naweRobotics/
├── custom_lib/                    # Standalone C++ signal processing library
│   ├── CMakeLists.txt             # Library build configuration
│   ├── filters/
│   │   └── lib/
│   │       ├── low_pass_iir_filter.hpp
│   │       └── fixed_point_low_pass_filter.hpp
│   ├── running_data/
│   │   └── lib/
│   │       ├── fixed_moving_average.hpp
│   │       ├── median_filter.hpp
│   │       └── time_duration_moving_average.hpp
│   ├── tools/
│   │   ├── fixed_heap.hpp
│   │   ├── fixed_priority_queue.hpp
│   │   └── ring_buffer.hpp
│   ├── setup.py
│   └── pyproject.toml
│
├── colcon_ws/                     # ROS 2 workspace
│   └── src/
│       ├── sensor_streamer/       # Python: data generation & replay
│       │   ├── config/
│       │   │   └── synthetic_params.yaml
│       │   ├── launch/
│       │   │   ├── synthetic_sensor.launch.py
│       │   │   └── synthetic_sensor_cpp.launch.py
│       │   ├── sensor_streamer/
│       │   │   ├── generator.py
│       │   │   ├── replay.py
│       │   │   └── synthetic_sensor_node.py
│       │   └── setup.py
│       └── signal_processing_cpp/  # C++: filter nodes
│           ├── launch/
│           │   ├── lp_launch.py
│           │   ├── ma_launch.py
│           │   └── td_ma_launch.py
│           └── src/
│               ├── lp_node.cpp
│               ├── fixed_ma_node.cpp
│               └── time_ma_node.cpp
│
├── Dockerfile
├── docker-compose.yaml
└── README.md
```

The project follows a strict separation between core signal processing logic (`custom_lib`) and ROS integration (`colcon_ws`). This enables independent testing of the library and reuse outside ROS environments.

## Prerequisites

### ROS Version
- **ROS 2 Humble Hawksbill**

### Compiler Requirements
- **C++17** or later
- **GCC** 9+ or **Clang** 10+ recommended

### Python Requirements
- **Python 3.8** or later
- Required packages: `numpy`, `pandas`, `scipy`, `matplotlib`

## Design Decisions

### Modular Architecture
The signal processing library (`custom_lib`) has zero ROS dependencies. All ROS-specific code is in the `colcon_ws` workspace. This separation enables:
- Independent library testing and development
- Reuse of signal processing logic outside ROS
- Clear dependency boundaries

### Type-Generic Filters
All filters use C++ templates to support both integer and floating-point types through a single code path, eliminating duplication and ensuring consistent behavior.

### Buffer Size Configuration
Three distinct buffer sizes for `FixedMovingAverage`:
- **8 samples**: High-rate IMUs (200-1000 Hz)
- **32 samples**: Medium-rate sensors (10-50 Hz)
- **128 samples**: Low-rate sensors (1-10 Hz)

### Floating-Point Precision
The library uses `float` internally for sum accumulation and time tracking. Specialized fixed-point implementation (`fixed_point_low_pass_filter.hpp`) is retained for pure integer arithmetic use cases.

### Timeout Handling
- **150ms timeout** for all filters, matching the dropout gap observed in `sensor_log.csv`
- Moving average filters: reset internal buffer and sum when gap > timeout
- LP filters: dynamically compute alpha from actual dt to prevent stale state

### Memory Constraints
All filters pre-allocate memory at initialization. The processing path has zero dynamic allocation, using fixed-size ring buffers.
