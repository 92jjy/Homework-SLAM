import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from xacro import process_file

def generate_launch_description():
    # 获取包路径
    pkg_path = get_package_share_directory('fishbot_description')
    
    # 使用 xacro 处理 URDF
    xacro_file = os.path.join(pkg_path, 'urdf', 'robot_gazebo.xacro')
    robot_description = process_file(xacro_file).toxml()
    
    gazebo_ros_path = get_package_share_directory('gazebo_ros')
    
    return LaunchDescription([
        # 启动 Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_ros_path, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={
                'world': '/usr/share/gazebo-11/worlds/empty.world'
            }.items()
        ),
        
        # robot_state_publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),
        
        # joint_state_publisher_gui（关节控制）
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            output='screen'
        ),
        
        # 生成机器人到 Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'my_robot',
                '-topic', 'robot_description',
                '-x', '0.0',
                '-y', '0.0',
                '-z', '0.3'
            ],
            output='screen'
        )
    ])
