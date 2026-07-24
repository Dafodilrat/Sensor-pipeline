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

# FPM is a REQUIRED dependency for fixed-point filters
# Users must ensure FPM is available in their build environment

# Option 1: Use system-installed FPM (recommended for production)
#   - Install via package manager: apt install libfpm-dev (if available)
#   - Or set FPM_ROOT environment variable pointing to FPM installation

# Option 2: Download automatically (for development/standalone builds)
#   - Downloads from GitHub releases using HTTPS (no git required)

# First, check if FPM is available via find_package
find_package(fpm QUIET)

if(fpm_FOUND)
    # Use system-installed FPM
    set(FPM_INCLUDE_DIR ${fpm_INCLUDE_DIRS})
    message(STATUS "Found system-installed FPM: ${FPM_INCLUDE_DIR}")
else()
    # Check if FPM_ROOT environment variable is set
    if(DEFINED ENV{FPM_ROOT} AND EXISTS "$ENV{FPM_ROOT}/include/fpm/fixed.hpp")
        set(FPM_INCLUDE_DIR "$ENV{FPM_ROOT}/include")
        message(STATUS "Found FPM via FPM_ROOT: ${FPM_INCLUDE_DIR}")
    else()
        # Try to download FPM from GitHub releases
        set(FPM_downloaded FALSE)
        
        # Primary URL: GitHub codeload service
        set(FPM_URL "https://codeload.github.com/MikePopoloski/fpm/tar.gz/v0.13.0")
        set(FPM_DOWNLOAD_DIR "${CMAKE_BINARY_DIR}/fpm-download")
        
        file(MAKE_DIRECTORY ${FPM_DOWNLOAD_DIR})
        
        message(STATUS "FPM not found. Attempting to download from GitHub...")
        
        # Download FPM tarball
        file(DOWNLOAD ${FPM_URL} ${FPM_DOWNLOAD_DIR}/fpm-v0.13.0.tar.gz
             STATUS fpm_download_status
             LOG fpm_download_log
             TIMEOUT 60
        )
        
        if(fpm_download_status EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-v0.13.0.tar.gz")
            # Extract the tarball
            execute_process(
                COMMAND ${CMAKE_COMMAND} -E tar xzf ${FPM_DOWNLOAD_DIR}/fpm-v0.13.0.tar.gz
                WORKING_DIRECTORY ${FPM_DOWNLOAD_DIR}
                RESULT_VARIABLE extract_result
                OUTPUT_QUIET
            )
            
            if(extract_result EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-0.13.0/include/fpm/fixed.hpp")
                set(FPM_INCLUDE_DIR "${FPM_DOWNLOAD_DIR}/fpm-0.13.0/include")
                set(FPM_downloaded TRUE)
                message(STATUS "Successfully downloaded FPM to: ${FPM_INCLUDE_DIR}")
            else()
                message(WARNING "Failed to extract FPM tarball")
            endif()
        else()
            message(WARNING "Failed to download FPM: ${fpm_download_log}")
            
            # Try backup URL
            set(FPM_URL_BACKUP "https://codeload.github.com/MikePopoloski/fpm/tar.gz/ref/tags/v0.13.0")
            message(STATUS "Trying backup URL...")
            
            file(DOWNLOAD ${FPM_URL_BACKUP} ${FPM_DOWNLOAD_DIR}/fpm-backup.tar.gz
                 STATUS fpm_backup_status
                 LOG fpm_backup_log
                 TIMEOUT 60
            )
            
            if(fpm_backup_status EQUAL 0 AND EXISTS "${FPM_DOWNLOAD_DIR}/fpm-backup.tar.gz")
                execute_process(
                    COMMAND ${CMAKE_COMMAND} -E tar xzf ${FPM_DOWNLOAD_DIR}/fpm-backup.tar.gz
                    WORKING_DIRECTORY ${FPM_DOWNLOAD_DIR}
                    RESULT_VARIABLE extract_backup_result
                    OUTPUT_QUIET
                )
                
                if(extract_backup_result EQUAL 0)
                    # Find the extracted directory
                    file(GLOB extracted_dir RELATIVE ${FPM_DOWNLOAD_DIR} ${FPM_DOWNLOAD_DIR}/fpm-*)
                    if(extracted_dir)
                        list(GET extracted_dir 0 first_dir)
                        if(EXISTS "${FPM_DOWNLOAD_DIR}/${first_dir}/include/fpm/fixed.hpp")
                            set(FPM_INCLUDE_DIR "${FPM_DOWNLOAD_DIR}/${first_dir}/include")
                            set(FPM_downloaded TRUE)
                            message(STATUS "Successfully downloaded FPM (backup URL) to: ${FPM_INCLUDE_DIR}")
                        endif()
                    endif()
                endif()
            else()
                message(WARNING "Failed to download FPM from backup URL: ${fpm_backup_log}")
            endif()
        endif()
        
        # Final check
        if(NOT FPM_downloaded)
            message(FATAL_ERROR 
                "\n"
                "=============================================================================\n"
                "FPM (Fixed Point Math Library) is REQUIRED for this project.\n"
                "\n"
                "To resolve this issue, please use ONE of the following options:\n"
                "\n"
                "OPTION 1: Install FPM system-wide\n"
                "  - Linux (Debian/Ubuntu): sudo apt install libfpm-dev\n"
                "  - Or build from source: https://github.com/MikePopoloski/fpm\n"
                "\n"
                "OPTION 2: Set FPM_ROOT environment variable\n"
                "  export FPM_ROOT=/path/to/fpm/installation\n"
                "  cmake .. -DFPM_ROOT=$FPM_ROOT\n"
                "\n"
                "OPTION 3: Ensure network access for automatic download\n"
                "  - This build requires HTTPS access to GitHub\n"
                "  - The automatic download may be blocked by firewall/proxy\n"
                "\n"
                "=============================================================================\n"
            )
        endif()
    endif()
endif()

# Verify FPM is available
if(NOT EXISTS "${FPM_INCLUDE_DIR}/fpm/fixed.hpp")
    message(FATAL_ERROR "FPM not found at: ${FPM_INCLUDE_DIR}\nPlease ensure FPM is properly installed.")
else()
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
        ${FPM_INCLUDE_DIR}
        ${TOOLS_DIR}
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
