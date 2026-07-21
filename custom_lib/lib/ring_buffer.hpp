#pragma once

#include <cstddef>
#include <array>
#include <stdexcept>

// =============================================================================
// RingBuffer: A generic circular buffer implementation
// =============================================================================
template<typename T, size_t Capacity>
class RingBuffer {
    private:
        std::array<T, Capacity> buffer_{};
        size_t head_ = 0;
        size_t count_ = 0;

    public:
        T push(const T& value) {
            T removed = value;
            
            if (full()) {
                removed = buffer_[head_];
            }
            
            buffer_[head_] = value;
            head_ = (head_ + 1) % Capacity;
            
            if (!full()) {
                count_++;
            }
            
            return removed;
        }

        T pop() {
            if (empty()) {
                throw std::runtime_error("RingBuffer: cannot pop from empty buffer");
            }
            T value = buffer_[head_];
            head_ = (head_ + 1) % Capacity;
            count_--;
            return value;
        }

        // Get latest element (most recently added) - front() is latest
        T& front() {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            return buffer_[(head_ + Capacity - 1) % Capacity];
        }

        // Get oldest element - back() is oldest
        T& back() {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            size_t oldest_index = (head_ + Capacity - count_) % Capacity;
            return buffer_[oldest_index];
        }

        // Const versions
        const T& front() const {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            return buffer_[(head_ + Capacity - 1) % Capacity];
        }

        const T& back() const {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            size_t oldest_index = (head_ + Capacity - count_) % Capacity;
            return buffer_[oldest_index];
        }

        size_t size() const { return count_; }
        size_t capacity() const { return Capacity; }
        bool empty() const { return count_ == 0; }
        bool full() const { return count_ == Capacity; }
        void clear() { head_ = 0; count_ = 0; }
};
