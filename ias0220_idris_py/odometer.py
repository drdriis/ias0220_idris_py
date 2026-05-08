import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3
from geometry_msgs.msg import Pose
from std_msgs.msg import String

from visualization_msgs.msg import Marker

from rclpy.duration import Duration


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

        # Publisher for walker path markers
        self.marker_publisher = self.create_publisher(
            Marker,
            '/walker_path',
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

        # Unique marker ID counter
        self.counter = 0

        # Marker message
        self.marker_msg = Marker()

        self.marker_msg.header.frame_id = 'map'

        self.marker_msg.type = Marker.SPHERE
        self.marker_msg.action = Marker.ADD

        self.marker_msg.scale.x = 0.5
        self.marker_msg.scale.y = 0.5
        self.marker_msg.scale.z = 0.5

        self.marker_msg.color.a = 0.2
        self.marker_msg.color.r = 1.0
        self.marker_msg.color.g = 0.0
        self.marker_msg.color.b = 0.0

        self.marker_msg.lifetime = Duration(
            seconds=1000
        ).to_msg()

        self.marker_msg.pose.orientation.x = 0.0
        self.marker_msg.pose.orientation.y = 0.0
        self.marker_msg.pose.orientation.z = 0.0
        self.marker_msg.pose.orientation.w = 1.0

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

        # Update marker timestamp
        self.marker_msg.header.stamp = self.get_clock().now().to_msg()

        # Update marker position
        self.marker_msg.pose.position.x = self.pose.position.x
        self.marker_msg.pose.position.y = self.pose.position.y
        self.marker_msg.pose.position.z = self.pose.position.z

        # Assign unique marker ID
        self.marker_msg.id = self.counter

        # Increment counter
        self.counter += 1

        # Publish marker
        self.marker_publisher.publish(self.marker_msg)

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
