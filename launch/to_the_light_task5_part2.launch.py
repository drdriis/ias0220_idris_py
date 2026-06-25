import os

from launch import LaunchDescription
from launch.actions import (IncludeLaunchDescription,
                            ExecuteProcess,
                            TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg = get_package_share_directory('ias0220_idris_py')
    gazebo_pkg = get_package_share_directory('setup_gazebo_ias0220')

    urdf_file = os.path.join(
        pkg,
        'urdf',
        'differential_robot_simu_task4_part1.urdf'
    )

    rviz_file = os.path.join(
        pkg,
        'config',
        'task4_part1_config.rviz'
    )

    bag_file = os.path.expanduser(
        '~/ros2_ws/src/ias0220_idris_py/bags/rosbag_to_light'
    )

    # Gazebo (loads seethelight.world by default)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                gazebo_pkg,
                'launch',
                'gazebo.launch.py'
            )
        ),
        launch_arguments={
            'xacro_file': urdf_file
        }.items()
    )

    # RViz
    rviz = ExecuteProcess(
        cmd=[
            'rviz2',
            '-d',
            rviz_file,
            '--ros-args',
            '-p',
            'use_sim_time:=true'
        ],
        output='screen'
    )

    # Replay the recorded bag
    bag_play = ExecuteProcess(
        cmd=[
            'ros2',
            'bag',
            'play',
            bag_file,
            '--topics',
            '/cmd_vel'
        ],
        output='screen'
    )

    # Delay playback so Gazebo has time to spawn the robot
    delayed_bag_play = TimerAction(
        period=10.0,
        actions=[bag_play]
    )

    return LaunchDescription([
        gazebo,
        rviz,
        delayed_bag_play,
    ])
