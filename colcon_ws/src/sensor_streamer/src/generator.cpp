// Copyright 2024 Nawe Robotics
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <chrono>
#include <cmath>
#include <memory>
#include <random>
#include <vector>

#include <Eigen/Dense>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int32.hpp"
#include "std_msgs/msg/float32.hpp"

class SyntheticDataNode : public rclcpp::Node
{
public:
  /*! Constructor for SyntheticDataNode
   *  Declare and load all parameters, initialize calculation constants,
   *  set up Eigen vectors, and create publishers/timers.
   */
  explicit SyntheticDataNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("synthetic_sensor_cpp", options)
  {
    this->declare_parameter<std::vector<double>>("amplitudes", {1.0, 0.5});
    this->declare_parameter<std::vector<double>>("frequencies", {1.0, 2.0});
    this->declare_parameter<std::vector<double>>("phases", {0.0, M_PI/2});
    this->declare_parameter<double>("wheel_circumference", 0.203);
    this->declare_parameter<int>("counts_per_revolution", 4096);
    this->declare_parameter<int>("seed", 42);
    this->declare_parameter<double>("imu.rate", 2000.0);
    this->declare_parameter<double>("imu.noise_std", 0.0);
    this->declare_parameter<double>("imu.drop_rate", 0.0);
    this->declare_parameter<double>("imu.jitter_range", 0.0);
    this->declare_parameter<double>("encoder.rate", 1.0);
    this->declare_parameter<double>("encoder.drop_rate", 0.0);
    this->declare_parameter<double>("encoder.jitter_range", 0.0);

    amplitudes_ = this->get_parameter("amplitudes").as_double_array();
    frequencies_ = this->get_parameter("frequencies").as_double_array();
    phases_ = this->get_parameter("phases").as_double_array();
    wheel_circumference_ = this->get_parameter("wheel_circumference").as_double();
    counts_per_revolution_ = this->get_parameter("counts_per_revolution").as_int();
    seed_ = this->get_parameter("seed").as_int();
    imu_rate_ = this->get_parameter("imu.rate").as_double();
    imu_noise_std_ = this->get_parameter("imu.noise_std").as_double();
    imu_drop_rate_ = this->get_parameter("imu.drop_rate").as_double();
    imu_jitter_range_ = this->get_parameter("imu.jitter_range").as_double();
    encoder_rate_ = this->get_parameter("encoder.rate").as_double();
    encoder_drop_rate_ = this->get_parameter("encoder.drop_rate").as_double();
    encoder_jitter_range_ = this->get_parameter("encoder.jitter_range").as_double();

    rng_.seed(seed_);
    RCLCPP_INFO(this->get_logger(), "Random seed set to %d for repeatable data generation", seed_);

    two_pi_ = 2.0 * M_PI;
    noise_dist_ = std::normal_distribution<double>(0.0, imu_noise_std_);
    
    size_t n = amplitudes_.size();
    A_.resize(n);
    f_.resize(n);
    phi_.resize(n);
    A_cos_phi_.resize(n);
    A_sin_phi_.resize(n);
    two_pi_f_.resize(n);
    
    for (size_t i = 0; i < n; ++i) {
      A_[i] = amplitudes_[i];
      f_[i] = frequencies_[i];
      phi_[i] = phases_[i];
      A_cos_phi_[i] = A_[i] * std::cos(phi_[i]);
      A_sin_phi_[i] = A_[i] * std::sin(phi_[i]);
      two_pi_f_[i] = two_pi_ * f_[i];
    }
    
    A_cos_phi_eigen_ = Eigen::Map<Eigen::VectorXd>(A_cos_phi_.data(), n);
    A_sin_phi_eigen_ = Eigen::Map<Eigen::VectorXd>(A_sin_phi_.data(), n);
    two_pi_f_eigen_ = Eigen::Map<Eigen::VectorXd>(two_pi_f_.data(), n);
    
    angles_.resize(n);
    sines_.resize(n);
    cosines_.resize(n);

    imu_use_jitter_ = imu_jitter_range_ > 0.0;
    encoder_use_jitter_ = encoder_jitter_range_ > 0.0;
    imu_use_dropout_ = imu_drop_rate_ > 0.0;
    encoder_use_dropout_ = encoder_drop_rate_ > 0.0;

    t0_ = this->now();
    imu_prev_time_ = t0_;
    imu_prev_velocity_ = 0.0;
    encoder_prev_time_ = t0_;
    encoder_position_ = 0.0;

    encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("encoder_count", 10);
    imu_pub_ = this->create_publisher<std_msgs::msg::Float32>("accel_x_mss", 10);

    imu_msg_ = std::make_shared<std_msgs::msg::Float32>();
    encoder_msg_ = std::make_shared<std_msgs::msg::Int32>();

    if (imu_rate_ > 0.0) {
      imu_timer_ = this->create_wall_timer(
        std::chrono::duration<double>(1.0 / imu_rate_),
        [this]() { this->publish_imu(); });
    }
    if (encoder_rate_ > 0.0) {
      encoder_timer_ = this->create_wall_timer(
        std::chrono::duration<double>(1.0 / encoder_rate_),
        [this]() { this->publish_encoder(); });
    }
  }

private:
  /*! Publish IMU data with configurable noise, dropout, and jitter */
  void publish_imu()
  {
    auto current_time = this->now();
    double t = (current_time - t0_).seconds();
    double dt = (current_time - imu_prev_time_).seconds();

    double current_vel = velocity(t);
    double acceleration = (dt > 0.0) ? (current_vel - imu_prev_velocity_) / dt : 0.0;

    if (imu_use_dropout_ && (drop_dist_(rng_) < imu_drop_rate_)) {
      return;
    }

    double imu_accel = acceleration + noise_dist_(rng_);
    imu_msg_->data = static_cast<float>(imu_accel);
    imu_pub_->publish(*imu_msg_);

    if (imu_use_jitter_) {
      std::this_thread::sleep_for(std::chrono::duration<double>(
        jitter_dist_(rng_) * imu_jitter_range_ / imu_rate_));
    }

    imu_prev_velocity_ = current_vel;
    imu_prev_time_ = current_time;
  }

