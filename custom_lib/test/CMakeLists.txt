# =============================================================================
# Test Configuration for naweRobotics Filters
# =============================================================================

# Option 1: C++ Tests with Google Test
# Uncomment below to enable C++ unit tests
#
# include(FetchContent)
#
# FetchContent_Declare(
#     googletest
#     GIT_REPOSITORY https://github.com/google/googletest.git
#     GIT_TAG release-1.12.1
#     GIT_SHALLOW TRUE
# )
#
# FetchContent_MakeAvailable(googletest)
# enable_testing()
#
# # Add C++ tests here
# # add_executable(test_filters test/filters/test_filters.cpp)
# # target_link_libraries(test_filters PRIVATE filters tools gtest_main)
# # gtest_discover_tests(test_filters)

# Option 2: Python Tests (pytest)
# This just creates a custom target to run Python tests

if(BUILD_TESTS)
    # Find Python and pytest
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    
    # Add custom target for running all Python tests
    add_custom_target(python_tests
        COMMAND ${Python3_EXECUTABLE} -m pytest
            ${CMAKE_CURRENT_SOURCE_DIR}/test/filters/test_low_pass_filter.py
            ${CMAKE_CURRENT_SOURCE_DIR}/test/filters/test_low_pass_simple.py
            ${CMAKE_CURRENT_SOURCE_DIR}/test/test_filter_bindings.py
            ${CMAKE_CURRENT_SOURCE_DIR}/test/running_data/test_python_bindings.py
            -v
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Running Python tests with pytest"
        VERBATIM
    )
    
    # Add custom target for running individual test files
    add_custom_target(python_tests_filters
        COMMAND ${Python3_EXECUTABLE} -m pytest
            ${CMAKE_CURRENT_SOURCE_DIR}/test/filters/
            -v
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Running filter Python tests"
        VERBATIM
    )
    
    add_custom_target(python_tests_moving_avg
        COMMAND ${Python3_EXECUTABLE} -m pytest
            ${CMAKE_CURRENT_SOURCE_DIR}/test/running_data/
            -v
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Running running data Python tests"
        VERBATIM
    )
endif()
