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

    // =========================================================================
    // FixedMovingAverage hierarchy
    // =========================================================================
    auto fixed_ma = m.def_submodule("FixedMovingAverage", "Fixed size moving average filters");
    
    auto smallbuffer = fixed_ma.def_submodule("smallbuffer", "Small buffer (100) variants");
    bind_FixedMovingAverage<int, SMALL_BUFFER>(smallbuffer, "Integer");
    bind_FixedMovingAverage<double, SMALL_BUFFER>(smallbuffer, "Double");
    bind_FixedMovingAverage<float, SMALL_BUFFER>(smallbuffer, "Float");
    
    auto mediumbuffer = fixed_ma.def_submodule("mediumbuffer", "Medium buffer (1000) variants");
    bind_FixedMovingAverage<int, MEDIUM_BUFFER>(mediumbuffer, "Integer");
    bind_FixedMovingAverage<double, MEDIUM_BUFFER>(mediumbuffer, "Double");
    bind_FixedMovingAverage<float, MEDIUM_BUFFER>(mediumbuffer, "Float");
    
    auto largebuffer = fixed_ma.def_submodule("largebuffer", "Large buffer (10000) variants");
    bind_FixedMovingAverage<int, LARGE_BUFFER>(largebuffer, "Integer");
    bind_FixedMovingAverage<double, LARGE_BUFFER>(largebuffer, "Double");
    bind_FixedMovingAverage<float, LARGE_BUFFER>(largebuffer, "Float");

    // =========================================================================
    // TimeDurationMovingAverage hierarchy
    // =========================================================================
    auto time_duration_ma = m.def_submodule("TimeDurationMovingAverage", "Time duration based moving average filters");
    
    auto td_smallbuffer = time_duration_ma.def_submodule("smallbuffer", "Small buffer (100) variants");
    bind_TimeDurationMovingAverage<int, SMALL_BUFFER>(td_smallbuffer, "Integer");
    bind_TimeDurationMovingAverage<double, SMALL_BUFFER>(td_smallbuffer, "Double");
    bind_TimeDurationMovingAverage<float, SMALL_BUFFER>(td_smallbuffer, "Float");
    
    auto td_mediumbuffer = time_duration_ma.def_submodule("mediumbuffer", "Medium buffer (1000) variants");
    bind_TimeDurationMovingAverage<int, MEDIUM_BUFFER>(td_mediumbuffer, "Integer");
    bind_TimeDurationMovingAverage<double, MEDIUM_BUFFER>(td_mediumbuffer, "Double");
    bind_TimeDurationMovingAverage<float, MEDIUM_BUFFER>(td_mediumbuffer, "Float");
    
    auto td_largebuffer = time_duration_ma.def_submodule("largebuffer", "Large buffer (10000) variants");
    bind_TimeDurationMovingAverage<int, LARGE_BUFFER>(td_largebuffer, "Integer");
    bind_TimeDurationMovingAverage<double, LARGE_BUFFER>(td_largebuffer, "Double");
    bind_TimeDurationMovingAverage<float, LARGE_BUFFER>(td_largebuffer, "Float");

}