cmake_minimum_required(VERSION 3.8)
project(signal_processing_cpp)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Find custom_lib pathways
# Try multiple methods to locate the library

# Method 1: Try find_package if nawe_robotics_lib CMake config exists
find_package(nawe_robotics_lib QUIET)
if(nawe_robotics_lib_FOUND)
    message(STATUS "Found nawe_robotics_lib via CMake config")
    set(CUSTOM_LIB_FOUND TRUE)
    set(CUSTOM_LIB_INCLUDE_DIR "${nawe_robotics_lib_INCLUDE_DIRS}")
endif()

# Method 2: Check if custom_lib is installed as a system package
if(NOT CUSTOM_LIB_FOUND)
    find_path(CUSTOM_LIB_FOUND
        NAMES filters/lib/low_pass_iir_filter.hpp
        PATHS
        ${CMAKE_INSTALL_PREFIX}/include
        /usr/local/include
        /usr/include
        NO_DEFAULT_PATH
    )
endif()

# Method 4: Check environment variable
if(NOT CUSTOM_LIB_FOUND AND DEFINED ENV{CUSTOM_LIB_PATH})
    if(EXISTS "$ENV{CUSTOM_LIB_PATH}/filters/lib/low_pass_iir_filter.hpp")
        set(CUSTOM_LIB_FOUND TRUE)
        set(CUSTOM_LIB_INCLUDE_DIR "$ENV{CUSTOM_LIB_PATH}")
    endif()
endif()

if(CUSTOM_LIB_FOUND)
    message(STATUS "Found custom_lib headers at: ${CUSTOM_LIB_INCLUDE_DIR}")
    include_directories(${CUSTOM_LIB_INCLUDE_DIR})
else()
    message(FATAL_ERROR "custom_lib not found. Please ensure it is installed or set CUSTOM_LIB_PATH environment variable.")
endif()

# Build the LP node
add_executable(lp_node
    src/lp_node.cpp
)

# Build the Fixed MA node
add_executable(fixed_ma_node
    src/fixed_ma_node.cpp
)

# Build the Time MA node
add_executable(time_ma_node
    src/time_ma_node.cpp
)

# Set C++ standard
set_target_properties(lp_node PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

set_target_properties(fixed_ma_node PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

set_target_properties(time_ma_node PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

target_include_directories(lp_node PRIVATE
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE:include>"
    ${CUSTOM_LIB_INCLUDE_DIR}
)

target_include_directories(fixed_ma_node PRIVATE
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE:include>"
    ${CUSTOM_LIB_INCLUDE_DIR}
)

target_include_directories(time_ma_node PRIVATE
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE:include>"
    ${CUSTOM_LIB_INCLUDE_DIR}
)

# Link against ROS2 libraries (uses plain signatures inside Jazzy's macro)
ament_target_dependencies(lp_node
    rclcpp
    std_msgs
)

ament_target_dependencies(fixed_ma_node
    rclcpp
    std_msgs
)

ament_target_dependencies(time_ma_node
    rclcpp
    std_msgs
)

# Link against nawe_robotics_lib headers if found (using PLAIN signature to match Jazzy)
if(nawe_robotics_lib_FOUND)
    target_link_libraries(lp_node nawe_robotics_lib::headers)
    target_link_libraries(fixed_ma_node nawe_robotics_lib::headers)
    target_link_libraries(time_ma_node nawe_robotics_lib::headers)
endif()

# If FPM is built as a library, link against it (using PLAIN signature to match Jazzy)
find_package(fpm QUIET)
if(fpm_FOUND)
    target_link_libraries(lp_node fpm)
    target_link_libraries(fixed_ma_node fpm)
    target_link_libraries(time_ma_node fpm)
endif()

# Install binary nodes
install(TARGETS lp_node fixed_ma_node time_ma_node
    DESTINATION lib/${PROJECT_NAME}
)

# Install package.xml for ROS2
install(FILES
    package.xml
    DESTINATION share/${PROJECT_NAME}
)

ament_package()
