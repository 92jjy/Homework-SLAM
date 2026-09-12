在看到题目后发现与我之前学习ros2的项目十分相似，这个项目中有一部分源自于小鱼的源码，还有相当一部分属于自己的想法。
考核题目分为四个小题，可以由两个终端来完成。（具体编译过程指令不再展示）
终端一：ros2 launch fishbot_description gazebo_sim.launch.py 启动仿真，可以在里面实现运动控制（键盘控制节点）
终端二：ros2 launch fishbot_navigation2 navigation2.launch.py 实现路径规划与全局避障
