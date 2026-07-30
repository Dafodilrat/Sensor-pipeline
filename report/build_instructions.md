# Build Instructions

Three build methods are available for the Signal Processing Pipeline project. Choose the method that best fits your use case.

## Method A: Standalone Library (Independent Build)

Use this method if you only need the signal processing library without ROS 2 functionality.

### 1. Enter library directory
```bash
cd naweRobotics/custom_lib
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pybind11>=2.6.0 numpy
```

### 3. Build using CMake
```bash
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

The FPM library will be automatically downloaded via FetchContent.

### 4. Install Python bindings
```bash
# From custom_lib directory
pip install -e .

# Or build and install
python setup.py build_ext --inplace
```

This creates the Python modules: `py_filter`, `py_moving_average`, `py_median_filter`.

### 5. Verify standalone library
```bash
python3 -c "import py_filter; print(dir(py_filter))"
python3 examples.py
```

---

## Method B: Full ROS 2 Workspace Build

Use this method for complete ROS 2 integration with all nodes and packages.

### 1. Set up ROS 2 environment
```bash
source /opt/ros/jazzy/setup.bash
```

### 2. Install ROS 2 dependencies
```bash
sudo apt update
sudo apt install ros-jazzy-sensor-msgs ros-jazzy-rclcpp ros-jazzy-std-msgs
```

### 3. Build the standalone library first
Complete Method A steps 1-4 above, or use the pip-installable wheel.

### 4. Build the ROS workspace
```bash
cd colcon_ws
colcon build --packages-select sensor_streamer signal_processing_cpp signal_processing_py
```

Or build all packages:
```bash
colcon build
```

### 5. Source the workspace
```bash
source install/setup.bash
```

---

## Method C: Docker Build (Recommended for Development)

The recommended method to try out the project is using Docker. The workspace is already configured to mount your local `colcon_ws` and `confidential` directories into the container at `/workspace`.

### 1. Build the Docker image
```bash
docker compose build
```

To force a fresh rebuild (useful when dependencies or configuration have changed):
```bash
docker compose build --no-cache
```

### 2. Start the container
```bash
docker compose up -d
```

### 3. Enter the container
```bash
docker exec -it ros2_jazzy_container bash
```

You'll be placed in the `/workspace` directory, which contains:
- `colcon_ws/` — ROS 2 workspace with all packages
- `confidential/` — Contains CSV files (sensor_log.csv) and ROS 2 packages

### 4. Inside the container

The ROS 2 Jazzy environment is **automatically sourced** with all dependencies, and the workspace is **pre-sourced** upon container entry. You can proceed with Method B build instructions, or use the pre-configured environment directly.

**Note**: If you rebuild the container (using `docker compose build --no-cache`), you only need to re-source the workspace environment after entering the fresh container:
```bash
# After container rebuild and entering a new shell
source /opt/ros/jazzy/setup.bash
source /workspace/colcon_ws/install/setup.bash
```

The workspace will be ready to use with all ROS 2 packages and dependencies available.

---

## Build Troubleshooting

### Common Issues

**CMake can't find pybind11:**
```bash
pip install pybind11>=2.6.0
# Ensure pybind11 is in your Python path
python3 -m pip show pybind11
```

**FPM library not found:**
```bash
# Clean build directory and retry
rm -rf custom_lib/build
cd custom_lib/build
cmake .. -DCMAKE_BUILD_TYPE=Release
```

**ROS 2 packages not found:**
```bash
# Ensure ROS 2 environment is sourced
source /opt/ros/jazzy/setup.bash
# Verify installation
ros2 --version
```

### Verification Steps

After successful build:
1. All Python modules should be importable
2. C++ nodes should compile without errors
3. ROS 2 workspace should source without errors
4. Example scripts should run successfully

```bash
# Test Python bindings
cd custom_lib
python3 -c "import py_filter; import py_moving_average; print('Python bindings OK')"

# Test C++ compilation
cd colcon_ws
colcon build --packages-select signal_processing_cpp

# Test ROS 2 nodes (after build)
source install/setup.bash
ros2 run sensor_streamer sensor_play --help
```