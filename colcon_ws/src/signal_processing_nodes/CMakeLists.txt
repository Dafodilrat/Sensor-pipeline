cmake_minimum_required(VERSION 3.8)
project(signal_processing_nodes)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Add custom lib as include directory
# This assumes custom_lib is a sibling directory
get_filename_component(CUSTOM_LIB_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../../../custom_lib" ABSOLUTE)

if(EXISTS "${CUSTOM_LIB_PATH}")
    message(STATUS "Found custom_lib at: ${CUSTOM_LIB_PATH}")
    include_directories(
        ${CUSTOM_LIB_PATH}/tools
        ${CUSTOM_LIB_PATH}/filters/lib
        ${CUSTOM_LIB_PATH}/running_data/lib
    )
else()
    message(WARNING "custom_lib not found at ${CUSTOM_LIB_PATH}")
endif()

# Build the C++ processing node
if(BUILD_CPP_NODE)
    add_executable(cpp_processing_node
        src/cpp_processing_node.cpp
    )
    
    target_include_directories(cpp_processing_node PRIVATE
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE/include>"
        ${CUSTOM_LIB_PATH}/tools
        ${CUSTOM_LIB_PATH}/filters/lib
        ${CUSTOM_LIB_PATH}/running_data/lib
    )
    
    # Link against ROS2 libraries and FPM if available
    target_link_libraries(cpp_processing_node
        rclcpp
        std_msgs
    )
    
    # If FPM is built as a library, link against it
    find_package(fpm QUIET)
    if(fpm_FOUND)
        target_link_libraries(cpp_processing_node PRIVATE fpm)
    endif()
    
    # Install
    install(TARGETS cpp_processing_node
        DESTINATION lib/${PROJECT_NAME}
    )
endif()

# Python processing node (uses setup.py)
if(BUILD_PYTHON_NODE)
    # Install Python scripts
    install(PROGRAMS
        signal_processing_nodes/python_processing_node.py
        DESTINATION lib/${PROJECT_NAME}
    )
    
    # Install package.xml for ROS2
    install(FILES
        package.xml
        DESTINATION share/${PROJECT_NAME}
    )
endif()

# Build both by default
option(BUILD_CPP_NODE "Build C++ processing node" ON)
option(BUILD_PYTHON_NODE "Build Python processing node" ON)

ament_package()
