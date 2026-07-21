#include <pybind11/pybind11.h>
#include <pybind11/chrono.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

// Include our moving average library header
#include "mavg.hpp"

namespace py = pybind11;

// =============================================================================
// Python Bindings for FixedMovingAverage
// =============================================================================

template<typename T, size_t MaxSamples>
void bind_FixedMovingAverage(py::module& m, const char* className) {
    py::class_<FixedMovingAverage<T, MaxSamples>>(m, className)
        .def(py::init<size_t>(), 
             py::arg("sample_count") = MaxSamples)
        .def("update", &FixedMovingAverage<T, MaxSamples>::update,
             py::arg("new_value"))
        .def("reset", &FixedMovingAverage<T, MaxSamples>::reset)
        .def("current_size", &FixedMovingAverage<T, MaxSamples>::currentSize)
        .def("capacity", &FixedMovingAverage<T, MaxSamples>::capacity)
        .def_property_readonly("size", &FixedMovingAverage<T, MaxSamples>::currentSize)
        .def_property_readonly("max_size", &FixedMovingAverage<T, MaxSamples>::capacity);
}

// =============================================================================
// Python Bindings for TimeDurationMovingAverage
// =============================================================================

template<typename T, size_t MaxSamples>
void bind_TimeDurationMovingAverage(py::module& m, const char* className) {
    using Class = TimeDurationMovingAverage<T, MaxSamples>;
    
    py::class_<Class>(m, className)
        .def(py::init<double, std::chrono::milliseconds>(),
             py::arg("sensor_hz"), 
             py::arg("window_duration"))
        .def("update", &Class::update,
             py::arg("new_value"))
        .def("reset", &Class::reset)
        .def("set_parameters", &Class::setParameters,
             py::arg("sensor_hz"),
             py::arg("window_duration"))
        .def("set_sensor_hz", &Class::setSensorHz,
             py::arg("sensor_hz"))
        .def("set_window_duration", &Class::setWindowDuration,
             py::arg("window_duration"))
        .def("current_size", &Class::currentSize)
        .def("get_window_duration", &Class::getWindowDuration)
        .def("get_sensor_hz", &Class::getSensorHz)
        .def("get_calculated_window_size", &Class::getCalculatedWindowSize)
        .def_property_readonly("size", &Class::currentSize)
        .def_property_readonly("window_duration", &Class::getWindowDuration)
        .def_property_readonly("sensor_hz", &Class::getSensorHz)
        .def_property_readonly("calculated_window_size", &Class::getCalculatedWindowSize)
        .def_property_readonly("max_size", &Class::capacity);
}

// =============================================================================
// Main module definition
// =============================================================================

PYBIND11_MODULE(py_moving_average, m) {
    m.doc() = "Python bindings for Moving Average Library";

    // Define common buffer sizes
    constexpr size_t MEDIUM_BUFFER = 1000;

    // =========================================================================
    // Main classes (using medium buffer as default)
    // =========================================================================
    bind_FixedMovingAverage<double, MEDIUM_BUFFER>(m, "FixedMovingAverageDouble");
    bind_FixedMovingAverage<float, MEDIUM_BUFFER>(m, "FixedMovingAverageFloat");
    bind_TimeDurationMovingAverage<double, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageDouble");
    bind_TimeDurationMovingAverage<float, MEDIUM_BUFFER>(m, "TimeDurationMovingAverageFloat");
}
