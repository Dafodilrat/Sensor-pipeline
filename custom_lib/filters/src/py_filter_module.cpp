// =============================================================================
// Main module definition for py_filter - Python bindings for filter library
// =============================================================================

#include "filter_bindings.cpp"

PYBIND11_MODULE(py_filter, m) {
    m.doc() = "Python bindings for Filter Library - Includes FixedPoint and Float Low-Pass Filters";

    // FixedPointLowPassFilter classes
    bind_FixedPointLowPassFilter_24_8(m, "FixedPointLowPassFilter_24_8");
    bind_FixedPointLowPassFilter_16_16(m, "FixedPointLowPassFilter_16_16");
    bind_FixedPointLowPassFilter_8_24(m, "FixedPointLowPassFilter_8_24");
    bind_FixedPointLowPassFilter_2_30(m, "FixedPointLowPassFilter_2_30");
    
    // FloatLowPassFilter classes
    bind_FloatLowPassFilter<double>(m, "FloatLowPassFilter_Double");
    bind_FloatLowPassFilter<float>(m, "FloatLowPassFilter_Float");
}
