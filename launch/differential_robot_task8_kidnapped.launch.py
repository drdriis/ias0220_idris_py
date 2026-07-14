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
        pkg, 'urdf', 'differential_robot_task8.urdf')
    rviz_file = os.path.join(
        pkg, 'config', 'differential_robot_rviz_task8.rviz')
    config = os.path.join(

        pkg, 'config', 'simple_control_v2.yaml')

    map_file = os.path.join(pkg, 'map', 'room.yaml')
    nav2_params = os.path.join(pkg, 'config', 'nav2_params.yaml')

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

    # ── 3. Static transform map -> odom (map_server does not provide it) ──────
    static_transform_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )

    # ── 4. Map server: serves the saved map ───────────────────────────────────
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'use_sim_time': True,
                     'yaml_filename': map_file}]
    )

    # ── 5. AMCL: particle filter localization ─────────────────────────────────
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[nav2_params]
    )

    # ── 6. Lifecycle manager: activates map_server and amcl ───────────────────
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': True,
                     'autostart': True,
                     'node_names': ['map_server', 'amcl']}]
    )
    # ── 7. Teleop keyboard (remapped to the diff drive command topic) ─────────
    teleop = ExecuteProcess(
        cmd=['ros2', 'run', 'teleop_twist_keyboard', 'teleop_twist_keyboard',
             '--ros-args', '-r', '/cmd_vel:=/diff_cont/cmd_vel'],
        output='screen',
        prefix='xterm -e'
    )

    return LaunchDescription([
        gazebo,
        rviz,
        static_transform_publisher,
        map_server,
        amcl,
        lifecycle_manager,
        teleop
    ])
