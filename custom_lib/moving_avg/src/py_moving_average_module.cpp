#include "py_moving_average_bindings.cpp"

// =============================================================================
// Main module definition
// =============================================================================

PYBIND11_MODULE(py_moving_average, m) {
    m.doc() = "Python bindings for Moving Average and Low-Pass Filter Library";

    // Define common buffer sizes
    constexpr size_t SMALL_BUFFER = 100;
    constexpr size_t MEDIUM_BUFFER = 1000;
    constexpr size_t LARGE_BUFFER = 10000;

    // FixedMovingAverage classes
    bind_FixedMovingAverage<int, SMALL_BUFFER>(m, "FixedMovingAverageInteger_Small");
    bind_FixedMovingAverage<double, SMALL_BUFFER>(m, "FixedMovingAverageDouble_Small");
    bind_FixedMovingAverage<float, SMALL_BUFFER>(m, "FixedMovingAverageFloat_Small");
    
    bind_FixedMovingAverage<int, MEDIUM_BUFFER>(m, "FixedMovingAverageInteger");
    bind_FixedMovingAverage<double, MEDIUM_BUFFER>(m, "FixedMovingAverageDouble");
    bind_FixedMovingAverage<float, MEDIUM_BUFFER>(m, "FixedMovingAverageFloat");
    
    bind_FixedMovingAverage<int, LARGE_BUFFER>(m, "FixedMovingAverageInteger_Large");
    bind_FixedMovingAverage<double, LARGE_BUFFER>(m, "FixedMovingAverageDouble_Large");
    bind_FixedMovingAverage<float, LARGE_BUFFER>(m, "FixedMovingAverageFloat_Large");

    // TimeDurationMovingAverage classes
    bind_TimeDurationMovingAverage<int, SMALL_BUFFER>(m, "TimeDurationMovingAverageInteger_Small");
    bind_TimeDurationMovingAverage<double, SMALL_BUFFER>(m, "TimeDurationMovingAverageDouble_Small");
    bind_TimeDurationMovingAverage<float, SMALL_BUFFER>(m, "TimeDurationMovingAverageFloat_Small");
    
    bind_TimeDurationMovingAverage<int, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageInteger");
    bind_TimeDurationMovingAverage<double, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageDouble");
    bind_TimeDurationMovingAverage<float, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageFloat");
    
    bind_TimeDurationMovingAverage<int, LARGE_BUFFER>(m, "TimeDurationMovingAverageInteger_Large");
    bind_TimeDurationMovingAverage<double, LARGE_BUFFER>(m, "TimeDurationMovingAverageDouble_Large");
    bind_TimeDurationMovingAverage<float, LARGE_BUFFER>(m, "TimeDurationMovingAverageFloat_Large");

}