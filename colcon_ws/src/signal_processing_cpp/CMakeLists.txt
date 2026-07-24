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
add_executable(cpp_processing_node
    src/cpp_processing_node.cpp
)

# Build the LP node
add_executable(lp_node
    src/lp_node.cpp
)

# Set C++ standard
set_target_properties(cpp_processing_node PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

set_target_properties(lp_node PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

target_include_directories(cpp_processing_node PRIVATE
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE.include>"
    ${CUSTOM_LIB_PATH}/tools
    ${CUSTOM_LIB_PATH}/filters/lib
    ${CUSTOM_LIB_PATH}/running_data/lib
)

target_include_directories(lp_node PRIVATE
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
    "$<INSTALL_INTERFACE.include>"
    ${CUSTOM_LIB_PATH}/tools
    ${CUSTOM_LIB_PATH}/filters/lib
    ${CUSTOM_LIB_PATH}/running_data/lib
)

# Link against ROS2 libraries and FPM if available
target_link_libraries(cpp_processing_node
    rclcpp
    std_msgs
)

target_link_libraries(lp_node
    rclcpp
    std_msgs
)

# If FPM is built as a library, link against it
find_package(fpm QUIET)
if(fpm_FOUND)
    target_link_libraries(cpp_processing_node PRIVATE fpm)
    target_link_libraries(lp_node PRIVATE fpm)
endif()

# Install
install(TARGETS cpp_processing_node lp_node
    DESTINATION lib/${PROJECT_NAME}
)

# Install package.xml for ROS2
install(FILES
    package.xml
    DESTINATION share/${PROJECT_NAME}
)

ament_package()
