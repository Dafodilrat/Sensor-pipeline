#pragma once

// Compatibility header for migrating from custom QValue to fpm library
// This provides backward-compatible types and functions

#include "../../external/fpm/include/fpm/fixed.hpp"
#include <cstddef>
#include <cstdint>
#include <limits>
#include <algorithm>
#include <type_traits>

namespace qformat {

// =============================================================================
// Type utilities - same as before
// =============================================================================

template<typename T>
struct CalcTypeHelper {
    using type = T;
};

template<> struct CalcTypeHelper<int32_t> { using type = int64_t; };
template<> struct CalcTypeHelper<int16_t> { using type = int32_t; };
template<> struct CalcTypeHelper<int8_t>  { using type = int16_t; };
template<> struct CalcTypeHelper<uint32_t> { using type = uint64_t; };
template<> struct CalcTypeHelper<uint16_t> { using type = uint32_t; };
template<> struct CalcTypeHelper<uint8_t>  { using type = uint16_t; };

// Specialization for int64_t - use __int128 if available, otherwise same type
#if defined(__SIZEOF_INT128__)
template<> struct CalcTypeHelper<int64_t> { using type = __int128_t; };
template<> struct CalcTypeHelper<uint64_t> { using type = unsigned __int128_t; };
#else
// When __int128 is not available, we'll have to use the same type for Q32_32
// This is a limitation that requires special handling
template<> struct CalcTypeHelper<int64_t> { using type = int64_t; };
template<> struct CalcTypeHelper<uint64_t> { using type = uint64_t; };
#endif

template<typename T>
using DefaultCalcT = typename CalcTypeHelper<T>::type;

// =============================================================================
// Type trait for detecting QValue types (now aliases to fpm::fixed)
// =============================================================================

template<typename T>
struct is_qvalue : std::false_type {};

// Specialization for fpm::fixed types to maintain the is_qvalue trait
template<typename BaseType, typename IntermediateType, unsigned int FractionBits, bool EnableRounding>
struct is_qvalue<fpm::fixed<BaseType, IntermediateType, FractionBits, EnableRounding>> : std::true_type {};

// =============================================================================
// Default fractional bits based on type size
// =============================================================================

template<typename T>
struct DefaultFractionalBits {
    static constexpr int value = (sizeof(T) == 4 ? 16 : (sizeof(T) == 8 ? 32 : 8));
};

// =============================================================================
// QValue: Now an alias to fpm::fixed with additional compatibility methods
// =============================================================================

template<typename T, typename CalcT = DefaultCalcT<T>, int FractionalBits = DefaultFractionalBits<T>::value>
class QValue {
private:
    fpm::fixed<T, CalcT, FractionalBits> value_;
    
    // Saturating operations helpers
    static T sat_add_impl(T a, T b) {
        CalcT result = static_cast<CalcT>(a) + static_cast<CalcT>(b);
        if (result > std::numeric_limits<T>::max()) {
            return std::numeric_limits<T>::max();
        }
        if (result < std::numeric_limits<T>::min()) {
            return std::numeric_limits<T>::min();
        }
        return static_cast<T>(result);
    }
    
    static T sat_sub_impl(T a, T b) {
        CalcT result = static_cast<CalcT>(a) - static_cast<CalcT>(b);
        if (result > std::numeric_limits<T>::max()) {
            return std::numeric_limits<T>::max();
        }
        if (result < std::numeric_limits<T>::min()) {
            return std::numeric_limits<T>::min();
        }
        return static_cast<T>(result);
    }
    
    static T sat_mul_impl(T a, T b) {
        CalcT result = static_cast<CalcT>(a) * static_cast<CalcT>(b);
        if (result > std::numeric_limits<T>::max()) {
            return std::numeric_limits<T>::max();
        }
        if (result < std::numeric_limits<T>::min()) {
            return std::numeric_limits<T>::min();
        }
        return static_cast<T>(result);
    }
    
