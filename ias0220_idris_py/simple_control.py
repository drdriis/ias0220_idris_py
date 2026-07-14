import math
import rclpy
import time
from rclpy.node import Node
from rclpy.time import Duration, Time
import numpy as np
from geometry_msgs.msg import Twist, PoseStamped, Point
from visualization_msgs.msg import Marker
from nav_msgs.msg import Odometry
from tf_transformations import euler_from_quaternion
from tf2_ros import Buffer, TransformListener


class PDController(Node):
    def __init__(self):
        super().__init__('controller')

        # Wait for run other nodes
        time.sleep(5)

        # tf2: to obtain the robot pose in the map frame (SLAM-corrected)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # variables for error change rate calculation
        self.start_time = self.get_clock().now()
        self.last_odom_time = self.get_clock().now()

        self.sub_odom = self.create_subscription(
            Odometry, '/diff_cont/odom', self.onOdom, 10)

        self.vel_cmd_pub = self.create_publisher(
            Twist, '/diff_cont/cmd_vel', 10)
        self.pub_viz = self.create_publisher(Marker, "waypoints", 10)

        self.marker_frame = "map"

        self.vel_cmd_msg = Twist()
        self.vel_cmd = np.array([0.0, 0.0])

        self.pos = np.array([0.0, 0.0])
        self.pos_diff = np.array([0.0, 0.0])
        self.theta = 0.0
        self.th_diff = 0.0

        self.error = np.array([0.0, 0.0])

        self.error_change_rate = np.array([0.0, 0.0])

        # Load params from parameter server
        self.waypoints = []
        self.waypoints_x = []
        self.waypoints_y = []
        read_waypoints_x = self.declare_parameter('waypoints_x', [0.0]).value
        read_waypoints_y = self.declare_parameter('waypoints_y', [0.0]).value
        self.Kp = np.array(self.declare_parameter('Kp', [0.0, 0.0]).value)
        self.Kd = np.array(self.declare_parameter('Kd', [0.0, 0.0]).value)

        # Identify the waypoints parameter is correcly load or not
        if (read_waypoints_x == [0.0]) and (read_waypoints_y == [0.0]):
            self.get_logger().error("!!!!!!!!!!!!!!ERROR!!!!!!!!!!!!!!")
            self.get_logger().error("Parameters not loaded correctly")
            self.get_logger().error("Please check your launch file to load yaml file correctly")
            self.get_logger().error("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        if (read_waypoints_x) and (read_waypoints_y):
            for i in range(len(read_waypoints_x)):
                self.waypoints.append(
                    [read_waypoints_x[i], read_waypoints_y[i]])
        self.waypoints = np.array(self.waypoints)

        self.distance_margin = self.declare_parameter(
            'distance_margin', 0.05).value
        self.target_angle = self.wrapAngle(self.declare_parameter(
            'target_angle', 0.0).value)

        # Check Params
        self.get_logger().info(f'Waypoints: \n {self.waypoints}')
        self.get_logger().info(f'Kp: {self.Kp}')
        self.get_logger().info(f'Kd: {self.Kd}')
        self.get_logger().info(f'Start Time: {self.start_time}')

    def wrapAngle(self, angle):
        """
        Helper function that returns angle wrapped between +- Pi.
        @param: self
        @param: angle - angle to be wrapped in [rad]
        @result: returns wrapped angle -Pi <= angle <= Pi
        """
        return np.arctan2(np.sin(angle), np.cos(angle))

    def control(self):
        """
        Takes the errors and calculates velocities from it, according to
        PD control algorithm.
        @param: self (errors got using "calculateError" function)
        @result: sets the values in self.vel_cmd
        """
        # PD law, element-wise: index 0 = linear, index 1 = angular
        # v = Kp_lin * e_pos + Kd_lin * e'_pos
        # w = Kp_ang * e_th  + Kd_ang * e'_th
        self.vel_cmd = self.Kp * self.error + self.Kd * self.error_change_rate

        # Gate linear velocity by heading error: don't drive fast while
        # pointing away from the target (prevents large overshooting arcs).
        # cos(0) = 1 -> full speed when aligned; <= 0 -> turn in place.
        self.vel_cmd[0] *= max(0.0, np.cos(self.th_diff))

        # Saturate commands to physically sensible limits [v_max, w_max]
        limits = np.array([0.5, 2.0])
        self.vel_cmd = np.clip(self.vel_cmd, -limits, limits)

    def publishWaypoints(self):
        """
        Publishes the list of waypoints, so RViz can see them.
        @param: self
        @result: publish message
        """
        marker = Marker()
        marker.header.frame_id = self.marker_frame

        marker.type = marker.SPHERE_LIST
        marker.action = marker.ADD

        marker.scale.x = self.distance_margin
        marker.scale.y = self.distance_margin
        marker.scale.z = self.distance_margin
        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 0.0

        marker.pose.orientation.w = 1.0

        marker.points = [Point(x=waypoint[0], y=waypoint[1])
                         for waypoint in self.waypoints]

        self.pub_viz.publish(marker)

    def calculateError(self):
        """
        Calculate lateral error to first waypoint and heading error between
        line to waypoint and robot heading.
        @param: self
        @result: updates self.error, self.error_change_rate, self.th_diff and
                 self.pos_diff
        """
        # No waypoints left: zero everything so control() outputs zero
        if self.waypoints.size == 0:
            self.error = np.array([0.0, 0.0])
            self.error_change_rate = np.array([0.0, 0.0])
            return

        target = self.waypoints[0]
        self.pos_diff = target - self.pos  # [dx, dy] to current waypoint

        # Position error: Euclidean distance to waypoint
        e_pos = np.linalg.norm(self.pos_diff)

        # Heading error: desired heading (atan2) minus current, wrapped
        theta_goal = np.arctan2(self.pos_diff[1], self.pos_diff[0])
        self.th_diff = self.wrapAngle(theta_goal - self.theta)

        new_error = np.array([e_pos, self.th_diff])

        # Error change rate for the D term.
        # Reject degenerate dt (< 1 ms): near-coincident odom stamps make
        # the finite difference blow up.
        if hasattr(self, 'dt') and self.dt > 1e-3:
            self.error_change_rate = (new_error - self.error) / self.dt
        else:
            self.error_change_rate = np.array([0.0, 0.0])

        self.error = new_error

    def isWaypointReached(self):
        """
        check if waypoint is reached based on user define threshold
        @param: self
        @result: if waypoint is reached that waypoint is popped from
                 waypoint list and True is returned,
                 otherwise False is returned.
        """

        if self.waypoints.size != 0:
            if (self.error[0] < self.distance_margin):
                self.waypoints = np.delete(self.waypoints, 0, axis=0)
                return True

        return False

    def onOdom(self, odom_msg):
        """
        Handles incoming odometry updates (callback function).
        @param: self
        @param odom_msg - odometry geometry message
        @result: update of relevant vehicle state variables
        """

        # Robot pose in the map frame (SLAM-corrected), instead of raw odom
        try:
            tf = self.tf_buffer.lookup_transform(
                'map', 'base_footprint', rclpy.time.Time())
            self.pos[0] = tf.transform.translation.x
            self.pos[1] = tf.transform.translation.y
            q = tf.transform.rotation
            self.theta = euler_from_quaternion([q.x, q.y, q.z, q.w])[2]
        except Exception:
            # map->odom not yet available (SLAM starting up): skip this cycle
            return

        now_odom_time = rclpy.time.Time.from_msg(odom_msg.header.stamp)

        dt_tmp = (now_odom_time - self.last_odom_time).to_msg()
        self.dt = float(dt_tmp.sec + dt_tmp.nanosec/1e9)
        self.last_odom_time = now_odom_time

        # Calculate error between current pose and next waypoint position
        self.calculateError()

        # Check reaching waypoint or not
        if self.isWaypointReached():
            self.get_logger().info(
                "Reached waypoint!\nFuture waypoint list: "
                + str(self.waypoints))
            self.calculateError()  # Update error with new target waypoint

        # Calculate velocity command using PID control
        self.control()

        # publish velocity commands
        self.vel_cmd_msg.linear.x = self.vel_cmd[0]
        self.vel_cmd_msg.angular.z = self.vel_cmd[1]
        self.vel_cmd_pub.publish(self.vel_cmd_msg)

        # Publish waypoints visualization
        self.publishWaypoints()


def main(args=None):
    rclpy.init(args=args)
    controller = PDController()
    rclpy.spin(controller)


if __name__ == "__main__":
    main()
