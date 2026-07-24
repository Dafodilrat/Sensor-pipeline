#include <pybind11/pybind11.h>

// Include the filter header
#include "../lib/median_filter.hpp"

namespace py = pybind11;

// =============================================================================
// Python Bindings for MedianFilter
// =============================================================================

// Template binding for MedianFilter with MaxWindowSize template parameter
// and runtime window_size construction
template<typename T, size_t MaxWindowSize>
void bind_MedianFilter(py::module& m, const char* className) {
    py::class_<MedianFilter<T, MaxWindowSize>>(m, className)
        .def(py::init<size_t>(),
             py::arg("window_size") = MaxWindowSize,
             "Create a median filter with specified window size (max " + std::to_string(MaxWindowSize) + ")")
        .def("update", &MedianFilter<T, MaxWindowSize>::update,
             py::arg("new_value"),
             "Add a new value and return the current median")
        .def("reset", &MedianFilter<T, MaxWindowSize>::reset,
             "Reset the filter state")
        .def("set_window_size", &MedianFilter<T, MaxWindowSize>::setWindowSize,
             py::arg("window_size"),
             "Set the window size at runtime")
        .def_property_readonly("window_size", &MedianFilter<T, MaxWindowSize>::windowSize)
        .def_property_readonly("current_size", &MedianFilter<T, MaxWindowSize>::currentSize)
        .def_property_readonly("max_window_size", &MedianFilter<T, MaxWindowSize>::maxWindowSize)
        .def_property_readonly("is_full", &MedianFilter<T, MaxWindowSize>::isFull);
}
