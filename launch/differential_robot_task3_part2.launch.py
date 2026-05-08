import os
from typing import Any

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    # Package name
    package_name = "ias0220_idris_py"

    # Package path
    package_path = get_package_share_directory(package_name)

    # URDF path
    urdf_file = os.path.join(
        package_path,
        "urdf",
        "differential_robot.urdf",
    )

    # RViz config path
    rviz_config_file = os.path.join(
        package_path,
        "config",
        "task3_part2_config.rviz",
    )

    # Process URDF/xacro
    robot_description_config: Any = xacro.process_file(urdf_file)

    robot_description = {
        "robot_description": robot_description_config.toxml()
    }

    # Robot State Publisher node
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    # Joint State Publisher node
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
    )

    # RViz node
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
    )

    # Move node
    move_node = Node(
        package="transform_frame",
        executable="move",
        name="move",
        output="screen",
    )

    # Teleop keyboard node
    teleop_node = Node(
        package="teleop_twist_keyboard",
        executable="teleop_twist_keyboard",
        name="teleop_twist_keyboard",
        output="screen",
        prefix="xterm -e",
        remappings=[
            ("/cmd_vel", "/move/cmd_vel"),
        ],
    )

    return LaunchDescription(
        [
            robot_state_publisher_node,
            joint_state_publisher_node,
            rviz_node,
            move_node,
            teleop_node,
        ]
    )