    static T sat_mul_q_impl(T a, T b) {
        CalcT result = static_cast<CalcT>(a) * static_cast<CalcT>(b);
        result >>= FractionalBits;
        if (result > std::numeric_limits<T>::max()) {
            return std::numeric_limits<T>::max();
        }
        if (result < std::numeric_limits<T>::min()) {
            return std::numeric_limits<T>::min();
        }
        return static_cast<T>(result);
    }

public:
    // Default constructor
    QValue() : value_(fpm::fixed<T, CalcT, FractionalBits>()) {}

    // Construct from a double value with optional clamping detection
    explicit QValue(double value, bool* is_clamped = nullptr) {
        fpm::fixed<T, CalcT, FractionalBits> temp(value);
        T raw_val = temp.raw_value();
        
        // Check for overflow by trying to construct from raw
        fpm::fixed<T, CalcT, FractionalBits> test = fpm::fixed<T, CalcT, FractionalBits>::from_raw_value(raw_val);
        if (static_cast<double>(test) != value && (value > 0 && raw_val == std::numeric_limits<T>::max()) || 
            (value < 0 && raw_val == std::numeric_limits<T>::min())) {
            if (is_clamped) *is_clamped = true;
            value_ = fpm::fixed<T, CalcT, FractionalBits>::from_raw_value(
                value > 0 ? std::numeric_limits<T>::max() : std::numeric_limits<T>::min());
        } else {
            if (is_clamped) *is_clamped = false;
            value_ = temp;
        }
    }

    // Construct from raw Q-format value
    explicit QValue(T raw_value) 
        : value_(fpm::fixed<T, CalcT, FractionalBits>::from_raw_value(raw_value)) {}

    // Construct from fpm::fixed directly
    explicit QValue(fpm::fixed<T, CalcT, FractionalBits> fpm_value) : value_(fpm_value) {}

    // Get the raw Q-format value
    T raw() const { 
        return value_.raw_value(); 
    }

    // Get as double
    double to_double() const {
        return static_cast<double>(value_);
    }

    // Get the Q scale
    static constexpr T q_scale() { 
        return static_cast<T>(T(1) << FractionalBits); 
    }

    // Get fractional bits
    static constexpr int fractional_bits() { 
        return FractionalBits; 
    }

    // Get the underlying fpm::fixed value
    fpm::fixed<T, CalcT, FractionalBits> get_fpm() const { 
        return value_; 
    }

    // =========================================================================
    // Operator overloading for arithmetic
    // =========================================================================

    QValue operator+(const QValue& other) const {
        return QValue(value_ + other.value_);
    }

    QValue operator-(const QValue& other) const {
        return QValue(value_ - other.value_);
    }

    QValue operator*(const QValue& other) const {
        return QValue(value_ * other.value_);
    }

    QValue& operator+=(const QValue& other) {
        value_ += other.value_;
        return *this;
    }

    QValue& operator-=(const QValue& other) {
        value_ -= other.value_;
        return *this;
    }

    QValue& operator*=(const QValue& other) {
        value_ *= other.value_;
        return *this;
    }

    QValue operator-() const {
        return QValue(-value_);
    }

    // =========================================================================
    // Mixed operations: QValue op T
    // =========================================================================

    QValue operator+(T other) const {
        return QValue(value_ + other);
    }

    QValue operator-(T other) const {
        return QValue(value_ - other);
    }

    QValue operator*(T other) const {
        // For direct multiplication with raw T, we need to use saturating non-Q multiplication
        // This matches the original behavior where T is treated as raw Q-format value
        T result = sat_mul_impl(raw(), other);
        return QValue(result);
    }

    QValue& operator+=(T other) {
        value_ += other;
        return *this;
    }

    QValue& operator-=(T other) {
        value_ -= other;
        return *this;
    }

    QValue& operator*=(T other) {
        // Same as operator* - treat T as raw
        T result = sat_mul_impl(raw(), other);
        value_ = fpm::fixed<T, CalcT, FractionalBits>::from_raw_value(result);
        return *this;
    }

    // =========================================================================
    // Friend functions for T op QValue
    // =========================================================================

