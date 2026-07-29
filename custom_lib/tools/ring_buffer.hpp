#pragma once

#include <array>
#include <stdexcept>

// =============================================================================
// RingBuffer: A generic circular buffer implementation
// All index types are int (Capacity is still size_t for template parameter)
// =============================================================================
template<typename T, size_t Capacity>
class RingBuffer {
    private:
        std::array<T, Capacity> buffer_{};
        int head_ = -1;         // position of newest element, -1 = empty
        int tail_ = 0;          // position of oldest element (next pop), always >= 0
        int count_ = 0;
        int size_limit_ = static_cast<int>(Capacity);

    public:
        // Constructor with optional runtime size limit
        explicit RingBuffer(int size_limit = static_cast<int>(Capacity)) 
            : buffer_(), head_(-1), tail_(0), count_(0), size_limit_(size_limit) {
            if (size_limit <= 0) {
                throw std::invalid_argument("RingBuffer: size limit must be positive");
            }
            if (static_cast<size_t>(size_limit) > Capacity) {
                throw std::invalid_argument("RingBuffer: size limit cannot exceed Capacity");
            }
        }

        T push(const T& value) {
            T removed = value;
            
            if (full()) {
                // Buffer is full, pop the oldest to make room
                removed = pop();
            }
            
            // head_ starts at -1, (-1 + 1) % size_limit_ = 0
            // On first push: head_ becomes 0, tail_ is already 0, no need to set tail_
            head_ = (head_ + 1) % size_limit_;
            buffer_[head_] = value;
            count_++;
            
            return removed;
        }

        T pop() {
            if (empty()) {
                throw std::runtime_error("RingBuffer: cannot pop from empty buffer");
            }
            // Read from tail_ (oldest)
            T value = buffer_[tail_];
            tail_ = (tail_ + 1) % size_limit_;
            count_--;
            
            // If this was the last element, reset to empty state
            if (empty()) {
                clear();
            }
            
            return value;
        }

        // Get latest element (most recently added) - front() is newest
        T& front() {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            // Newest is at head_
            return buffer_[head_];
        }

        // Get oldest element - back() is oldest
        T& back() {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            // Oldest is at tail_
            return buffer_[tail_];
        }

        // Const versions
        const T& front() const {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            return buffer_[head_];
        }

        const T& back() const {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            return buffer_[tail_];
        }

        int size() const { return count_; }
        int capacity() const { return static_cast<int>(Capacity); }
        int size_limit() const { return size_limit_; }
        int head() const { return head_; }
        int tail() const { return tail_; }
        bool empty() const { return count_ == 0; }
        bool full() const { return count_ >= size_limit_; }
        void clear() { head_ = -1; tail_ = 0; count_ = 0; }
        
        // Copy elements to destination array (in insertion order, oldest to newest)
        template<typename DestT>
        void copyTo(DestT (&dest)[Capacity]) const {
            if (empty()) return;
            // tail_ is oldest, head_ is newest, copy sequentially
            for (int i = 0; i < count_; ++i) {
                dest[i] = buffer_[(tail_ + i) % size_limit_];
            }
        }
};
