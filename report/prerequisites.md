# Prerequisites

## Operating System
- **Recommended**: Ubuntu 24.04 LTS
- **Alternative**: Any Linux distribution

## ROS Version
- **ROS 2 Jazzy Jalisco**

## Python Version
- **Development**: Python 3.12+
- **Minimum Supported**: Python 3.7+

## C++ Compiler
- **GCC 11+** or **Clang 12+** with C++17 support

## Build Tools
- **CMake 3.15+** (for FetchContent support)
- **pip 21+** (modern package installation)
- **setuptools 65+**
- **wheel**
- **pybind11 2.6.0+** (Python-C++ binding generation)

## Dependencies

### External Libraries
- **FPM (Fixed Point Math) library** - Automatically cloned via FetchContent or git submodule
- **numpy** - For Python bindings

### ROS 2 Packages
- `rclcpp`
- `sensor_msgs`
- `std_msgs`

## Component Requirements Summary

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| **GCC** | 11+ | C++20 support for templates and modern features |
| **CMake** | 3.15+ | FetchContent support for dependency management |
| **Python** | 3.12 (dev), 3.7+ (runtime) | pybind11 compatibility |
| **pip** | 21+ | Modern package installation |
| **pybind11** | 2.6.0+ | Python-C++ binding generation |
| **FPM** | Latest | Fixed-point math operations |

## Installation Commands (Ubuntu 24.04)

```bash
# Update package lists
sudo apt update

# Install compiler and build tools
sudo apt install -y gcc-12 g++-12 cmake build-essential

# Install Python development tools
sudo apt install -y python3-dev python3-pip python3-venv python3-setuptools

# Install ROS 2 Jazzy and dependencies
sudo apt install -y ros-jazzy-desktop ros-jazzy-sensor-msgs ros-jazzy-rclcpp ros-jazzy-std-msgs

# Install pip dependencies
pip install --upgrade pip setuptools wheel
pip install pybind11>=2.6.0 numpy
```

## Environment Setup

Add these to your `.bashrc` or `.zshrc` for development:

```bash
# ROS 2 Jazzy
export ROS_DISTRO=jazzy
source /opt/ros/jazzy/setup.bash

# Python
export PYTHONPATH="/home/dafodilrat/Documents/projects/naweRobotics/custom_lib:$PYTHONPATH"
```

## Docker Environment

The project includes a pre-configured Docker environment that handles all dependencies automatically. See [Build Instructions](build_instructions.md#docker-build-recommended-for-development) for Docker setup.