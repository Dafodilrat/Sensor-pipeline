#pragma once

// =============================================================================
// Main low-pass filter header file
// Includes all low-pass filter implementations
// =============================================================================

#include "base_filter.hpp"
#include "base_iir_filter.hpp"
#include "float_low_pass_filter.hpp"
#include "fixed_point_low_pass_filter.hpp"

// =============================================================================
// Note: This file exists for backward compatibility.
// All filter classes are now split into separate files:
//   - base_filter.hpp: BaseFilter base class
//   - base_iir_filter.hpp: BaseIIRFilter base class
//   - float_low_pass_filter.hpp: FloatLowPassFilter for floating-point types
//   - fixed_point_low_pass_filter.hpp: FixedPointLowPassFilter for integer types
// =============================================================================
