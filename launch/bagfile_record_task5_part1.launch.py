from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():

    imu_static_transform = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[
            "--frame-id", "map",
            "--child-frame-id", "imu_link"
        ]
    )

    sensors_interface = Node(
        package='ias0220_sensors',
        executable='serial_interface',
        name='sensors',
        output='screen',
        parameters=[
            {'serial_port': '/dev/ttyUSB0'}
        ]
    )

    bag_record = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-a',
            '-o',
            '/home/drdriis/ros2_ws/src/ias0220_idris_py/bags/recorded'
        ],
        output='screen'
    )

    return LaunchDescription([
        imu_static_transform,
        sensors_interface,
        bag_record
    ])
