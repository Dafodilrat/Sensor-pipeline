// =============================================================================
// Python bindings for py_filter module
// Exposes all filter classes with naming: FilterFloat, FilterFixed_*
// =============================================================================

#include <pybind11/pybind11.h>
#include <pybind11/chrono.h>
#include <pybind11/stl.h>

// Include the filter headers
#include "../lib/low_pass_iir_filter.hpp"
#include "../lib/fixed_point_low_pass_filter.hpp"

namespace py = pybind11;

// =============================================================================
// Bindings for LowPassIIRFilter (floating-point versions)
// =============================================================================

template<typename T>
void bind_LowPassFilter(py::module& m, const char* className) {
    using Class = LowPassIIRFilter<T>;
    
    py::class_<Class>(m, className)
        .def(py::init<T, float>(),
             py::arg("cutoff_freq"),
             py::arg("timeout_seconds") = -1.0f)
        .def("update", &Class::update,
             py::arg("new_value"))
        .def("reset", &Class::reset)
        .def("set_cutoff", &Class::set_cutoff,
             py::arg("cutoff_freq"))
        .def("get_cutoff", &Class::get_cutoff)
        .def("set_timeout", &Class::set_timeout,
             py::arg("timeout_seconds"))
        .def("get_timeout", &Class::get_timeout)
        .def("get_last_dt", &Class::get_last_dt)
        .def("get_alpha", &Class::get_alpha)
        .def("has_timeout", &Class::has_timeout)
        .def_property_readonly("cutoff", &Class::get_cutoff)
        .def_property_readonly("timeout", &Class::get_timeout);
}

// =============================================================================
// Bindings for FixedPointLowPassFilter
// =============================================================================

template<typename T, typename CalcT, int FractionalBits>
void bind_FixedPointFilter(py::module& m, const char* className) {
    using Class = FixedPointLowPassFilter<T, CalcT, FractionalBits>;
    
    py::class_<Class>(m, className)
        .def(py::init<std::int32_t, unsigned int, std::int64_t>(),
             py::arg("cutoff_freq_times_100"),
             py::arg("fractional_bits") = FractionalBits,
             py::arg("timeout_ns") = 0)
        .def("update", &Class::update,
             py::arg("new_value"))
        .def("reset", &Class::reset)
        .def("had_clamp", &Class::had_clamp)
        .def("get_fractional_bits", &Class::get_fractional_bits)
        .def("get_q_scale", &Class::get_q_scale)
        .def("get_rc_raw", &Class::get_rc_raw)
        .def("get_current_output_double", &Class::get_current_output_double)
        .def("enable_verbose_warnings", &Class::enable_verbose_warnings,
             py::arg("enable") = true)
        .def("is_near_saturation", &Class::is_near_saturation,
             py::arg("threshold") = 0.10)
        .def("get_max_value", &Class::get_max_value)
        .def("get_min_value", &Class::get_min_value)
        .def("set_cutoff", &Class::set_cutoff,
             py::arg("cutoff_freq_times_100"))
        .def("set_timeout", &Class::set_timeout,
             py::arg("timeout_ns"))
        .def("get_timeout", &Class::get_timeout)
        .def("has_timeout", &Class::has_timeout)
        .def_property_readonly("fractional_bits", &Class::get_fractional_bits)
        .def_property_readonly("q_scale", &Class::get_q_scale)
        .def_property_readonly("timeout", &Class::get_timeout);
}

// =============================================================================
// Module initialization
// =============================================================================

PYBIND11_MODULE(py_filter, m) {
    m.doc() = "Python bindings for Filter Library - Low-pass IIR filters";

    // Floating-point filters
    bind_LowPassFilter<float>(m, "LowPassIIRFilter_Float");
    
    // Fixed-point filters
    bind_FixedPointFilter<int32_t, int64_t, 8>(m, "FixedPointLowPassFilter_24_8");
    bind_FixedPointFilter<int32_t, int64_t, 16>(m, "FixedPointLowPassFilter_16_16");
}
