import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 1. 获取URDF路径
    urdf_package_path = get_package_share_directory('fishbot_description')
    default_urdf_path = os.path.join(urdf_package_path, 'urdf', 'first_robot.urdf')
    
    # 2. 声明参数
    declare_model_arg = launch.actions.DeclareLaunchArgument(
        name='model',
        default_value=str(default_urdf_path),
        description='URDF模型文件路径'
    )
    
    # 3. 读取URDF内容（修复了原代码的拼写错误和cat命令问题）
    with open(default_urdf_path, 'r') as f:
        urdf_content = f.read()
    
    # 4. 启动robot_state_publisher
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': urdf_content}]
    )
    
    # 5. 启动joint_state_publisher（发布关节状态）
    joint_state_publisher_node = launch_ros.actions.Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'source_list': ['joint_states'], 'use_sim_time': False}]
    )
    
    # 6. 启动RViz2
    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(urdf_package_path, 'rviz', 'display.rviz')]  # 如果有配置文件
    )
    
    return launch.LaunchDescription([
        declare_model_arg,
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node,
    ])