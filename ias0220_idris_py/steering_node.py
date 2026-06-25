import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu, Range
from geometry_msgs.msg import Twist

from transforms3d.euler import quat2euler


class SteeringNode(Node):

    def __init__(self):
        super().__init__('steering_node')

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        self.distance = 999.0

        # Tune these if needed
        self.linear_scale = 0.01
        self.angular_scale = 0.02
        self.distance_threshold = 0.30

        self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )

        self.create_subscription(
            Range,
            '/distance',
            self.distance_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # 10 Hz publishing
        self.timer = self.create_timer(
            0.1,
            self.publish_cmd
        )

        self.get_logger().info('Steering node started')

    def imu_callback(self, msg):

        qx = msg.orientation.x
        qy = msg.orientation.y
        qz = msg.orientation.z
        qw = msg.orientation.w

        roll, pitch, yaw = quat2euler(
            [qw, qx, qy, qz]
        )

        self.roll = math.degrees(roll)
        self.pitch = math.degrees(pitch)
        self.yaw = math.degrees(yaw)

    def distance_callback(self, msg):
        self.distance = msg.range

    def publish_cmd(self):

        cmd = Twist()

        if self.distance > self.distance_threshold:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        else:
            cmd.linear.x = self.pitch * self.linear_scale
            cmd.angular.z = self.roll * self.angular_scale

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    node = SteeringNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
