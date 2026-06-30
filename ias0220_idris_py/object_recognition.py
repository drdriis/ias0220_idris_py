#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


class ObjectRecognition(Node):
    def __init__(self):
        super().__init__('object_recognition')

        # Red wraps around the hue circle, so two bands. OpenCV hue is 0-179.
        self.declare_parameter('hsv_lower1', [0, 120, 70])
        self.declare_parameter('hsv_upper1', [10, 255, 255])
        self.declare_parameter('hsv_lower2', [170, 120, 70])
        self.declare_parameter('hsv_upper2', [180, 255, 255])
        self.declare_parameter('min_area', 150.0)
        self.declare_parameter('publish_mask', True)
        self.declare_parameter('draw_path', True)
        self.declare_parameter('max_path_points', 3000)

        self.bridge = CvBridge()
        self.path = []

        self.sub = self.create_subscription(
            Image, '/camera1/image_raw', self.image_callback, 10)
        self.pub_img = self.create_publisher(
            Image, '/object_recognition/image', 10)
        self.pub_mask = self.create_publisher(
            Image, '/object_recognition/mask', 10)

        self.get_logger().info('object_recognition node started.')

    def _bound(self, name):
        return np.array(self.get_parameter(name).value, dtype=np.uint8)

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'cv_bridge conversion failed: {e}')
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask1 = cv2.inRange(hsv, self._bound('hsv_lower1'),
                            self._bound('hsv_upper1'))
        mask2 = cv2.inRange(hsv, self._bound('hsv_lower2'),
                            self._bound('hsv_upper2'))
        mask = cv2.bitwise_or(mask1, mask2)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = self.get_parameter('min_area').value
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) >= min_area:
                (x, y), radius = cv2.minEnclosingCircle(largest)
                center = (int(x), int(y))
                cv2.circle(frame, center, int(radius), (0, 255, 0), 2)
                cv2.circle(frame, center, 3, (0, 255, 0), -1)
                cv2.putText(frame, 'ddrobot',
                            (center[0] - 30, center[1] - int(radius) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                if self.get_parameter('draw_path').value:
                    self.path.append(center)
                    max_pts = self.get_parameter('max_path_points').value
                    if len(self.path) > max_pts:
                        self.path = self.path[-max_pts:]

        if self.get_parameter('draw_path').value and len(self.path) > 1:
            cv2.polylines(frame, [np.array(self.path, dtype=np.int32)],
                          isClosed=False, color=(255, 0, 0), thickness=2)

        out = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        out.header = msg.header
        self.pub_img.publish(out)

        if self.get_parameter('publish_mask').value:
            mask_msg = self.bridge.cv2_to_imgmsg(mask, encoding='mono8')
            mask_msg.header = msg.header
            self.pub_mask.publish(mask_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ObjectRecognition()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
