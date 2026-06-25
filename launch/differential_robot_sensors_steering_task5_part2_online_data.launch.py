import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

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

    sensors = Node(
        package='ias0220_sensors',
        executable='serial_interface',
        name='sensors',
        output='screen',
        parameters=[
            {'serial_port': '/dev/ttyUSB0'}
        ]
    )

    steering = Node(
        package='ias0220_idris_py',
        executable='steering_node',
        name='steering_node',
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        rviz,
        sensors,
        steering,
    ])
