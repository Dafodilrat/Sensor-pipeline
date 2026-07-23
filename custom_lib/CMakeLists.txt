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
set(MOVING_AVG_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/moving_avg/lib)

# =============================================================================
# Tools Library (RingBuffer)
# =============================================================================

add_library(tools STATIC
    ${TOOLS_DIR}/ring_buffer.hpp
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
# Moving Average Library
# =============================================================================

add_library(moving_avg STATIC
    ${MOVING_AVG_LIB_DIR}/fixed_moving_average.hpp
    ${MOVING_AVG_LIB_DIR}/time_duration_moving_average.hpp
)

target_include_directories(moving_avg
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${MOVING_AVG_LIB_DIR}
        ${FILTERS_LIB_DIR}
        ${TOOLS_DIR}
        ${FPM_INCLUDE_DIR}
)

target_link_libraries(moving_avg PUBLIC filters tools)

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
# py_moving_average Python Extension Module
# =============================================================================

add_library(py_moving_average MODULE
    ${CMAKE_CURRENT_SOURCE_DIR}/moving_avg/src/py_moving_average_bindings.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/moving_avg/src/py_moving_average_module.cpp
)

target_include_directories(py_moving_average
    PRIVATE
        ${Python3_INCLUDE_DIRS}
        ${pybind11_INCLUDE_DIRS}
        ${MOVING_AVG_LIB_DIR}
        ${FILTERS_LIB_DIR}
        ${TOOLS_DIR}
        ${FPM_INCLUDE_DIR}
)

target_link_libraries(py_moving_average
    PRIVATE
        moving_avg
        filters
        tools
        Python3::Python
        pybind11::embed
)

# Set module name for Python
set_target_properties(py_moving_average PROPERTIES
    PREFIX ""
    SUFFIX "${Python3_MODULE_EXTENSION}"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/moving_avg
)

# =============================================================================
# Install Targets
# =============================================================================

install(TARGETS py_filter py_moving_average
    LIBRARY DESTINATION lib
)

install(DIRECTORY ${FILTERS_LIB_DIR}/ DESTINATION include/filters)
install(DIRECTORY ${MOVING_AVG_LIB_DIR}/ DESTINATION include/moving_avg)
install(DIRECTORY ${TOOLS_DIR}/ DESTINATION include/tools)

# =============================================================================
# Test Build (Optional)
# =============================================================================

if(BUILD_TESTS)
    add_subdirectory(test)
endif()
