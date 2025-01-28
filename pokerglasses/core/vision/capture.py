"""
Camera input handling module.
"""
import cv2
import numpy as np
from typing import Optional, Tuple, Generator

class Camera:
    """Handles camera input from smart glasses."""
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.capture = None
        self.is_running = False

    def start(self) -> bool:
        """Start the camera capture."""
        try:
            self.capture = cv2.VideoCapture(self.device_id)
            self.is_running = self.capture.isOpened()
            return self.is_running
        except Exception as e:
            print(f"Failed to start camera: {e}")
            return False

    def stop(self) -> None:
        """Stop the camera capture."""
        if self.capture is not None:
            self.capture.release()
        self.is_running = False

    def get_frame(self) -> Optional[np.ndarray]:
        """Get a single frame from the camera."""
        if not self.is_running:
            return None
        ret, frame = self.capture.read()
        return frame if ret else None

    def stream(self) -> Generator[np.ndarray, None, None]:
        """Stream frames from the camera."""
        while self.is_running:
            frame = self.get_frame()
            if frame is not None:
                yield frame

    def get_resolution(self) -> Tuple[int, int]:
        """Get the camera resolution."""
        if not self.is_running:
            return (0, 0)
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    def set_resolution(self, width: int, height: int) -> bool:
        """Set the camera resolution."""
        if not self.is_running:
            return False
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return True

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 