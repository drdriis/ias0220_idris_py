import os
from pathlib import Path

import cv2
import rclpy
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class ImagePublisher(Node):
    def __init__(self):
        super().__init__("image_publisher")

        package_share = get_package_share_directory("ias0220_idris_py")
        image_dir = os.path.join(package_share, "data", "images")

        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp"}

        image_paths = sorted(
            [
                os.path.join(image_dir, file_name)
                for file_name in os.listdir(image_dir)
                if Path(file_name).suffix.lower() in valid_extensions
            ]
        )

        if not image_paths:
            raise RuntimeError(f"No images found in {image_dir}")

        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, "/image_raw", 10)

        self.images = []

        for image_path in image_paths:
            cv_image = cv2.imread(image_path)

            if cv_image is None:
                self.get_logger().warn(f"Could not read image: {image_path}")
                continue

            self.images.append(cv_image)

        if not self.images:
            raise RuntimeError("No valid images could be loaded")

        self.current_index = 0

        self.timer = self.create_timer(0.5, self.publish_image)

        self.get_logger().info(f"Preloaded {len(self.images)} images")
        self.get_logger().info("Publishing /image_raw at 2 Hz")

    def publish_image(self):
        cv_image = self.images[self.current_index]

        image_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
        image_msg.header.stamp = self.get_clock().now().to_msg()
        image_msg.header.frame_id = "camera"

        self.publisher.publish(image_msg)

        self.current_index = (self.current_index + 1) % len(self.images)


def main(args=None):
    rclpy.init(args=args)

    node = ImagePublisher()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
