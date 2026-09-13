#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/pose_with_covariance_stamped.hpp>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Matrix3x3.h>
#include <tf2/utils.h>
#include <chrono>
#include <vector>
#include <array>
#include <memory>

class PatrolNode : public rclcpp::Node
{
public:
  using NavigateToPose = nav2_msgs::action::NavigateToPose;
  using GoalHandleNavigateToPose = rclcpp_action::ClientGoalHandle<NavigateToPose>;

  PatrolNode(const std::string & node_name = "patrol_node")
  : rclcpp::Node(node_name)
  {
    // 导航相关定义
    this->declare_parameter<std::vector<double>>("initial_point", {0.0, 0.0, 0.0});
    this->declare_parameter<std::vector<double>>("target_points", {0.0, 0.0, 0.0, 1.0, 1.0, 1.57});
    this->get_parameter("initial_point", initial_point_);
    this->get_parameter("target_points", target_points_);

    // 创建导航动作客户端
    action_client_ = rclcpp_action::create_client<NavigateToPose>(this, "navigate_to_pose");

    // 创建初始位姿发布者
    initial_pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseWithCovarianceStamped>(
      "/initialpose", 10);

    // 创建TF缓冲区与监听器
    tf_buffer_ = std::make_shared<tf2_ros::Buffer>(this->get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
  }

  geometry_msgs::msg::PoseStamped get_pose_by_xyyaw(double x, double y, double yaw)
  {
    /**
     * 通过 x,y,yaw 合成 PoseStamped
     */
    geometry_msgs::msg::PoseStamped pose;
    pose.header.frame_id = "map";
    pose.pose.position.x = x;
    pose.pose.position.y = y;
    tf2::Quaternion rotation_quat;
    rotation_quat.setRPY(0, 0, yaw);
    pose.pose.orientation.x = rotation_quat.x();
    pose.pose.orientation.y = rotation_quat.y();
    pose.pose.orientation.z = rotation_quat.z();
    pose.pose.orientation.w = rotation_quat.w();
    return pose;
  }

  void setInitialPose(const geometry_msgs::msg::PoseStamped & pose)
  {
    geometry_msgs::msg::PoseWithCovarianceStamped init_pose;
    init_pose.header = pose.header;
    init_pose.pose.pose = pose.pose;
    initial_pose_pub_->publish(init_pose);
  }

  void waitUntilNav2Active()
  {
    while (!action_client_->wait_for_action_server(std::chrono::seconds(1))) {
      if (!rclcpp::ok()) {
        RCLCPP_ERROR(this->get_logger(), "等待导航服务器时被中断");
        return;
      }
      RCLCPP_INFO(this->get_logger(), "等待导航服务器就绪...");
    }
  }

  void init_robot_pose()
  {
    /**
     * 初始化机器人位姿
     */
    // 从参数获取初始化点
    this->get_parameter("initial_point", initial_point_);
    // 合成位姿并进行初始化
    this->setInitialPose(this->get_pose_by_xyyaw(
      this->initial_point_[0], this->initial_point_[1], this->initial_point_[2]));
    // 等待直到导航激活
    this->waitUntilNav2Active();
  }

  std::vector<std::array<double, 3>> get_target_points()
  {
    /**
     * 通过参数值获取目标点集合
     */
    std::vector<std::array<double, 3>> points;
    this->get_parameter("target_points", target_points_);
    for (size_t index = 0; index < static_cast<size_t>(this->target_points_.size() / 3); ++index) {
      double x = this->target_points_[index * 3];
      double y = this->target_points_[index * 3 + 1];
      double yaw = this->target_points_[index * 3 + 2];
      points.push_back({x, y, yaw});
      RCLCPP_INFO(this->get_logger(), "获取到目标点: %zu->(%.2f,%.2f,%.2f)", index, x, y, yaw);
    }
    return points;
  }

  void nav_to_pose(const geometry_msgs::msg::PoseStamped & target_pose)
  {
    /**
     * 导航到指定位姿
     */
    this->waitUntilNav2Active();

    auto goal_msg = NavigateToPose::Goal();
    goal_msg.pose = target_pose;

    auto send_goal_options = rclcpp_action::Client<NavigateToPose>::SendGoalOptions();
    send_goal_options.goal_response_callback =
      [this](std::shared_ptr<GoalHandleNavigateToPose> goal_handle) {
        if (!goal_handle) {
          RCLCPP_ERROR(this->get_logger(), "目标被服务器拒绝");
        } else {
          RCLCPP_INFO(this->get_logger(), "目标被服务器接受，等待结果");
        }
      };
    send_goal_options.feedback_callback =
      [this](std::shared_ptr<GoalHandleNavigateToPose>,
        const std::shared_ptr<const NavigateToPose::Feedback> feedback) {
        double remaining_sec = feedback->estimated_time_remaining.sec +
          feedback->estimated_time_remaining.nanosec / 1e9;
        RCLCPP_INFO(this->get_logger(), "预计: %.2f s 后到达", remaining_sec);
      };
    send_goal_options.result_callback =
      [this](const GoalHandleNavigateToPose::WrappedResult & result) {
        // 最终结果判断
        switch (result.code) {
          case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(this->get_logger(), "导航结果：成功");
            break;
          case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(this->get_logger(), "导航结果：被取消");
            break;
          case rclcpp_action::ResultCode::ABORTED:
            RCLCPP_ERROR(this->get_logger(), "导航结果：失败");
            break;
          default:
            RCLCPP_ERROR(this->get_logger(), "导航结果：返回状态无效");
            break;
        }
      };

    auto goal_handle_future = action_client_->async_send_goal(goal_msg, send_goal_options);

    if (rclcpp::spin_until_future_complete(this->get_node_base_interface(), goal_handle_future) !=
      rclcpp::FutureReturnCode::SUCCESS)
    {
      RCLCPP_ERROR(this->get_logger(), "发送目标失败");
      return;
    }

    std::shared_ptr<GoalHandleNavigateToPose> goal_handle = goal_handle_future.get();
    if (!goal_handle) {
      RCLCPP_ERROR(this->get_logger(), "目标被服务器拒绝");
      return;
    }

    auto result_future = action_client_->async_get_result(goal_handle);

    if (rclcpp::spin_until_future_complete(this->get_node_base_interface(), result_future) !=
      rclcpp::FutureReturnCode::SUCCESS)
    {
      RCLCPP_ERROR(this->get_logger(), "获取结果失败");
      return;
    }
  }

  geometry_msgs::msg::TransformStamped get_current_pose()
  {
    /**
     * 通过TF获取当前位姿
     */
    while (rclcpp::ok()) {
      try {
        auto tf = tf_buffer_->lookupTransform(
          "map", "base_footprint", tf2::TimePointZero, tf2::durationFromSec(1.0));
        auto transform = tf.transform;
        tf2::Quaternion q(
          transform.rotation.x,
          transform.rotation.y,
          transform.rotation.z,
          transform.rotation.w);
        tf2::Matrix3x3 m(q);
        double roll, pitch, yaw;
        m.getRPY(roll, pitch, yaw);
        RCLCPP_INFO(
          this->get_logger(),
          "平移:[%.2f,%.2f,%.2f],旋转四元数:[%.2f,%.2f,%.2f,%.2f]:旋转欧拉角:[%.2f,%.2f,%.2f]",
          transform.translation.x, transform.translation.y, transform.translation.z,
          transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w,
          roll, pitch, yaw);
        return tf;
      } catch (const tf2::TransformException & e) {
        RCLCPP_WARN(this->get_logger(), "不能够获取坐标变换，原因: %s", e.what());
      }
    }
    return geometry_msgs::msg::TransformStamped();
  }

private:
  rclcpp_action::Client<NavigateToPose>::SharedPtr action_client_;
  rclcpp::Publisher<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr initial_pose_pub_;
  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
  std::vector<double> initial_point_;
  std::vector<double> target_points_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto patrol = std::make_shared<PatrolNode>();
  patrol->init_robot_pose();

  while (rclcpp::ok()) {
    for (const auto & point : patrol->get_target_points()) {
      double x = point[0];
      double y = point[1];
      double yaw = point[2];
      // 导航到目标点
      auto target_pose = patrol->get_pose_by_xyyaw(x, y, yaw);
      patrol->nav_to_pose(target_pose);
    }
  }
  rclcpp::shutdown();
  return 0;
}

