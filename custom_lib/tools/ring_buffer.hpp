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
        size_t size_limit_ = Capacity;

    public:
        // Constructor with optional runtime size limit
        explicit RingBuffer(size_t size_limit = Capacity) : size_limit_(size_limit) {
            if (size_limit == 0) {
                throw std::invalid_argument("RingBuffer: size limit must be positive");
            }
            if (size_limit > Capacity) {
                throw std::invalid_argument("RingBuffer: size limit cannot exceed Capacity");
            }
        }

        T push(const T& value) {
            T removed = value;
            
            if (full()) {
                removed = buffer_[head_];
                // Remove oldest element
                head_ = (head_ + 1) % Capacity;
                count_--;
            }
            
            buffer_[head_] = value;
            head_ = (head_ + 1) % Capacity;
            
            if (count_ < size_limit_) {
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
        size_t size_limit() const { return size_limit_; }
        size_t head() const { return head_; }
        bool empty() const { return count_ == 0; }
        bool full() const { return count_ >= size_limit_; }
        void clear() { head_ = 0; count_ = 0; }
        
        // Copy elements to destination array (in insertion order, oldest to newest)
        template<typename DestT>
        void copyTo(DestT (&dest)[Capacity]) const {
            if (empty()) return;
            size_t tail = (head_ + Capacity - count_) % Capacity;
            for (size_t i = 0; i < count_; ++i) {
                dest[i] = buffer_[(tail + i) % Capacity];
            }
        }
};
