#pragma once

#include "base_filter.hpp"

// =============================================================================
// BaseIIRFilter: Base class for IIR (Infinite Impulse Response) filters
// Provides common IIR functionality: previous output, update template method
// =============================================================================

template<typename T>
class BaseIIRFilter : public BaseFilter<T> {
protected:
    T previous_output_;
    
    // Apply IIR filter formula: output = alpha * input + (1 - alpha) * previous_output
    T apply_iir_filter(T new_value, double alpha) {
        return static_cast<T>(alpha * new_value + (1.0 - alpha) * this->previous_output_);
    }

public:
    explicit BaseIIRFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : BaseFilter<T>(cutoff_freq_hz, timeout_seconds),
          previous_output_(T(0)) {}
    
    ~BaseIIRFilter() override = default;
    
    // Reset filter state
    void reset() override {
        this->previous_output_ = T(0);
        // Reset first call flag by accessing the protected member
        this->first_call_ = true;
    }
    
    // Get current output (latest filtered value)
    virtual T get_current_output() const {
        return previous_output_;
    }
};
