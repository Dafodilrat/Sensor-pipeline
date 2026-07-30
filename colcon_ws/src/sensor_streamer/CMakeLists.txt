cmake_minimum_required(VERSION 3.8)
project(sensor_streamer)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED) # REQUIRED for proper Python support
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(Eigen3 REQUIRED)

# ==============================================================================
# 1. C++ TARGETS
# ==============================================================================

# Synthetic data generator node (C++ version)
add_executable(synthetic_sensor_node_cpp src/generator.cpp)

# Target-specific include directories (Modern CMake replacement for include_directories)
target_include_directories(synthetic_sensor_node_cpp PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Standard dependencies (Eigen is a system dependency, link it directly)
target_link_libraries(synthetic_sensor_node_cpp
  Eigen3::Eigen
)

# ROS 2 modern target dependencies (Do NOT pass Eigen3::Eigen here)
ament_target_dependencies(synthetic_sensor_node_cpp
  rclcpp
  std_msgs
)

# Install C++ executable
install(TARGETS synthetic_sensor_node_cpp
  DESTINATION lib/${PROJECT_NAME}
)

# ==============================================================================
# 2. PYTHON TARGETS & MODULES
# ==============================================================================

# Automatically installs your python library files located under your project folder
# This allows 'import sensor_streamer' to work seamlessly across files.
ament_python_install_package(${PROJECT_NAME})

# Install standalone Python script executables (nodes)
install(
  PROGRAMS 
    sensor_streamer/generator.py
    sensor_streamer/replay.py
    sensor_streamer/sensor_play.py
    sensor_streamer/synthetic_sensor_node.py
  DESTINATION lib/${PROJECT_NAME}
)

# ==============================================================================
# 3. SHARE ASSETS & EXPORTS
# ==============================================================================

# Install launch files
install(
  DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}
)

# Install config files
install(
  DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}
)

# Install resource files
install(
  DIRECTORY resource/
  DESTINATION share/${PROJECT_NAME}
)

# Export package macros for downstream packages
ament_export_include_directories(include)
ament_export_dependencies(rclcpp std_msgs Eigen3)
ament_package()
