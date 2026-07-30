# Project Report: Signal Processing Pipeline (ROS2)

This report documents the complete Signal Processing Pipeline project, including design decisions, data analysis, implementation details, and execution instructions.

## Report Structure

- **[Design Decisions](design_decisions.md)** - Architecture choices, project structure, and technical design
- **[Prerequisites](prerequisites.md)** - System requirements, dependencies, and version specifications  
- **[Build Instructions](build_instructions.md)** - Step-by-step guides for standalone, ROS 2, and Docker builds
- **[Data Analysis](data_analysis.md)** - FFT analysis, noise characteristics, and filter parameter justification
- **[Execution Instructions](execution_instructions.md)** - How to run all nodes and the complete pipeline
- **[Benchmark Results](benchmark_results.md)** - Performance measurements and results
- **[Instructions](instructions.md)** - Complete commands for benchmarking, sensor replay, and signal processing nodes

## Latest Benchmark

The most recent benchmark results are from [fixed_ma_benchmark_200hz_20260729_200803.json](file:///home/dafodilrat/Documents/projects/naweRobotics/colcon_ws/results/olde/fixed_ma_benchmark_200hz_20260729_200803.json):

- **Filter Type**: FIXED MEAN FILTER
- **Sensor Type**: IMU
- **Timestamp**: 20260729_200803
- **Throughput**: 200.09 Hz ( target: 200.0 Hz ✅)
- **Average Processing Time**: 64.21 μs
- **Utilization**: 12.84%
- **Result**: Can keep up with real-time processing ✅

See [Benchmark Results](benchmark_results.md) for detailed analysis.