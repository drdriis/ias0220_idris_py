import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def generate_launch_description():

    # ── Paths ──────────────────────────────────────────────────────────────
    pkg = get_package_share_directory('ias0220_idris_py')
    gazebo_pkg = get_package_share_directory('setup_gazebo_ias0220')

    urdf_file = os.path.join(
        pkg, 'urdf', 'differential_robot_simu_task4_part2.urdf')
    rviz_file = os.path.join(pkg, 'config', 'task4_part2_config.rviz')

    # ── 1. Gazebo + robot_state_publisher + spawn ──────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_pkg, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'xacro_file': urdf_file}.items()
    )

    # ── 2. RViz ────────────────────────────────────────────────────────────
    rviz = ExecuteProcess(
        cmd=[
            'rviz2', '-d', rviz_file,
            '--ros-args', '-p', 'use_sim_time:=true'
        ],
        output='screen'
    )

    # ── 3. Teleop keyboard ─────────────────────────────────────────────────
    teleop = ExecuteProcess(
        cmd=['ros2', 'run', 'teleop_twist_keyboard', 'teleop_twist_keyboard'],
        output='screen',
        prefix='xterm -e'
    )

    # ── 4. rqt_graph ───────────────────────────────────────────────────────
    rqt = ExecuteProcess(
        cmd=['rqt_graph'],
        output='screen'
    )

    # ── 5. Encoder node ────────────────────────────────────────────────────
    encoder_node = Node(
        package='encoders_pkg',
        executable='encoders_node',
        name='encoders_node',
        output='screen'
    )

    # ── 6. Static transform publisher: map -> odom ─────────────────────────
    static_transform_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )

    # ── 7. Odometry node ───────────────────────────────────────────────────
    odometry_node = Node(
        package='ias0220_idris_py',
        executable='odometry',
        name='odometry_node',
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        rviz,
        teleop,
        rqt,
        encoder_node,
        static_transform_publisher,
        odometry_node,
    ])
