# nawe_robotics_lib CMake Config File
# This allows CMake packages to find nawe_robotics_lib via find_package()

# Get the directory where this config file is located
get_filename_component(_nawe_robotics_lib_CONFIG_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)

# Calculate the base installation directory (go up from cmake/nawe_robotics_lib to the prefix)
# Typical layout: /usr/local/lib/cmake/nawe_robotics_lib/nawe_robotics_libConfig.cmake
# We want: /usr/local/include/nawe_robotics_lib
get_filename_component(_nawe_robotics_lib_PREFIX "${_nawe_robotics_lib_CONFIG_DIR}/../../.." ABSOLUTE)
set(nawe_robotics_lib_INCLUDE_DIR "${_nawe_robotics_lib_PREFIX}/include/nawe_robotics_lib")

# Set variables
set(nawe_robotics_lib_INCLUDE_DIRS "${nawe_robotics_lib_INCLUDE_DIR}")
set(nawe_robotics_lib_VERSION 1.0.0)

# Mark as found
set(nawe_robotics_lib_FOUND TRUE)

# Define imported target for headers
if(NOT TARGET nawe_robotics_lib::headers)
    add_library(nawe_robotics_lib::headers INTERFACE IMPORTED)
    target_include_directories(nawe_robotics_lib::headers
        INTERFACE
            "${nawe_robotics_lib_INCLUDE_DIR}/tools"
            "${nawe_robotics_lib_INCLUDE_DIR}/filters/lib"
            "${nawe_robotics_lib_INCLUDE_DIR}/running_data/lib"
    )
endif()
