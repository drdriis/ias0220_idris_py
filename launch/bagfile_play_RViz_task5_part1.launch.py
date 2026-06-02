import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg = get_package_share_directory('ias0220_idris_py')

    rviz_file = os.path.join(
        pkg,
        'config',
        'task5_part1_config.rviz'
    )

    bag_file = os.path.expanduser(
        '~/ros2_ws/src/ias0220_idris_py/bags/bag1'
    )

    bag_play = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'play',
            '-l',
            bag_file
        ],
        output='screen'
    )

    rviz = ExecuteProcess(
        cmd=[
            'rviz2',
            '-d',
            rviz_file
        ],
        output='screen'
    )

    return LaunchDescription([
        bag_play,
        rviz,
    ])
