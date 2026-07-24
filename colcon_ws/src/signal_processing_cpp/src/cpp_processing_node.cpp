/**
 * C++ Processing Node for Signal Processing Pipeline
 * 
 * This node subscribes to integer and floating-point sensor streams,
 * applies moving average and low-pass filters using the standalone C++ library,
 * and publishes the filtered results.
 * 
 * This version uses simplified template instantiation with concrete types
 * to avoid complex template metaprogramming while still meeting Part 3 requirements.
 * 
 * Requirements:
 * - The custom_lib must be built and accessible
 * - ROS2 environment properly sourced
 * 
 * Usage:
 *     ros2 run signal_processing_cpp cpp_processing_node
 *      
 *     # With parameters
 *     ros2 run signal_processing_cpp cpp_processing_node --ros-args -p ma_window_size:=10 -p lp_cutoff:=5.0
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/float32.hpp>
#include <chrono>
#include <memory>

// Include the standalone signal processing library headers
#include "running_data/lib/fixed_moving_average.hpp"
#include "running_data/lib/time_duration_moving_average.hpp"
#include "filters/lib/fixed_point_low_pass_filter.hpp"
#include "filters/lib/float_low_pass_filter.hpp"

using namespace std::chrono_literals;

class CppProcessingNode : public rclcpp::Node {
public:
    CppProcessingNode()
        : Node("cpp_processing_node")
    {
        // Declare parameters with defaults
        this->declare_parameter<int>("ma_window_size", 5);
        this->declare_parameter<double>("lp_cutoff_hz", 10.0);
        this->declare_parameter<double>("ma_window_duration_ms", 100.0);
        this->declare_parameter<bool>("use_time_based_ma", false);
        this->declare_parameter<int>("fixed_point_bits", 16);
        this->declare_parameter<double>("timeout_seconds", 10.0);

        // Get parameter values
        int ma_window_size = this->get_parameter("ma_window_size").as_int();
        double lp_cutoff_hz = this->get_parameter("lp_cutoff_hz").as_double();
        double ma_window_duration_ms = this->get_parameter("ma_window_duration_ms").as_double();
        bool use_time_based_ma = this->get_parameter("use_time_based_ma").as_bool();
        int fixed_point_bits = this->get_parameter("fixed_point_bits").as_int();
        double timeout_seconds = this->get_parameter("timeout_seconds").as_double();

        RCLCPP_INFO(this->get_logger(), 
                   "Parameters: MA window=%d, LP cutoff=%.1fHz, Time-based MA=%s, FP bits=%d, timeout=%.3fs",
                   ma_window_size, lp_cutoff_hz, use_time_based_ma ? "true" : "false", fixed_point_bits, timeout_seconds);

        // Initialize moving average filters with timeout
        // Timeout causes reset on dropout gaps > timeout_seconds
        if (use_time_based_ma) {
            // Use time-based moving average with 500 max samples and timeout
            ma_encoder_ = std::make_unique<TimeDurationMovingAverage<int, 500>>(
                ma_window_size, std::chrono::milliseconds(static_cast<int>(ma_window_duration_ms)), timeout_seconds);
            ma_accel_ = std::make_unique<TimeDurationMovingAverage<double, 500>>(
                ma_window_size, std::chrono::milliseconds(static_cast<int>(ma_window_duration_ms)), timeout_seconds);
        } else {
            // Use fixed-size moving average with 500 max samples and timeout
            ma_encoder_ = std::make_unique<FixedMovingAverage<int, 500>>(ma_window_size, timeout_seconds);
            ma_accel_ = std::make_unique<FixedMovingAverage<double, 500>>(ma_window_size, timeout_seconds);
        }

        // Initialize low-pass filters based on fixed-point bits
        // For encoder (integer) stream, use fixed-point filter with appropriate Q-format
        if (fixed_point_bits == 8) {
            // Q24.8 format
            lp_encoder_24_8_ = std::make_unique<FixedPointLowPassFilter_24_8>(lp_cutoff_hz, 8, timeout_seconds);
            active_encoder_filter_ = 8;
        } else if (fixed_point_bits == 16) {
            // Q16.16 format (default)
            lp_encoder_16_16_ = std::make_unique<FixedPointLowPassFilter_16_16>(lp_cutoff_hz, 16, timeout_seconds);
            active_encoder_filter_ = 16;
        } else if (fixed_point_bits == 24) {
            // Q8.24 format
            lp_encoder_8_24_ = std::make_unique<FixedPointLowPassFilter_8_24>(lp_cutoff_hz, 24, timeout_seconds);
            active_encoder_filter_ = 24;
        } else if (fixed_point_bits == 30) {
            // Q2.30 format
            lp_encoder_2_30_ = std::make_unique<FixedPointLowPassFilter_2_30>(lp_cutoff_hz, 30, timeout_seconds);
            active_encoder_filter_ = 30;
        } else {
            // Default to Q16.16
            lp_encoder_16_16_ = std::make_unique<FixedPointLowPassFilter_16_16>(lp_cutoff_hz, 16, timeout_seconds);
            active_encoder_filter_ = 16;
        }

        // For accel (float) stream, use float filter
        lp_accel_ = std::make_unique<FloatLowPassFilter_Double>(lp_cutoff_hz, timeout_seconds);

        RCLCPP_INFO(this->get_logger(), "Filters created");
        RCLCPP_INFO(this->get_logger(), "  Encoder MA: %s", use_time_based_ma ? "TimeDuration" : "Fixed");
        RCLCPP_INFO(this->get_logger(), "  Accel MA: %s", use_time_based_ma ? "TimeDuration" : "Fixed");
        RCLCPP_INFO(this->get_logger(), "  Encoder LP: FixedPointLowPassFilter (Q%d.%d)", 
                   (32 - fixed_point_bits), fixed_point_bits);
        RCLCPP_INFO(this->get_logger(), "  Accel LP: FloatLowPassFilter_Double");

        // Create subscribers
        encoder_sub_ = this->create_subscription<std_msgs::msg::Int32>(
            "encoder_count", 10, 
            [this](const std_msgs::msg::Int32::SharedPtr msg) {
                this->encoder_callback(msg);
            });

        accel_sub_ = this->create_subscription<std_msgs::msg::Float32>(
            "accel_x_mss", 10, 
            [this](const std_msgs::msg::Float32::SharedPtr msg) {
                this->accel_callback(msg);
            });

        // Create publishers
        filtered_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("filtered_encoder_count", 10);
        filtered_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("filtered_accel_x_mss", 10);
        ma_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("ma_encoder", 10);
        ma_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("ma_accel", 10);
        lp_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("lp_encoder", 10);
        lp_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("lp_accel", 10);

        RCLCPP_INFO(this->get_logger(), "C++ processing node initialized");
        RCLCPP_INFO(this->get_logger(), "Subscribed to: /encoder_count, /accel_x_mss");
        RCLCPP_INFO(this->get_logger(), "Publishing to: /filtered_encoder_count, /filtered_accel_x_mss, /ma_encoder, /ma_accel, /lp_encoder, /lp_accel");
    }

private:
    void encoder_callback(const std_msgs::msg::Int32::SharedPtr msg) {
        auto current_time = this->now();
        int32_t value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = std::chrono::duration<double>(current_time - last_encoder_time_).count();
        last_encoder_time_ = current_time;
        
        // Apply moving average
        int32_t ma_result = ma_encoder_->update(value);
        
        // Apply low-pass filter
        // Convert rclcpp::Time to std::chrono::steady_clock::time_point for the filter
        auto now_time_point = std::chrono::steady_clock::time_point(
            std::chrono::nanoseconds(current_time.nanoseconds()));
        
        // Apply low-pass filter based on which type is active
        int32_t lp_result = 0;
        switch (active_encoder_filter_) {
            case 8:
                lp_result = lp_encoder_24_8_->update(value, now_time_point);
                break;
            case 16:
                lp_result = lp_encoder_16_16_->update(value, now_time_point);
                break;
            case 24:
                lp_result = lp_encoder_8_24_->update(value, now_time_point);
                break;
            case 30:
                lp_result = lp_encoder_2_30_->update(value, now_time_point);
                break;
            default:
                // Fallback to simple update without timestamp
                // This should not happen if initialization is correct
                lp_result = value;
                break;
        }
        
        // For now, use moving average as filtered result
        int32_t filtered_result = ma_result;
        
        // Publish results
        auto ma_msg = std_msgs::msg::Int32();
        ma_msg.data = ma_result;
        ma_encoder_pub_->publish(ma_msg);
        
        auto lp_msg = std_msgs::msg::Int32();
        lp_msg.data = lp_result;
        lp_encoder_pub_->publish(lp_msg);
        
        auto filtered_msg = std_msgs::msg::Int32();
        filtered_msg.data = filtered_result;
        filtered_encoder_pub_->publish(filtered_msg);
        
        // Log occasionally
        if (ma_encoder_->currentSize() % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Encoder processing: raw=%d, ma=%d, lp=%d, dt=%.3fs",
                         value, ma_result, lp_result, dt);
        }
    }

    void accel_callback(const std_msgs::msg::Float32::SharedPtr msg) {
        auto current_time = this->now();
        double value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = std::chrono::duration<double>(current_time - last_accel_time_).count();
        last_accel_time_ = current_time;
        
        // Apply moving average
        double ma_result = ma_accel_->update(value);
        
        // Apply low-pass filter
        // Convert rclcpp::Time to std::chrono::steady_clock::time_point for the filter
        auto now_time_point = std::chrono::steady_clock::time_point(
            std::chrono::nanoseconds(current_time.nanoseconds()));
        double lp_result = lp_accel_->update(value, now_time_point);
        
        // For now, use moving average as filtered result
        double filtered_result = ma_result;
        
        // Publish results
        auto ma_msg = std_msgs::msg::Float32();
        ma_msg.data = static_cast<float>(ma_result);
        ma_accel_pub_->publish(ma_msg);
        
        auto lp_msg = std_msgs::msg::Float32();
        lp_msg.data = static_cast<float>(lp_result);
        lp_accel_pub_->publish(lp_msg);
        
        auto filtered_msg = std_msgs::msg::Float32();
        filtered_msg.data = static_cast<float>(filtered_result);
        filtered_accel_pub_->publish(filtered_msg);
        
        // Log occasionally
        if (ma_accel_->currentSize() % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Accel processing: raw=%.3f, ma=%.3f, lp=%.3f, dt=%.3fs",
                         value, ma_result, lp_result, dt);
        }
    }

    // Subscribers
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr encoder_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr accel_sub_;

    // Publishers
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr filtered_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr filtered_accel_pub_;
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr ma_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr ma_accel_pub_;
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr lp_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr lp_accel_pub_;

    // Filter instances
    // Moving average filters - use base class unique_ptr for polymorphism
    std::unique_ptr<FixedMovingAverage<int, 500>> ma_encoder_;
    std::unique_ptr<FixedMovingAverage<double, 500>> ma_accel_;
    
    // Low-pass filter for encoder (integer) - use base class pointer for polymorphism
    // The concrete type will be one of the FixedPointLowPassFilter_*_* instatiations
    // We use void* and dynamic_cast to handle different Q-formats since C++ templates don't have runtime polymorphism
    // For simplicity, we'll use four separate unique_ptrs and activate the right one
    std::unique_ptr<FixedPointLowPassFilter_24_8> lp_encoder_24_8_;
    std::unique_ptr<FixedPointLowPassFilter_16_16> lp_encoder_16_16_;
    std::unique_ptr<FixedPointLowPassFilter_8_24> lp_encoder_8_24_;
    std::unique_ptr<FixedPointLowPassFilter_2_30> lp_encoder_2_30_;
    
    // Low-pass filter for accel (float)
    std::unique_ptr<FloatLowPassFilter_Double> lp_accel_;
    
    // Track which encoder filter is active
    int active_encoder_filter_ = 16; // 8, 16, 24, or 30

    // Timestamps for dt calculation
    rclcpp::Time last_encoder_time_ = this->now();
    rclcpp::Time last_accel_time_ = this->now();
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<CppProcessingNode>();
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    
    return 0;
}