  /*! Publish encoder data with configurable dropout and jitter */
  void publish_encoder()
  {
    auto current_time = this->now();
    double t = (current_time - t0_).seconds();
    double dt = (current_time - encoder_prev_time_).seconds();

    double current_vel = velocity(t);
    encoder_position_ += current_vel * dt;

    if (encoder_use_dropout_ && (drop_dist_(rng_) < encoder_drop_rate_)) {
      return;
    }

    double rotations = encoder_position_ / wheel_circumference_;
    int32_t encoder_count = static_cast<int32_t>(rotations * counts_per_revolution_);
    encoder_msg_->data = encoder_count;
    encoder_pub_->publish(*encoder_msg_);

    if (encoder_use_jitter_) {
      std::this_thread::sleep_for(std::chrono::duration<double>(
        jitter_dist_(rng_) * encoder_jitter_range_ / encoder_rate_));
    }

    encoder_prev_time_ = current_time;
  }

  /*! Calculate velocity using Eigen vectorization for fast computation */
  double velocity(double t)
  {
    angles_ = two_pi_f_eigen_ * t;
    sines_ = angles_.array().sin();
    cosines_ = angles_.array().cos();
    
    return (A_cos_phi_eigen_.array() * sines_.array() + 
            A_sin_phi_eigen_.array() * cosines_.array()).sum();
  }

  // Parameters
  std::vector<double> amplitudes_;
  std::vector<double> frequencies_;
  std::vector<double> phases_;
  double wheel_circumference_;
  int counts_per_revolution_;
  int seed_;
  double imu_rate_;
  double imu_noise_std_;
  double imu_drop_rate_;
  double imu_jitter_range_;
  double encoder_rate_;
  double encoder_drop_rate_;
  double encoder_jitter_range_;

  // Pre-computed constants
  double two_pi_;
  std::vector<double> A_;
  std::vector<double> f_;
  std::vector<double> phi_;
  std::vector<double> A_cos_phi_;
  std::vector<double> A_sin_phi_;
  std::vector<double> two_pi_f_;
  
  // Eigen vectors for fast matrix operations
  Eigen::VectorXd A_cos_phi_eigen_;
  Eigen::VectorXd A_sin_phi_eigen_;
  Eigen::VectorXd two_pi_f_eigen_;
  
  // Workspace for intermediate calculations
  Eigen::VectorXd angles_;
  Eigen::VectorXd sines_;
  Eigen::VectorXd cosines_;

  // Flags
  bool imu_use_jitter_;
  bool encoder_use_jitter_;
  bool imu_use_dropout_;
  bool encoder_use_dropout_;

  // State
  rclcpp::Time t0_;
  rclcpp::Time imu_prev_time_;
  double imu_prev_velocity_;
  rclcpp::Time encoder_prev_time_;
  double encoder_position_;

  // ROS 2 components
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr encoder_pub_;
  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr imu_pub_;
  rclcpp::TimerBase::SharedPtr imu_timer_;
  rclcpp::TimerBase::SharedPtr encoder_timer_;
  std::shared_ptr<std_msgs::msg::Float32> imu_msg_;
  std::shared_ptr<std_msgs::msg::Int32> encoder_msg_;

  // Random number generation
  std::mt19937 rng_;
  std::uniform_real_distribution<double> drop_dist_{0.0, 1.0};
  std::normal_distribution<double> noise_dist_;
  std::uniform_real_distribution<double> jitter_dist_{0.0, 1.0};
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SyntheticDataNode>());
  rclcpp::shutdown();
  return 0;
}

