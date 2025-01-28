"""
Camera input handling module.

This module provides camera capture functionality for the smart glasses,
including frame capture, streaming, and resolution management.
"""
import cv2
import numpy as np
from typing import Optional, Tuple, Generator
from dataclasses import dataclass
from enum import Enum

class CameraError(Exception):
    """Base exception for camera-related errors."""
    pass

class CameraInitError(CameraError):
    """Raised when camera initialization fails."""
    pass

class CameraNotRunningError(CameraError):
    """Raised when trying to use a camera that isn't running."""
    pass

@dataclass
class Resolution:
    """Camera resolution configuration."""
    width: int
    height: int

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"

class CameraMode(Enum):
    """Camera operation modes."""
    PREVIEW = "preview"  # Lower resolution, higher FPS
    CAPTURE = "capture"  # Higher resolution, lower FPS
    DETECTION = "detection"  # Optimized for card detection

class Camera:
    """
    Handles camera input from smart glasses.
    
    This class manages camera initialization, frame capture, and streaming.
    It provides error handling and various camera configuration options.
    """
    def __init__(self, device_id: int = 0, mode: CameraMode = CameraMode.DETECTION):
        """
        Initialize the camera.
        
        Args:
            device_id: Camera device identifier
            mode: Camera operation mode
            
        Raises:
            CameraInitError: If camera initialization fails
        """
        self.device_id = device_id
        self.mode = mode
        self.capture = None
        self.is_running = False
        self._default_resolutions = {
            CameraMode.PREVIEW: Resolution(640, 480),
            CameraMode.CAPTURE: Resolution(1920, 1080),
            CameraMode.DETECTION: Resolution(1280, 720)
        }

    def start(self) -> bool:
        """
        Start the camera capture.
        
        Returns:
            bool: True if camera started successfully
            
        Raises:
            CameraInitError: If camera fails to initialize
        """
        try:
            self.capture = cv2.VideoCapture(self.device_id)
            if not self.capture.isOpened():
                raise CameraInitError(f"Failed to open camera device {self.device_id}")
            
            # Set default resolution for the mode
            resolution = self._default_resolutions[self.mode]
            self.set_resolution(resolution.width, resolution.height)
            
            self.is_running = True
            return True
            
        except Exception as e:
            raise CameraInitError(f"Camera initialization failed: {str(e)}")

    def stop(self) -> None:
        """
        Stop the camera capture and release resources.
        """
        if self.capture is not None:
            self.capture.release()
        self.is_running = False

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera.
        
        Returns:
            Optional[np.ndarray]: Camera frame or None if capture fails
            
        Raises:
            CameraNotRunningError: If camera is not running
        """
        if not self.is_running:
            raise CameraNotRunningError("Camera is not running")
        
        ret, frame = self.capture.read()
        if not ret:
            return None
            
        return self._process_frame(frame)

    def stream(self) -> Generator[np.ndarray, None, None]:
        """
        Stream frames from the camera.
        
        Yields:
            np.ndarray: Camera frames
            
        Raises:
            CameraNotRunningError: If camera is not running
        """
        if not self.is_running:
            raise CameraNotRunningError("Camera is not running")
            
        while self.is_running:
            frame = self.get_frame()
            if frame is not None:
                yield frame

    def get_resolution(self) -> Resolution:
        """
        Get the current camera resolution.
        
        Returns:
            Resolution: Current width and height
            
        Raises:
            CameraNotRunningError: If camera is not running
        """
        if not self.is_running:
            raise CameraNotRunningError("Camera is not running")
            
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return Resolution(width, height)

    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set the camera resolution.
        
        Args:
            width: Desired frame width
            height: Desired frame height
            
        Returns:
            bool: True if resolution was set successfully
            
        Raises:
            CameraNotRunningError: If camera is not running
        """
        if not self.is_running:
            raise CameraNotRunningError("Camera is not running")
            
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Verify the resolution was set
        actual = self.get_resolution()
        return actual.width == width and actual.height == height

    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process the captured frame based on the camera mode.
        
        Args:
            frame: Raw camera frame
            
        Returns:
            np.ndarray: Processed frame
        """
        # Apply mode-specific processing
        if self.mode == CameraMode.DETECTION:
            # Optimize for card detection
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
        
        return frame

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 