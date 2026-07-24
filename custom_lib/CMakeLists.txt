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

# FPM is a header-only library for fixed-point arithmetic
# We need to download it since it's not available in the container

# Try to download FPM from GitHub using file(DOWNLOAD)
# This avoids git dependency issues in containers
set(FPM_URL "https://codeload.github.com/MikePopoloski/fpm/tar.gz/v0.13.0")
set(FPM_DOWNLOAD_DIR "${CMAKE_BINARY_DIR}/fpm-download")

# Create download directory
file(MAKE_DIRECTORY ${FPM_DOWNLOAD_DIR})

# Download FPM tarball
file(DOWNLOAD ${FPM_URL} ${FPM_DOWNLOAD_DIR}/fpm-0.13.0.tar.gz
     STATUS fpm_download_status
     LOG fpm_download_log
     TIMEOUT 60
)

if(fpm_download_status EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-0.13.0.tar.gz")
    # Extract the tarball
    execute_process(
        COMMAND ${CMAKE_COMMAND} -E tar xzf ${FPM_DOWNLOAD_DIR}/fpm-0.13.0.tar.gz
        WORKING_DIRECTORY ${FPM_DOWNLOAD_DIR}
        RESULT_VARIABLE extract_result
        OUTPUT_QUIET
    )
    
    if(extract_result EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-0.13.0/include/fpm/fixed.hpp")
        # FPM successfully downloaded and extracted
        set(FPM_INCLUDE_DIR "${FPM_DOWNLOAD_DIR}/fpm-0.13.0/include")
        message(STATUS "FPM downloaded and extracted to: ${FPM_DOWNLOAD_DIR}/fpm-0.13.0")
    else()
        message(WARNING "Failed to extract FPM tarball. Trying alternative method...")
        set(FPM_INCLUDE_DIR "")
    endif()
else()
    message(WARNING "Failed to download FPM: ${fpm_download_log}")
    message(WARNING "Status: ${fpm_download_status}")
    
    # Try alternative URL format
    set(FPM_URL_ALT "https://codeload.github.com/MikePopoloski/fpm/tar.gz/refs/tags/v0.13.0")
    file(DOWNLOAD ${FPM_URL_ALT} ${FPM_DOWNLOAD_DIR}/fpm-alt.tar.gz
         STATUS fpm_alt_status
         LOG fpm_alt_log
         TIMEOUT 60
    )
    
    if(fpm_alt_status EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-alt.tar.gz")
        execute_process(
            COMMAND ${CMAKE_COMMAND} -E tar xzf ${FPM_DOWNLOAD_DIR}/fpm-alt.tar.gz
            WORKING_DIRECTORY ${FPM_DOWNLOAD_DIR}
            RESULT_VARIABLE extract_alt_result
            OUTPUT_QUIET
        )
        
        if(extract_alt_result EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-0.13.0/include/fpm/fixed.hpp")
            set(FPM_INCLUDE_DIR "${FPM_DOWNLOAD_DIR}/fpm-0.13.0/include")
            message(STATUS "FPM downloaded (alt URL) and extracted to: ${FPM_DOWNLOAD_DIR}/fpm-0.13.0")
        else()
            message(WARNING "FPM is required for fixed-point filters. Trying to use local fallback...")
            set(FPM_INCLUDE_DIR "")
        endif()
    else()
        message(WARNING "FPM is required for fixed-point filters. Trying to use local fallback...")
        set(FPM_INCLUDE_DIR "")
    endif()
endif()

# Check if we successfully got FPM
if(NOT FPM_INCLUDE_DIR OR NOT EXISTS "${FPM_INCLUDE_DIR}/fpm/fixed.hpp")
    # Last resort: create a warning and set empty path
    # Fixed-point filters will not compile without FPM
    message(WARNING "FPM library not available. Fixed-point filters will be disabled.")
    message(WARNING "To enable fixed-point filters, ensure FPM is available at: ${FPM_INCLUDE_DIR}")
    set(FPM_FOUND FALSE)
else()
    set(FPM_FOUND TRUE)
    message(STATUS "FPM include directory: ${FPM_INCLUDE_DIR}")
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

# Build base filters (float) - these don't require FPM
add_library(filters STATIC
    ${FILTERS_LIB_DIR}/base_filter.hpp
    ${FILTERS_LIB_DIR}/base_iir_filter.hpp
    ${FILTERS_LIB_DIR}/float_low_pass_filter.hpp
)

target_include_directories(filters
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${FILTERS_LIB_DIR}
        ${TOOLS_DIR}
)

target_link_libraries(filters PUBLIC tools)

# Build fixed-point filters only if FPM is available
if(FPM_FOUND)
    target_include_directories(filters
        PUBLIC
            ${FPM_INCLUDE_DIR}
    )
    
    # Add fixed-point filter source files
    target_sources(filters
        PRIVATE
            ${FILTERS_LIB_DIR}/fixed_point_low_pass_filter.hpp
    )
    
    message(STATUS "Fixed-point filters enabled (FPM available)")
else()
    message(WARNING "Fixed-point filters disabled (FPM not available)")
endif()

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
)

# Add FPM include directory if available
if(FPM_FOUND)
    target_include_directories(running_data
        PUBLIC
            ${FPM_INCLUDE_DIR}
    )
endif()

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
)

# Add FPM include directory if available
if(FPM_FOUND)
    target_include_directories(py_filter
        PRIVATE
            ${FPM_INCLUDE_DIR}
    )
endif()

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
)

# Add FPM include directory if available
if(FPM_FOUND)
    target_include_directories(py_median_filter
        PRIVATE
            ${FPM_INCLUDE_DIR}
    )
endif()

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
)

# Add FPM include directory if available
if(FPM_FOUND)
    target_include_directories(py_moving_average
        PRIVATE
            ${FPM_INCLUDE_DIR}
    )
endif()

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
