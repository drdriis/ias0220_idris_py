import cv2
import numpy as np
import rclpy

from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo


class CameraCalibration(Node):
    def __init__(self):
        super().__init__("camera_calibration")

        self.subscription = self.create_subscription(
            Image,
            "/image_raw",
            self.image_callback,
            10
        )

        self.processed_publisher = self.create_publisher(
            Image,
            "/image_processed",
            10
        )

        self.camera_info_publisher = self.create_publisher(
            CameraInfo,
            "/camera_info",
            10
        )

        self.bridge = CvBridge()

        # IMPORTANT:
        # This is the number of INNER chessboard corners.
        # Change this if your calibration board is different.
        self.chessboard_size = (7, 6)

        self.required_images = 37
        self.state = "collecting"

        self.object_points = []
        self.image_points = []

        self.camera_matrix = None
        self.dist_coeffs = None
        self.image_size = None

        self.criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.001
        )

        self.objp = np.zeros(
            (self.chessboard_size[0] * self.chessboard_size[1], 3),
            np.float32
        )

        self.objp[:, :2] = np.mgrid[
            0:self.chessboard_size[0],
            0:self.chessboard_size[1]
        ].T.reshape(-1, 2)

        self.get_logger().info("camera_calibration node started")

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding="bgr8"
        )

        if self.state == "collecting":
            self.collect_calibration_image(cv_image, msg)

            if len(self.object_points) >= self.required_images:
                self.calibrate_camera()

        elif self.state == "calibrated":
            camera_info_msg = self.create_camera_info_msg(msg)
            self.camera_info_publisher.publish(camera_info_msg)

    def collect_calibration_image(self, cv_image, msg):
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # OpenCV uses image size as (width, height)
        self.image_size = gray.shape[::-1]

        found, corners = cv2.findChessboardCorners(
            gray,
            self.chessboard_size,
            None
        )

        display_image = cv_image.copy()

        if found:
            refined_corners = cv2.cornerSubPix(
                gray,
                corners,
                (11, 11),
                (-1, -1),
                self.criteria
            )

            self.object_points.append(self.objp)
            self.image_points.append(refined_corners)

            cv2.drawChessboardCorners(
                display_image,
                self.chessboard_size,
                refined_corners,
                found
            )

            self.get_logger().info(
                f"Collected image{len(self.object_points)}/{self.required_images}"
            )
        else:
            self.get_logger().warn("Chessboard not found")

        processed_msg = self.bridge.cv2_to_imgmsg(
            display_image,
            encoding="bgr8"
        )

        processed_msg.header = msg.header
        self.processed_publisher.publish(processed_msg)

    def calibrate_camera(self):
        self.get_logger().info("Starting camera calibration...")

        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            self.object_points,
            self.image_points,
            self.image_size,
            None,
            None
        )

        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs

        total_error = 0

        for i in range(len(self.object_points)):
            projected_points, _ = cv2.projectPoints(
                self.object_points[i],
                rvecs[i],
                tvecs[i],
                self.camera_matrix,
                self.dist_coeffs
            )

            error = cv2.norm(
                self.image_points[i],
                projected_points,
                cv2.NORM_L2
            ) / len(projected_points)

            total_error += error

        average_error = total_error / len(self.object_points)

        self.get_logger().info("Calibration finished")
        self.get_logger().info(f"OpenCV RMS error: {ret}")
        self.get_logger().info(f"Average reprojection error: {average_error}")

        self.state = "calibrated"

    def create_camera_info_msg(self, image_msg):
        camera_info_msg = CameraInfo()

        camera_info_msg.header = image_msg.header
        camera_info_msg.height = image_msg.height
        camera_info_msg.width = image_msg.width

        camera_info_msg.distortion_model = "plumb_bob"

        camera_info_msg.d = self.dist_coeffs.flatten().tolist()
        camera_info_msg.k = self.camera_matrix.flatten().tolist()

        r_matrix = np.eye(3)
        camera_info_msg.r = r_matrix.flatten().tolist()

        p_matrix = np.zeros((3, 4))
        p_matrix[:3, :3] = self.camera_matrix
        camera_info_msg.p = p_matrix.flatten().tolist()

        return camera_info_msg


def main(args=None):
    rclpy.init(args=args)

    node = CameraCalibration()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
