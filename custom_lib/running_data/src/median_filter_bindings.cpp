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
        .def(py::init<size_t, float>(),
             py::arg("window_size") = MaxWindowSize,
             py::arg("timeout_seconds") = -1.0f,
             "Create a median filter with specified window size and optional timeout (<= 0 = disabled)")
        .def("update", &MedianFilter<T, MaxWindowSize>::update,
             py::arg("new_value"),
             "Add a new value and return the current median")
        .def("reset", &MedianFilter<T, MaxWindowSize>::reset,
             "Reset the filter state")
        .def("set_window_size", &MedianFilter<T, MaxWindowSize>::setWindowSize,
             py::arg("window_size"),
             "Set the window size at runtime")
        .def("set_timeout", &MedianFilter<T, MaxWindowSize>::set_timeout,
             py::arg("timeout_seconds"),
             "Set timeout in seconds. Use <= 0 to disable timeout")
        .def("get_timeout", &MedianFilter<T, MaxWindowSize>::get_timeout,
             "Get current timeout value in seconds. Returns <= 0 if disabled")
        .def_property_readonly("has_timeout", &MedianFilter<T, MaxWindowSize>::has_timeout)
        .def_property_readonly("timeout_occurred", &MedianFilter<T, MaxWindowSize>::timeout_occurred)
        .def_property_readonly("window_size", &MedianFilter<T, MaxWindowSize>::windowSize)
        .def_property_readonly("current_size", &MedianFilter<T, MaxWindowSize>::currentSize)
        .def_property_readonly("max_window_size", &MedianFilter<T, MaxWindowSize>::maxWindowSize)
        .def_property_readonly("is_full", &MedianFilter<T, MaxWindowSize>::isFull);
}
