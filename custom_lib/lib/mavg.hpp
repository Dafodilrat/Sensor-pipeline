#pragma once

// Main moving average library header
// This file provides backward compatibility by including all moving average classes
// For new code, prefer including the specific headers you need

#include "fixed_moving_average.hpp"
#include "time_duration_moving_average.hpp"
#include "ring_buffer.hpp"

// Factory namespace for convenience
namespace MovingAverageFactory {
    
    template<typename T, size_t MaxSamples>
    FixedMovingAverage<T, MaxSamples> createFixedAverage(size_t sample_count = MaxSamples) {
        return FixedMovingAverage<T, MaxSamples>(sample_count);
    }

    template<typename T, size_t MaxSamples>
    TimeDurationMovingAverage<T, MaxSamples> createTimeDurationAverage(
        double sensor_hz, 
        std::chrono::milliseconds duration
    ) {
        return TimeDurationMovingAverage<T, MaxSamples>(sensor_hz, duration);
    }
}
