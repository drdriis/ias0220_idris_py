import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3
from geometry_msgs.msg import Pose
from std_msgs.msg import String


class PositionCalculator(Node):

    def __init__(self):
        super().__init__('position_calculator')

        # Subscribe to velocity topic
        self.velocity_subscription = self.create_subscription(
            Vector3,
            '/velocity',
            self.velocity_callback,
            10
        )

        # Subscribe to name_and_time topic
        self.name_time_subscription = self.create_subscription(
            String,
            '/name_and_time',
            self.name_time_callback,
            10
        )

        # Pose object to store position
        self.pose = Pose()

        # Initial position
        self.pose.position.x = 0.0
        self.pose.position.y = 0.0
        self.pose.position.z = 0.0

        # Time interval (2 Hz -> 0.5 seconds)
        self.dt = 0.5

    def name_time_callback(self, msg):

        # Split incoming message
        student_id, timestamp = msg.data.split(',')

        # Display formatted message
        self.get_logger().info(
            f'Student {student_id} contacted me, '
            f'and told me that current time is: {timestamp}'
        )

    def velocity_callback(self, msg):

        # Compute displacement
        delta_x = msg.x * self.dt
        delta_y = msg.y * self.dt

        # Update position
        self.pose.position.x += delta_x
        self.pose.position.y += delta_y

        # z always remains 0
        self.pose.position.z = 0.0

        # Display updated position
        self.get_logger().info(
            f'The new position of the walker is:\n'
            f'x = {self.pose.position.x}\n'
            f'y = {self.pose.position.y}\n'
            f'z = {self.pose.position.z}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = PositionCalculator()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
