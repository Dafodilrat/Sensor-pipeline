/**
 * Mean Filter Processing Node for Signal Processing Pipeline
 * 
 * This node subscribes to integer and floating-point sensor streams,
 * applies moving average (mean) filters using the standalone C++ library,
 * and publishes the filtered results.
 * 
 * This is a dedicated mean filter node without low-pass filter components.
 * 
 * Requirements:
 * - The custom_lib must be built and accessible
 * - ROS2 environment properly sourced
 * 
 * Usage:
 *     ros2 run signal_processing_cpp mean_filter_node
 *       
 *     # With parameters
 *     ros2 run signal_processing_cpp mean_filter_node --ros-args -p ma_window_size:=10 -p use_time_based_ma:=false -p ma_window_duration_ms:=100.0 -p timeout_seconds:=10.0
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/float32.hpp>
#include <chrono>
#include <memory>

// Include the standalone signal processing library headers for moving average
#include "nawe_robotics_lib/running_data/lib/fixed_moving_average.hpp"
#include "nawe_robotics_lib/running_data/lib/time_duration_moving_average.hpp"

using namespace std::chrono_literals;

class MeanFilterNode : public rclcpp::Node {
public:
    MeanFilterNode()
        : Node("mean_filter_node")
    {
        // Declare parameters with defaults
        this->declare_parameter<int>("ma_window_size", 5);
        this->declare_parameter<double>("ma_window_duration_ms", 100.0);
        this->declare_parameter<bool>("use_time_based_ma", false);
        this->declare_parameter<double>("timeout_seconds", 10.0);

        // Get parameter values
        int ma_window_size = this->get_parameter("ma_window_size").as_int();
        double ma_window_duration_ms = this->get_parameter("ma_window_duration_ms").as_double();
        bool use_time_based_ma = this->get_parameter("use_time_based_ma").as_bool();
        double timeout_seconds = this->get_parameter("timeout_seconds").as_double();

        RCLCPP_INFO(this->get_logger(), 
                   "Mean Filter Parameters: window_size=%d, time_based=%s, window_duration=%.1fms, timeout=%.3fs",
                   ma_window_size, use_time_based_ma ? "true" : "false", ma_window_duration_ms, timeout_seconds);

        // Initialize moving average filters with timeout
        if (use_time_based_ma) {
            // Use time-based moving average with 500 max samples and timeout
            ma_encoder_time_ = std::make_unique<TimeDurationMovingAverage<int, 500>>(
                ma_window_size, std::chrono::milliseconds(static_cast<int>(ma_window_duration_ms)), timeout_seconds);
            ma_accel_time_ = std::make_unique<TimeDurationMovingAverage<double, 500>>(
                ma_window_size, std::chrono::milliseconds(static_cast<int>(ma_window_duration_ms)), timeout_seconds);
            using_time_based_ = true;
            
            RCLCPP_INFO(this->get_logger(), "Using Time-Based Moving Average filters");
        } else {
            // Use fixed-size moving average with 500 max samples and timeout
            ma_encoder_fixed_ = std::make_unique<FixedMovingAverage<int, 500>>(ma_window_size, timeout_seconds);
            ma_accel_fixed_ = std::make_unique<FixedMovingAverage<double, 500>>(ma_window_size, timeout_seconds);
            using_time_based_ = false;
            
            RCLCPP_INFO(this->get_logger(), "Using Fixed-Size Moving Average filters");
        }

        RCLCPP_INFO(this->get_logger(), "Mean filters created with window size: %d", ma_window_size);

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

        // Create publishers for mean-filtered outputs
        mean_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("mean_encoder", 10);
        mean_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("mean_accel", 10);

        RCLCPP_INFO(this->get_logger(), "Mean filter node initialized");
        RCLCPP_INFO(this->get_logger(), "Subscribed to: /encoder_count, /accel_x_mss");
        RCLCPP_INFO(this->get_logger(), "Publishing to: /mean_encoder, /mean_accel");
    }

private:
    void encoder_callback(const std_msgs::msg::Int32::SharedPtr msg) {
        auto current_time = this->now();
        int32_t value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_encoder_time_).seconds();
        last_encoder_time_ = current_time;
        
        // Apply moving average (mean) filter
        int32_t mean_result = using_time_based_ ? ma_encoder_time_->update(value) : ma_encoder_fixed_->update(value);
        
        // Increment counter
        encoder_update_count_++;
        
        // Publish results
        auto mean_msg = std_msgs::msg::Int32();
        mean_msg.data = mean_result;
        mean_encoder_pub_->publish(mean_msg);
        
        // Log occasionally
        if (encoder_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Encoder Mean: raw=%d, mean=%d, dt=%.3fs, window_size=%zu",
                         value, mean_result, dt, using_time_based_ ? ma_encoder_time_->currentSize() : ma_encoder_fixed_->currentSize());
        }
    }

    void accel_callback(const std_msgs::msg::Float32::SharedPtr msg) {
        auto current_time = this->now();
        double value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_accel_time_).seconds();
        last_accel_time_ = current_time;
        
        // Apply moving average (mean) filter
        double mean_result = using_time_based_ ? ma_accel_time_->update(value) : ma_accel_fixed_->update(value);
        
        // Increment counter
        accel_update_count_++;
        
        // Publish results
        auto mean_msg = std_msgs::msg::Float32();
        mean_msg.data = static_cast<float>(mean_result);
        mean_accel_pub_->publish(mean_msg);
        
        // Log occasionally
        if (accel_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Accel Mean: raw=%.3f, mean=%.3f, dt=%.3fs, window_size=%zu",
                         value, mean_result, dt, using_time_based_ ? ma_accel_time_->currentSize() : ma_accel_fixed_->currentSize());
        }
    }

    // Subscribers
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr encoder_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr accel_sub_;

    // Publishers
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr mean_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr mean_accel_pub_;

    // Filter instances - moving average only
    // Using base class pointers to handle both fixed and time-based MA
    std::unique_ptr<TimeDurationMovingAverage<int, 500>> ma_encoder_time_;
    std::unique_ptr<TimeDurationMovingAverage<double, 500>> ma_accel_time_;
    std::unique_ptr<FixedMovingAverage<int, 500>> ma_encoder_fixed_;
    std::unique_ptr<FixedMovingAverage<double, 500>> ma_accel_fixed_;
    
    // Track which type is active
    bool using_time_based_ = false;
    
    // Timestamps for dt calculation
    rclcpp::Time last_encoder_time_ = this->now();
    rclcpp::Time last_accel_time_ = this->now();
    
    // Counters for occasional logging
    size_t encoder_update_count_ = 0;
    size_t accel_update_count_ = 0;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<MeanFilterNode>();
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    
    return 0;
}
