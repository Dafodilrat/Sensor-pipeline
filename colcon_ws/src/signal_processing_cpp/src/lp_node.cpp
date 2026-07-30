/**
 * Low Pass Filter Processing Node for Signal Processing Pipeline
 * 
 * This node subscribes to integer and floating-point sensor streams,
 * passes through encoder values (no filtering) and applies low-pass filters to accel using the standalone C++ library,
 * and publishes the results.
 * 
 * Requirements:
 * - The custom_lib must be built and accessible
 * - ROS2 environment properly sourced
 * 
 * Usage:
 *     ros2 run signal_processing_cpp lp_node
 *       
 *     # With parameters
 *     ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=10.0 -p timeout_seconds:=10.0
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/float32.hpp>
#include <chrono>
#include <memory>

// Include the standalone signal processing library headers
// Installed to /usr/local/include/nawe_robotics_lib via Docker
#include "nawe_robotics_lib/filters/lib/low_pass_iir_filter.hpp"

using namespace std::chrono_literals;

class LPNode : public rclcpp::Node {
public:
    /*! Constructor for LPNode
     *  Initialize parameters, create low-pass filter, set up subscribers and publishers
     */
    LPNode()
        : Node("lp_node")
    {
        this->declare_parameter<float>("lp_cutoff_hz", 10.0f);
        this->declare_parameter<float>("timeout_seconds", 10.0f);

        float lp_cutoff_hz = this->get_parameter("lp_cutoff_hz").get_value<float>();
        float timeout_seconds = this->get_parameter("timeout_seconds").get_value<float>();

        RCLCPP_INFO(this->get_logger(), 
                   "LP Parameters: cutoff=%.1fHz, timeout=%.3fs",
                   lp_cutoff_hz, timeout_seconds);

        // For accel (float) stream, use float filter
        // Note: LowPassFilterFloat uses Hz and seconds (not times_100 and ns)
        lp_accel_ = std::make_unique<LowPassFilterFloat>(lp_cutoff_hz, timeout_seconds);

        RCLCPP_INFO(this->get_logger(), "Low-pass filter created for accel");
        RCLCPP_INFO(this->get_logger(), "  Accel LP: LowPassFilterFloat");
        RCLCPP_INFO(this->get_logger(), "  Encoder: passthrough (no filtering)");

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

        lp_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("lp_encoder", 10);
        lp_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("lp_accel", 10);

        RCLCPP_INFO(this->get_logger(), "C++ LP node initialized");
        RCLCPP_INFO(this->get_logger(), "Subscribed to: /encoder_count, /accel_x_mss");
        RCLCPP_INFO(this->get_logger(), "Publishing to: /lp_encoder, /lp_accel");
    }

private:
    /*! Handle encoder data - passthrough without filtering */
    void encoder_callback(const std_msgs::msg::Int32::SharedPtr msg) {
        auto current_time = this->now();
        int32_t value = msg->data;
        
        double dt = (current_time - last_encoder_time_).seconds();
        last_encoder_time_ = current_time;
        
        int32_t lp_result = value;
        
        encoder_update_count_++;
        
        auto lp_msg = std_msgs::msg::Int32();
        lp_msg.data = lp_result;
        lp_encoder_pub_->publish(lp_msg);
        
        if (encoder_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Encoder passthrough: raw=%d, published=%d, dt=%.3fs",
                         value, lp_result, dt);
        }
    }

    /*! Handle accel data - apply low-pass filter */
    void accel_callback(const std_msgs::msg::Float32::SharedPtr msg) {
        auto current_time = this->now();
        float value = msg->data;
        
        double dt = (current_time - last_accel_time_).seconds();
        last_accel_time_ = current_time;
        
        // Apply low-pass filter
        // Using update() without timestamp - uses system clock internally
        float lp_result = lp_accel_->update(value);
        
        accel_update_count_++;
        
        auto lp_msg = std_msgs::msg::Float32();
        lp_msg.data = lp_result;
        lp_accel_pub_->publish(lp_msg);
        
        if (accel_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Accel LP: raw=%.3f, lp=%.3f, dt=%.3fs",
                         value, lp_result, dt);
        }
    }

    // Subscribers
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr encoder_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr accel_sub_;

    // Publishers
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr lp_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr lp_accel_pub_;

    // Filter instances
    // Low-pass filter for accel (float)
    std::unique_ptr<LowPassFilterFloat> lp_accel_;

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
    auto node = std::make_shared<LPNode>();
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    
    return 0;
}
