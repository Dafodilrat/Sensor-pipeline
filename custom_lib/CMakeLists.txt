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
# FPM Dependency (Fixed Point Math Library) - REQUIRED
# =============================================================================

include(FetchContent)

# Check if FPM_ROOT environment variable is set
if(DEFINED ENV{FPM_ROOT} AND EXISTS "$ENV{FPM_ROOT}/include/fpm/fixed.hpp")
    set(FPM_INCLUDE_DIR "$ENV{FPM_ROOT}/include")
    message(STATUS "Found FPM via FPM_ROOT: ${FPM_INCLUDE_DIR}")
else()
    # Download FPM from GitHub using FetchContent
    FetchContent_Declare(
        fpm
        GIT_REPOSITORY https://github.com/MikeLankamp/fpm
        GIT_SHALLOW TRUE
    )
    
    # Set output directory for FPM
    set(FETCHCONTENT_BASE_DIR ${CMAKE_BINARY_DIR}/fpm_fetch)
    
    message(STATUS "Downloading FPM from GitHub...")
    FetchContent_MakeAvailable(fpm)
    
    # Set FPM include directory to the downloaded source
    set(FPM_INCLUDE_DIR ${fpm_SOURCE_DIR}/include)
    
    message(STATUS "FPM downloaded to: ${FPM_INCLUDE_DIR}")
endif()

# Verify FPM headers exist
if(NOT EXISTS "${FPM_INCLUDE_DIR}/fpm/fixed.hpp")
    message(FATAL_ERROR 
        "\n"
        "=============================================================================\n"
        "FPM (Fixed Point Math Library) is REQUIRED for this project.\n"
        "\n"
        "Expected to find FPM headers at: ${FPM_INCLUDE_DIR}/fpm/fixed.hpp\n"
        "\n"
        "OPTION 1: Set FPM_ROOT environment variable\n"
        "  export FPM_ROOT=/path/to/fpm/installation\n"
        "  cmake .. -DFPM_ROOT=$FPM_ROOT\n"
        "\n"
        "=============================================================================\n"
    )
else()
    message(STATUS "Found FPM headers at: ${FPM_INCLUDE_DIR}")
endif()

# =============================================================================
# Project Structure
# =============================================================================

set(TOOLS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/tools)
set(FILTERS_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/filters/lib)
set(RUNNING_DATA_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/running_data/lib)

# =============================================================================
# Tools Library (RingBuffer, FixedHeap, FixedPriorityQueue)
# =============================================================================

add_library(tools INTERFACE)

target_include_directories(tools
    INTERFACE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${TOOLS_DIR}
)

# =============================================================================
# Filters Library
# =============================================================================

add_library(filters INTERFACE)

target_include_directories(filters
    INTERFACE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${FILTERS_LIB_DIR}
        ${FPM_INCLUDE_DIR}
        ${TOOLS_DIR}
)

target_link_libraries(filters INTERFACE tools)

# =============================================================================
# Running Data Library (formerly Moving Average)
# =============================================================================

add_library(running_data INTERFACE)

target_include_directories(running_data
    INTERFACE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${RUNNING_DATA_LIB_DIR}
        ${FILTERS_LIB_DIR}
        ${FPM_INCLUDE_DIR}
        ${TOOLS_DIR}
)

target_link_libraries(running_data INTERFACE filters tools)

# =============================================================================
# py_filter Python Extension Module
# =============================================================================

# Find Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Use FetchContent for pybind11
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.11.1
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(pybind11)

# py_filter module
add_library(py_filter MODULE
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
