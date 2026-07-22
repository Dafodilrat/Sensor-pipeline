#include "py_moving_average_bindings.cpp"

// =============================================================================
// Main module definition
// =============================================================================

PYBIND11_MODULE(py_moving_average, m) {
    m.doc() = "Python bindings for Moving Average and Low-Pass Filter Library";

    // Define common buffer sizes
    constexpr size_t MEDIUM_BUFFER = 1000;

    // =========================================================================
    // FixedMovingAverage bindings
    // =========================================================================
    bind_FixedMovingAverage<int, MEDIUM_BUFFER>(m, "FixedMovingAverage_Int");
    bind_FixedMovingAverage<double, MEDIUM_BUFFER>(m, "FixedMovingAverage_Double");
    bind_FixedMovingAverage<float, MEDIUM_BUFFER>(m, "FixedMovingAverage_Float");

    // =========================================================================
    // TimeDurationMovingAverage bindings
    // =========================================================================
    bind_TimeDurationMovingAverage<int, MEDIUM_BUFFER>(m, "TimeDurationMovingAverage_Int");
    bind_TimeDurationMovingAverage<double, MEDIUM_BUFFER>(m, "TimeDurationMovingAverage_Double");
    bind_TimeDurationMovingAverage<float, MEDIUM_BUFFER>(m, "TimeDurationMovingAverage_Float");

    // =========================================================================
    // LowPassFilter bindings
    // =========================================================================
    bind_FloatLowPassFilter<double>(m, "FloatLowPassFilter_Double");
    bind_FloatLowPassFilter<float>(m, "FloatLowPassFilter_Float");
    bind_FixedPointLowPassFilter32(m, "FixedPointLowPassFilter_Integer");
}