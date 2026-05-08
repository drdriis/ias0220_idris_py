import random
import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3
from std_msgs.msg import String


class RandomWalker(Node):

    def __init__(self):
        super().__init__('walker')

        # Publisher for velocity
        self.velocity_publisher = self.create_publisher(
            Vector3,
            '/velocity',
            10
        )

        # Publisher for ID and timestamp
        self.name_time_publisher = self.create_publisher(
            String,
            '/name_and_time',
            10
        )

        # Timer running at 2 Hz (0.5 seconds)
        self.timer = self.create_timer(0.5, self.timer_callback)

        self.student_id = "256894"

    def timer_callback(self):

        # Generate random velocity values
        velocity_msg = Vector3()

        velocity_msg.x = float(random.choice([-1, 0, 1]))
        velocity_msg.y = float(random.choice([-1, 0, 1]))
        velocity_msg.z = 0.0

        # Publish velocity
        self.velocity_publisher.publish(velocity_msg)

        # Print velocity information
        self.get_logger().info(
            f'I will move with this velocity for 0.5 seconds:\n'
            f'x: {velocity_msg.x}\n'
            f'y: {velocity_msg.y}\n'
            f'z: {velocity_msg.z}'
        )

        # Create ID and timestamp message
        current_time = time.time()

        name_time_msg = String()
        name_time_msg.data = f'{self.student_id},{current_time}'

        # Publish ID and timestamp
        self.name_time_publisher.publish(name_time_msg)

        # Print ID and timestamp information
        self.get_logger().info(
            f'Hello, these are my ID and the current time:\n'
            f'{name_time_msg.data}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = RandomWalker()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
