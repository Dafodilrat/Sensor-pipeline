// =============================================================================
// Median Filter Module - Demonstrates extensibility
// This file can be added to the library without modifying any existing files
// =============================================================================

#include <pybind11/pybind11.h>
#include "../lib/median_filter.hpp"
#include "median_filter_bindings.cpp"

namespace py = pybind11;

// Buffer size constants
constexpr size_t SMALL_BUFFER = 101;
constexpr size_t MEDIUM_BUFFER = 501;
constexpr size_t LARGE_BUFFER = 1001;

// Explicit instantiations for different types and max window sizes
void bind_MedianFilterIntSmall(py::module& m) {
    bind_MedianFilter<int, SMALL_BUFFER>(m, "Integer");
}

void bind_MedianFilterIntMedium(py::module& m) {
    bind_MedianFilter<int, MEDIUM_BUFFER>(m, "Integer");
}

void bind_MedianFilterIntLarge(py::module& m) {
    bind_MedianFilter<int, LARGE_BUFFER>(m, "Integer");
}

void bind_MedianFilterFloatSmall(py::module& m) {
    bind_MedianFilter<float, SMALL_BUFFER>(m, "Float");
}

void bind_MedianFilterFloatMedium(py::module& m) {
    bind_MedianFilter<float, MEDIUM_BUFFER>(m, "Float");
}

void bind_MedianFilterFloatLarge(py::module& m) {
    bind_MedianFilter<float, LARGE_BUFFER>(m, "Float");
}

void bind_MedianFilterDoubleSmall(py::module& m) {
    bind_MedianFilter<double, SMALL_BUFFER>(m, "Double");
}

void bind_MedianFilterDoubleMedium(py::module& m) {
    bind_MedianFilter<double, MEDIUM_BUFFER>(m, "Double");
}

void bind_MedianFilterDoubleLarge(py::module& m) {
    bind_MedianFilter<double, LARGE_BUFFER>(m, "Double");
}

PYBIND11_MODULE(py_median_filter, m) {
    m.doc() = "Python bindings for Median Filter - Demonstrates library extensibility";

    // =========================================================================
    // MedianFilter hierarchy with nested submodules
    // =========================================================================
    auto median_filter = m.def_submodule("MedianFilter", "Median filter with position tracking");
    
    auto smallbuffer = median_filter.def_submodule("smallbuffer", "Small buffer (" + std::to_string(SMALL_BUFFER) + ") variants");
    bind_MedianFilterIntSmall(smallbuffer);
    bind_MedianFilterFloatSmall(smallbuffer);
    bind_MedianFilterDoubleSmall(smallbuffer);
    
    auto mediumbuffer = median_filter.def_submodule("mediumbuffer", "Medium buffer (" + std::to_string(MEDIUM_BUFFER) + ") variants");
    bind_MedianFilterIntMedium(mediumbuffer);
    bind_MedianFilterFloatMedium(mediumbuffer);
    bind_MedianFilterDoubleMedium(mediumbuffer);
    
    auto largebuffer = median_filter.def_submodule("largebuffer", "Large buffer (" + std::to_string(LARGE_BUFFER) + ") variants");
    bind_MedianFilterIntLarge(largebuffer);
    bind_MedianFilterFloatLarge(largebuffer);
    bind_MedianFilterDoubleLarge(largebuffer);
}
