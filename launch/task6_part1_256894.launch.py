import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    package_name = "ias0220_idris_py"

    package_share = get_package_share_directory(package_name)

    rviz_config_file = os.path.join(
        package_share,
        "config",
        "task6_part1_256894.rviz"
    )

    image_publisher_node = Node(
        package=package_name,
        executable="image_publisher",
        name="image_publisher",
        output="screen"
    )

    camera_calibration_node = Node(
        package=package_name,
        executable="camera_calibration",
        name="camera_calibration",
        output="screen"
    )

    image_proc_container = ComposableNodeContainer(
        name="image_proc_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        output="screen",
        composable_node_descriptions=[
            ComposableNode(
                package="image_proc",
                plugin="image_proc::RectifyNode",
                name="rectify_node",
                remappings=[
                    ("image", "/image_raw"),
                    ("image_raw", "/image_raw"),
                    ("camera_info", "/camera_info"),
                    ("image_rect", "/image_rect"),
                ],
            ),
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
    )

    return LaunchDescription([
        image_publisher_node,
        camera_calibration_node,
        image_proc_container,
        rviz_node,
    ])
