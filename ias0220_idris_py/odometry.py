import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from encoders_interfaces.msg import Counter
import transforms3d
import math


class PositionCalculator(Node):

    def __init__(self):
        super().__init__('position_calculator')

        # ── Robot parameters ───────────────────────────────────────────────
        self.cpr = 508.8           # counts per revolution
        self.wheel_radius = 0.036  # metres
        self.wheel_separation = 0.350  # metres (2 * wheel_y_offset)

        # ── State variables ────────────────────────────────────────────────
        self.prev_count_left = None
        self.prev_count_right = None
        self.prev_time = None

        # Accumulated wheel angles in radians
        self.angle_left = 0.0
        self.angle_right = 0.0

        # Robot pose (x, y, theta)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # ── Odometry message ───────────────────────────────────────────────
        self.odom_msg = Odometry()
        self.odom_msg.header.frame_id = 'odom'
        self.odom_msg.child_frame_id = 'base_link'

        # ── Publisher ──────────────────────────────────────────────────────
        self.odom_publisher = self.create_publisher(
            Odometry, '/my_odom', 10)

        # ── Subscriber ────────────────────────────────────────────────────
        self.encoder_subscription = self.create_subscription(
            Counter,
            '/encoders_ticks',
            self.encoder_callback,
            10
        )

        self.get_logger().info('Odometry node started.')

    def encoder_callback(self, msg):

        current_time = self.get_clock().now()

        count_left = msg.count_left
        count_right = msg.count_right

        # ── First message: initialise and return ───────────────────────────
        if self.prev_count_left is None:
            self.prev_count_left = count_left
            self.prev_count_right = count_right
            self.prev_time = current_time
            return

        # ── Time delta ────────────────────────────────────────────────────
        dt = (current_time - self.prev_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        # ── Tick deltas with wrap-around handling ──────────────────────────
        # Encoder counts go 0 -> CPR -> 0, handle the wrap
        delta_left = self._delta_ticks(count_left, self.prev_count_left)
        delta_right = self._delta_ticks(count_right, self.prev_count_right)

        # ── Convert tick deltas to wheel angle deltas (radians) ────────────
        delta_angle_left = (delta_left / self.cpr) * 2.0 * math.pi
        delta_angle_right = (-delta_right / self.cpr) * 2.0 * math.pi

        # ── Convert wheel angles to distances ─────────────────────────────
        dist_left = delta_angle_left * self.wheel_radius
        dist_right = delta_angle_right * self.wheel_radius

        # ── Robot displacement and heading change ──────────────────────────
        d = (dist_left + dist_right) / 2.0
        delta_theta = (dist_right - dist_left) / self.wheel_separation

        # ── Update pose using lecture formula ──────────────────────────────
        self.x += d * math.cos(self.theta + delta_theta / 2.0)
        self.y += d * math.sin(self.theta + delta_theta / 2.0)
        self.theta += delta_theta

        # ── Velocities ────────────────────────────────────────────────────
        linear_vel = d / dt
        angular_vel = delta_theta / dt

        # ── Convert theta to quaternion ───────────────────────────────────
        # transforms3d returns (w, x, y, z)
        q = transforms3d.euler.euler2quat(0.0, 0.0, self.theta, axes='sxyz')

        # ── Fill and publish odometry message ─────────────────────────────
        self.odom_msg.header.stamp = current_time.to_msg()

        self.odom_msg.pose.pose.position.x = self.x
        self.odom_msg.pose.pose.position.y = self.y
        self.odom_msg.pose.pose.position.z = 0.0

        self.odom_msg.pose.pose.orientation.w = q[0]
        self.odom_msg.pose.pose.orientation.x = q[1]
        self.odom_msg.pose.pose.orientation.y = q[2]
        self.odom_msg.pose.pose.orientation.z = q[3]

        self.odom_msg.twist.twist.linear.x = linear_vel
        self.odom_msg.twist.twist.linear.y = 0.0
        self.odom_msg.twist.twist.angular.z = angular_vel

        self.odom_publisher.publish(self.odom_msg)

        # ── Update previous values ────────────────────────────────────────
        self.prev_count_left = count_left
        self.prev_count_right = count_right
        self.prev_time = current_time

    def _delta_ticks(self, current, previous):
        """
        Compute signed tick delta handling wrap-around at CPR boundary.
        Encoder counts are absolute (0 to CPR), wrapping back to 0.
        """
        delta = float(current - previous)
        half_cpr = self.cpr / 2.0
        if delta > half_cpr:
            delta -= self.cpr
        elif delta < -half_cpr:
            delta += self.cpr
        return delta


def main(args=None):
    rclpy.init(args=args)
    node = PositionCalculator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
