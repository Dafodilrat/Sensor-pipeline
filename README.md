# Sensor Pipeline

## Project Overview

Welcome to the Sensor Pipeline project - a high-performance signal processing pipeline for ROS 2 applications featuring fixed-point arithmetic, moving average filters, and low-pass filters optimized for real-time sensor data processing.

## Documentation

For comprehensive project documentation, please see the [report/](./report/) directory which contains:

- **[Project Report Index](report/README.md)** - Main report overview and navigation
- **[Design Decisions](report/design_decisions.md)** - Architecture choices and technical design rationale
- **[Prerequisites](report/prerequisites.md)** - System requirements and dependencies
- **[Build Instructions](report/build_instructions.md)** - Complete build guides for all platforms
- **[Data Analysis](report/data_analysis.md)** - FFT analysis and filter parameter justification
- **[Execution Instructions](report/execution_instructions.md)** - How to run all nodes and the complete pipeline
- **[Benchmark Results](report/benchmark_results.md)** - Performance measurements and results

## Quick Start

### Docker (Recommended)
```bash
# Build and start the development container
docker compose build
docker compose up -d

# Enter the container
docker exec -it ros2_jazzy_container bash

# Build and run the pipeline
cd /workspace/colcon_ws
colcon build
source install/setup.bash
```

### Standalone Library
```bash
cd custom_lib
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
pip install -e ..
```

### Full ROS 2 Build
```bash
# In colcon_ws directory
colcon build
source install/setup.bash
```

## Project Structure

```
naweRobotics/
├── custom_lib/                    # Standalone C++ signal processing library
├── colcon_ws/                     # ROS 2 workspace with all packages
├── confidential/                 # Configuration and data files
├── report/                        # Detailed project documentation (NEW)
│   ├── README.md                  # Report overview and navigation
│   ├── design_decisions.md        # Architecture and design details
│   ├── prerequisites.md          # System requirements
│   ├── build_instructions.md      # Build guides
│   ├── data_analysis.md           # FFT analysis and filter justification
│   ├── execution_instructions.md # Node execution guides
│   └── benchmark_results.md       # Performance benchmarks
├── Dockerfile                    # Container configuration
├── docker-compose.yaml           # Development environment
└── README.md                     # This file
```

## Recent Updates

- **2026-07-29**: Added comprehensive report folder with split documentation for easier maintenance
- **2026-07-29**: Latest benchmark results show fixed mean filter achieving 200.09 Hz throughput at 12.84% CPU utilization

## Latest Performance Results

🟢 **Fixed Mean Filter (2026-07-29)**: 200.09 Hz achieved, 12.84% CPU usage, **PASSED**

See [Benchmark Results](report/benchmark_results.md) for detailed performance analysis.

## License

This project is proprietary and confidential. For usage rights and restrictions, please refer to the project documentation or contact the maintainers.

## Support

For questions or issues, please refer to the documentation in the [report/](./report/) directory or consult the project maintainers.