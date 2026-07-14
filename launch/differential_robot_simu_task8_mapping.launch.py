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

    # ── 3. SLAM Toolbox: publishes map->odom, builds the map ──────────────────
    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'odom_frame': 'odom',
            'base_frame': 'base_footprint',
            'map_frame': 'map',
            'scan_topic': '/scan',
        }]
    )

    # ── 4. PD controller node ──────────────────────────────────────────────
    controller_node = Node(
        package='ias0220_idris_py',
        executable='simple_control',
        name='controller',
        output='screen',
        parameters=[config]
    )

    return LaunchDescription([
        gazebo,
        rviz,
        slam,
        controller_node,
    ])