    template<typename U>
    friend QValue operator+(U lhs, const QValue& rhs) {
        return QValue(static_cast<T>(lhs)) + rhs;
    }

    template<typename U>
    friend QValue operator-(U lhs, const QValue& rhs) {
        return QValue(static_cast<T>(lhs)) - rhs;
    }

    template<typename U>
    friend QValue operator*(U lhs, const QValue& rhs) {
        return QValue(static_cast<T>(lhs)) * rhs;
    }

    // =========================================================================
    // Comparison operators
    // =========================================================================

    bool operator==(const QValue& other) const { return value_ == other.value_; }
    bool operator!=(const QValue& other) const { return value_ != other.value_; }
    bool operator<(const QValue& other) const { return value_ < other.value_; }
    bool operator>(const QValue& other) const { return value_ > other.value_; }
    bool operator<=(const QValue& other) const { return value_ <= other.value_; }
    bool operator>=(const QValue& other) const { return value_ >= other.value_; }
};

// =============================================================================
// Convenience type aliases - same as before
// =============================================================================

using Q16_16 = QValue<int32_t, int64_t, 16>;

// For Q32_32, use the default CalcT which will be __int128_t on systems that support it
using Q32_32 = QValue<int64_t, DefaultCalcT<int64_t>, 32>;

using Q0_32 = QValue<int32_t, int64_t, 32>;

// Additional aliases for fpm types
using FPM_Q16_16 = fpm::fixed_16_16;
using FPM_Q24_8 = fpm::fixed_24_8;
using FPM_Q8_24 = fpm::fixed_8_24;

// =============================================================================
// Free functions for Q-value operations
// =============================================================================

// Create a Q-value from double
template<typename T, typename CalcT, int FB>
QValue<T, CalcT, FB> make_qvalue(double value, bool* is_clamped = nullptr) {
    return QValue<T, CalcT, FB>(value, is_clamped);
}

// Convert Q-value to double
template<typename T, typename CalcT, int FB>
double qvalue_to_double(QValue<T, CalcT, FB> qv) {
    return qv.to_double();
}

// =============================================================================
// Saturating arithmetic functions for raw T values
// These maintain the original behavior for raw Q-format arithmetic
// =============================================================================

template<typename T, typename CalcT = DefaultCalcT<T>>
T sat_add(T a, T b) {
    CalcT result = static_cast<CalcT>(a) + static_cast<CalcT>(b);
    if (result > std::numeric_limits<T>::max()) {
        return std::numeric_limits<T>::max();
    }
    if (result < std::numeric_limits<T>::min()) {
        return std::numeric_limits<T>::min();
    }
    return static_cast<T>(result);
}

template<typename T, typename CalcT = DefaultCalcT<T>>
T sat_sub(T a, T b) {
    CalcT result = static_cast<CalcT>(a) - static_cast<CalcT>(b);
    if (result > std::numeric_limits<T>::max()) {
        return std::numeric_limits<T>::max();
    }
    if (result < std::numeric_limits<T>::min()) {
        return std::numeric_limits<T>::min();
    }
    return static_cast<T>(result);
}

template<typename T, typename CalcT = DefaultCalcT<T>, int FB = 16>
T sat_mul_q(T a, T b) {
    CalcT result = static_cast<CalcT>(a) * static_cast<CalcT>(b);
    result >>= FB;
    if (result > std::numeric_limits<T>::max()) {
        return std::numeric_limits<T>::max();
    }
    if (result < std::numeric_limits<T>::min()) {
        return std::numeric_limits<T>::min();
    }
    return static_cast<T>(result);
}

template<typename T, typename CalcT = DefaultCalcT<T>>
T sat_mul(T a, T b) {
    CalcT result = static_cast<CalcT>(a) * static_cast<CalcT>(b);
    if (result > std::numeric_limits<T>::max()) {
        return std::numeric_limits<T>::max();
    }
    if (result < std::numeric_limits<T>::min()) {
        return std::numeric_limits<T>::min();
    }
    return static_cast<T>(result);
}

} // namespace qformat
