import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (IncludeLaunchDescription,
                            RegisterEventHandler, TimerAction)
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    # ----------------------------------------------------------------------
    my_pkg = 'ias0220_idris_py'
    student_code = 'idris_py'
    urdf_rel = 'urdf/differntial_robot_task6_part2.urdf'
    # ----------------------------------------------------------------------

    my_pkg_share = get_package_share_directory(my_pkg)
    mvt_share = get_package_share_directory('machine_vision_part2')

    xacro_path = os.path.join(my_pkg_share, urdf_rel)
    robot_description = xacro.process_file(xacro_path).toxml()

    rviz_config = os.path.join(
        my_pkg_share, 'config', f'task6_part2_{student_code}.rviz')

    # Environment (Gazebo world + target robot). mvt_main does NOT launch RViz.
    mvt_main = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mvt_share, 'launch', 'mvt_main.launch.py')),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True}],
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=['-topic', 'robot_description',
                   '-entity', 'ddrobot_idris',
                   '-x', '0.6', '-y', '-7.5', '-z', '0.0', '-Y', '1.6'],
    )

    object_recognition = Node(
        package=my_pkg,
        executable='object_recognition',
        name='object_recognition',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            # HSV color thresholds for detecting the red object
            'hsv_lower1': [0, 150, 70],
            'hsv_upper1': [5, 255, 255],
            'hsv_lower2': [175, 150, 70],
            'hsv_upper2': [180, 255, 255],
        }],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
    )

    delayed_spawn = RegisterEventHandler(
        OnProcessStart(
            target_action=robot_state_publisher,
            on_start=[TimerAction(period=3.0, actions=[spawn_robot])],
        )
    )

    return LaunchDescription([
        mvt_main,
        robot_state_publisher,
        delayed_spawn,
        object_recognition,
        rviz,
    ])
