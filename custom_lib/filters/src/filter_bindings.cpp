#include <pybind11/pybind11.h>
#include <pybind11/chrono.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

// Include the filter headers
#include "../lib/fixed_point_low_pass_filter.hpp"
#include "../lib/float_low_pass_filter.hpp"

namespace py = pybind11;

// =============================================================================
// Python Bindings for FixedPointLowPassFilter
// =============================================================================

// Template binding for FixedPointLowPassFilter with configurable precision
template<typename T, typename CalcT, int FractionalBits>
void bind_FixedPointLowPassFilter_template(py::module& m, const char* className) {
    using Class = FixedPointLowPassFilter<T, CalcT, FractionalBits>;
    
    py::class_<Class>(m, className)
        .def(py::init<double, int, double>(),
             py::arg("cutoff_freq_hz"),
             py::arg("fractional_bits") = FractionalBits,
             py::arg("timeout_seconds") = 10.0)
        .def("update", static_cast<T(Class::*)(T)>(&Class::update),
             py::arg("new_value"))
        .def("update_with_timestamp", 
             static_cast<T(Class::*)(T, std::chrono::steady_clock::time_point, bool*)>(&Class::update),
             py::arg("new_value"),
             py::arg("timestamp"),
             py::arg("is_clamped") = nullptr)
        .def("reset", &Class::reset)
        .def("set_cutoff_frequency", &Class::set_cutoff_frequency,
             py::arg("cutoff_freq_hz"))
        .def("get_cutoff_frequency", &Class::get_cutoff_frequency)
        .def("set_timeout", &Class::set_timeout,
             py::arg("timeout_seconds"))
        .def("get_timeout", &Class::get_timeout)
        .def("get_current_output_double", &Class::get_current_output_double)
        .def("get_fractional_bits", &Class::get_fractional_bits)
        .def("get_q_scale", &Class::get_q_scale)
        .def_property_readonly("cutoff_frequency", &Class::get_cutoff_frequency)
        .def_property_readonly("timeout", &Class::get_timeout)
        .def_property_readonly("fractional_bits", &Class::get_fractional_bits)
        .def_property_readonly("q_scale", &Class::get_q_scale);
}

// Binding for FixedPointLowPassFilter_16_16 (Q16.16)
void bind_FixedPointLowPassFilter_16_16(py::module& m, const char* className) {
    bind_FixedPointLowPassFilter_template<int32_t, int64_t, 16>(m, className);
}

// Binding for FixedPointLowPassFilter_24_8 (Q24.8)
void bind_FixedPointLowPassFilter_24_8(py::module& m, const char* className) {
    bind_FixedPointLowPassFilter_template<int32_t, int64_t, 8>(m, className);
}

// Binding for FixedPointLowPassFilter_8_24 (Q8.24)
void bind_FixedPointLowPassFilter_8_24(py::module& m, const char* className) {
    bind_FixedPointLowPassFilter_template<int32_t, int64_t, 24>(m, className);
}

// Binding for FixedPointLowPassFilter_2_30 (Q2.30)
void bind_FixedPointLowPassFilter_2_30(py::module& m, const char* className) {
    bind_FixedPointLowPassFilter_template<int32_t, int64_t, 30>(m, className);
}

// =============================================================================
// Python Bindings for FloatLowPassFilter
// =============================================================================

template<typename T>
void bind_FloatLowPassFilter(py::module& m, const char* className) {
    using Class = FloatLowPassFilter<T, 1000>;
    
    py::class_<Class>(m, className)
        .def(py::init<double, double>(),
             py::arg("cutoff_freq_hz"),
             py::arg("timeout_seconds") = 10.0)
        .def("update", static_cast<T(Class::*)(T)>(&Class::update),
             py::arg("new_value"))
        .def("update_with_timestamp",
             static_cast<T(Class::*)(T, std::chrono::steady_clock::time_point)>(&Class::update),
             py::arg("new_value"),
             py::arg("timestamp"))
        .def("reset", &Class::reset)
        .def("set_cutoff_frequency", &Class::set_cutoff_frequency,
             py::arg("cutoff_freq_hz"))
        .def("get_cutoff_frequency", &Class::get_cutoff_frequency)
        .def("set_timeout", &Class::set_timeout,
             py::arg("timeout_seconds"))
        .def("get_timeout", &Class::get_timeout)
        .def("get_current_output", &Class::get_current_output)
        .def_property_readonly("cutoff_frequency", &Class::get_cutoff_frequency)
        .def_property_readonly("timeout", &Class::get_timeout);
}
