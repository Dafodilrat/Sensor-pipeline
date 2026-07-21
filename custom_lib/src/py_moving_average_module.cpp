#include "py_moving_average_bindings.cpp"

// =============================================================================
// Main module definition
// =============================================================================

PYBIND11_MODULE(py_moving_average, m) {
    m.doc() = "Python bindings for Moving Average Library";

    // Define common buffer sizes
    constexpr size_t MEDIUM_BUFFER = 1000;

    // =========================================================================
    // Create FixedMovingAverage as a submodule with type-specific classes
    // This allows: from py_moving_average import FixedMovingAverage
    //             avg = FixedMovingAverage.Integer(100)  # max_buffer_size = 100
    //             avg.update(5)
    // =========================================================================
    
    py::module_ fixedAvgModule = py::module_::create_submodule(
        m, "FixedMovingAverage", "FixedMovingAverage with type-specific implementations");
    
    // Bind Integer version with custom buffer size support
    bind_FixedMovingAverage<int, MEDIUM_BUFFER>(fixedAvgModule, "IntegerMovingAvg");
    
    // Bind Double version 
    bind_FixedMovingAverage<double, MEDIUM_BUFFER>(fixedAvgModule, "DoubleMovingAvg");
    
    // Bind Float version
    bind_FixedMovingAverage<float, MEDIUM_BUFFER>(fixedAvgModule, "FloatMovingAvg");

    // =========================================================================
    // Create TimeDurationMovingAverage as a submodule
    // This allows: from py_moving_average import TimeDurationMovingAverage
    //             avg = TimeDurationMovingAverage.Integer(50.0, 100ms)
    // =========================================================================
    
    py::module_ timeDurationAvgModule = py::module_::create_submodule(
        m, "TimeDurationMovingAverage", "Time-based moving average with type-specific implementations");
    
    bind_TimeDurationMovingAverage<int, MEDIUM_BUFFER>(timeDurationAvgModule, "IntegerMovingAvg");
    bind_TimeDurationMovingAverage<double, MEDIUM_BUFFER>(timeDurationAvgModule, "DoubleMovingAvg");
    bind_TimeDurationMovingAverage<float, MEDIUM_BUFFER>(timeDurationAvgModule, "FloatMovingAvg");

    // =========================================================================
    // Also expose the types directly in the main module for convenience
    // This allows both:
    //   FixedMovingAverage.Integer(...)   AND   IntegerAverage(...)
    // =========================================================================
    
    // Direct type bindings in main module
    // bind_FixedMovingAverage<int, MEDIUM_BUFFER>(m, "IntegerAverage");
    // bind_FixedMovingAverage<double, MEDIUM_BUFFER>(m, "FixedMovingAverage");
    // bind_FixedMovingAverage<float, MEDIUM_BUFFER>(m, "FixedMovingAverageFloat");
    
    // bind_TimeDurationMovingAverage<int, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageInt");
    // bind_TimeDurationMovingAverage<double, MEDIUM_BUFFER>(m, "TimeDurationMovingAverage");
    // bind_TimeDurationMovingAverage<float, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageFloat");
}
