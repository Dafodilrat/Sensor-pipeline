cmake_minimum_required(VERSION 3.15)
project(naweRoboticsFilters VERSION 1.0.0 LANGUAGES CXX)

# =============================================================================
# Project Configuration
# =============================================================================

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable warnings
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# =============================================================================
# FPM Dependency (Fixed Point Math Library)
# =============================================================================

# Option 1: Use FetchContent to automatically download FPM
include(FetchContent)

FetchContent_Declare(
    fpm
    GIT_REPOSITORY https://github.com/MikePopoloski/fpm.git
    GIT_TAG v0.13.0  # Use a specific release tag
    GIT_SHALLOW TRUE
)

# Option 2: Use find_package if FPM is installed system-wide
# find_package(fpm CONFIG QUIET)

# If FPM wasn't found, use FetchContent
if(NOT fpm_FOUND)
    FetchContent_MakeAvailable(fpm)
    # FPM is header-only, so we just need its include directory
    set(FPM_INCLUDE_DIR ${fpm_SOURCE_DIR}/include)
else()
    # Use system-installed FPM
    set(FPM_INCLUDE_DIR ${fpm_INCLUDE_DIRS})
endif()

message(STATUS "FPM include directory: ${FPM_INCLUDE_DIR}")

# =============================================================================
# Project Structure
# =============================================================================

set(TOOLS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/tools)
set(FILTERS_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/filters/lib)
set(RUNNING_DATA_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/running_data/lib)

# =============================================================================
# Tools Library (RingBuffer, FixedHeap, FixedPriorityQueue)
# =============================================================================

add_library(tools STATIC
    ${TOOLS_DIR}/ring_buffer.hpp
    ${TOOLS_DIR}/fixed_heap.hpp
    ${TOOLS_DIR}/fixed_priority_queue.hpp
)

target_include_directories(tools
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${TOOLS_DIR}
)

# =============================================================================
# Filters Library
# =============================================================================

add_library(filters STATIC
    ${FILTERS_LIB_DIR}/base_filter.hpp
    ${FILTERS_LIB_DIR}/base_iir_filter.hpp
    ${FILTERS_LIB_DIR}/float_low_pass_filter.hpp
    ${FILTERS_LIB_DIR}/fixed_point_low_pass_filter.hpp
)

target_include_directories(filters
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${FILTERS_LIB_DIR}
        ${FPM_INCLUDE_DIR}
        ${TOOLS_DIR}
)

target_link_libraries(filters PUBLIC tools)

# =============================================================================
# Running Data Library (formerly Moving Average)
# =============================================================================

add_library(running_data STATIC
    ${RUNNING_DATA_LIB_DIR}/fixed_moving_average.hpp
    ${RUNNING_DATA_LIB_DIR}/time_duration_moving_average.hpp
    ${RUNNING_DATA_LIB_DIR}/median_filter.hpp
)

target_include_directories(running_data
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${RUNNING_DATA_LIB_DIR}
        ${FILTERS_LIB_DIR}
        ${TOOLS_DIR}
        ${FPM_INCLUDE_DIR}
)

target_link_libraries(running_data PUBLIC filters tools)

# =============================================================================
# py_filter Python Extension Module
# =============================================================================

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# py_filter module
add_library(py_filter MODULE
    ${CMAKE_CURRENT_SOURCE_DIR}/filters/src/filter_bindings.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/filters/src/py_filter_module.cpp
)

target_include_directories(py_filter
    PRIVATE
        ${Python3_INCLUDE_DIRS}
        ${pybind11_INCLUDE_DIRS}
        ${FILTERS_LIB_DIR}
        ${TOOLS_DIR}
        ${FPM_INCLUDE_DIR}
)

target_link_libraries(py_filter
    PRIVATE
        filters
        tools
        Python3::Python
        pybind11::embed
)

# Set module name for Python
set_target_properties(py_filter PROPERTIES
    PREFIX ""
    SUFFIX "${Python3_MODULE_EXTENSION}"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/filters
)

# =============================================================================
# py_median_filter Python Extension Module (Demonstrates Extensibility)
# This module can be added without modifying any existing files
# =============================================================================

add_library(py_median_filter MODULE
    ${CMAKE_CURRENT_SOURCE_DIR}/running_data/src/median_filter_bindings.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/running_data/src/py_median_filter_module.cpp
)

target_include_directories(py_median_filter
    PRIVATE
        ${Python3_INCLUDE_DIRS}
        ${pybind11_INCLUDE_DIRS}
        ${RUNNING_DATA_LIB_DIR}
        ${TOOLS_DIR}
        ${FPM_INCLUDE_DIR}
)

target_link_libraries(py_median_filter
    PRIVATE
        running_data
        tools
        Python3::Python
        pybind11::embed
)

# Set module name for Python
set_target_properties(py_median_filter PROPERTIES
    PREFIX ""
    SUFFIX "${Python3_MODULE_EXTENSION}"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/running_data
)

# =============================================================================
# py_moving_average Python Extension Module
# =============================================================================

add_library(py_moving_average MODULE
    ${CMAKE_CURRENT_SOURCE_DIR}/running_data/src/py_moving_average_bindings.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/running_data/src/py_moving_average_module.cpp
)

target_include_directories(py_moving_average
    PRIVATE
        ${Python3_INCLUDE_DIRS}
        ${pybind11_INCLUDE_DIRS}
        ${RUNNING_DATA_LIB_DIR}
        ${FILTERS_LIB_DIR}
        ${TOOLS_DIR}
        ${FPM_INCLUDE_DIR}
)

target_link_libraries(py_moving_average
    PRIVATE
        running_data
        filters
        tools
        Python3::Python
        pybind11::embed
)

# Set module name for Python
set_target_properties(py_moving_average PROPERTIES
    PREFIX ""
    SUFFIX "${Python3_MODULE_EXTENSION}"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/running_data
)

# =============================================================================
# Install Targets
# =============================================================================

install(TARGETS py_filter py_moving_average py_median_filter
    LIBRARY DESTINATION lib
)

install(DIRECTORY ${FILTERS_LIB_DIR}/ DESTINATION include/filters)
install(DIRECTORY ${RUNNING_DATA_LIB_DIR}/ DESTINATION include/running_data)
install(DIRECTORY ${TOOLS_DIR}/ DESTINATION include/tools)

# =============================================================================
# Test Build (Optional)
# =============================================================================

if(BUILD_TESTS)
    add_subdirectory(test)
endif()
