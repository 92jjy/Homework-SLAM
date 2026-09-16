
考核题目分为四个小题，可以由两个终端来完成。先进行cmake编译
终端一：ros2 launch fishbot_description gazebo_sim.launch.py 启动仿真，可以在里面实现运动控制（键盘控制节点）使用ros2 control的内置差速驱动器
终端二：ros2 launch fishbot_navigation2 navigation2.launch.py 实现路径规划与全局避障，nav2的控制可显示处理约束，mpc更适合机器人对抗，在启动nav2之期还要占据地图构建map
（因为我直接使用了nav2框架，底层算法在document仓库有复刻）
