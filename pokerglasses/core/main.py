"""
Main application entry point.

This module contains the main application class and entry point for the
PokerGlasses application, handling initialization, main loop, and cleanup.
"""
import sys
import logging
from pathlib import Path
from typing import Optional, List

from pokerglasses.core.vision.capture import Camera, CameraError, CameraMode
from pokerglasses.core.game.cards import CardDetector, Card
from pokerglasses.utils.config import config
from pokerglasses.hardware.glasses import GlassesDisplay
from pokerglasses.hardware.controls import InputController

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base exception for application-related errors."""
    pass

class InitializationError(ApplicationError):
    """Raised when application initialization fails."""
    pass

class PokerGlassesApp:
    """
    Main application class for PokerGlasses.
    
    This class coordinates all components of the application, including:
    - Camera input and card detection
    - Display output
    - User input handling
    - Application state management
    """
    
    def __init__(self):
        """Initialize application components."""
        self.camera: Optional[Camera] = None
        self.card_detector = CardDetector(
            confidence_threshold=config.get('ml.confidence_threshold', 0.85)
        )
        self.display = GlassesDisplay()
        self.controller = InputController()
        self.running = False
        self.detected_cards: List[Card] = []

    def setup(self) -> bool:
        """
        Initialize application components.
        
        Returns:
            bool: True if setup was successful
            
        Raises:
            InitializationError: If any component fails to initialize
        """
        try:
            logger.info("Starting application setup...")
            
            # Load configuration
            config.create_default_config()
            logger.info("Configuration loaded")
            
            # Initialize camera
            device_id = config.get('camera.device_id', 0)
            self.camera = Camera(
                device_id=device_id,
                mode=CameraMode.DETECTION
            )
            if not self.camera.start():
                raise InitializationError("Failed to initialize camera")
            logger.info("Camera initialized")

            # Set up display
            if not self.display.initialize():
                raise InitializationError("Failed to initialize display")
            logger.info("Display initialized")

            # Set up input controller
            if not self.controller.initialize():
                raise InitializationError("Failed to initialize input controller")
            logger.info("Input controller initialized")

            logger.info("Application setup completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Setup failed: {str(e)}"
            logger.error(error_msg)
            raise InitializationError(error_msg) from e

    def run(self) -> None:
        """
        Main application loop.
        
        This method handles the main application flow, including:
        - Processing user input
        - Capturing and analyzing frames
        - Updating the display
        - Error handling and recovery
        """
        try:
            if not self.setup():
                logger.error("Application setup failed")
                sys.exit(1)

            logger.info("Starting main application loop")
            self.running = True
            
            while self.running and self.camera:
                try:
                    # Process input events
                    self.controller.process_events()

                    # Get camera frame
                    frame = self.camera.get_frame()
                    if frame is None:
                        logger.warning("Failed to capture frame")
                        continue

                    # Detect cards
                    self.detected_cards = self.card_detector.detect_multiple_cards(frame)
                    
                    if self.detected_cards:
                        logger.debug(f"Detected cards: {[str(card) for card in self.detected_cards]}")

                    # Update display
                    self.display.update(self.detected_cards)

                    # Check for quit condition
                    if self.controller.should_quit():
                        logger.info("Quit signal received")
                        self.running = False

                except CameraError as e:
                    logger.error(f"Camera error: {e}")
                    self.handle_camera_error()
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    # Continue running but log the error

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Critical error: {e}")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources and perform shutdown tasks."""
        logger.info("Starting cleanup...")
        
        if self.camera:
            try:
                self.camera.stop()
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")

        try:
            self.display.shutdown()
            logger.info("Display shut down")
        except Exception as e:
            logger.error(f"Error shutting down display: {e}")

        try:
            self.controller.shutdown()
            logger.info("Input controller shut down")
        except Exception as e:
            logger.error(f"Error shutting down input controller: {e}")

        logger.info("Cleanup completed")

    def handle_camera_error(self) -> None:
        """Handle camera errors with potential recovery."""
        try:
            if self.camera:
                logger.info("Attempting to restart camera...")
                self.camera.stop()
                if self.camera.start():
                    logger.info("Camera restarted successfully")
                else:
                    logger.error("Failed to restart camera")
        except Exception as e:
            logger.error(f"Error during camera recovery: {e}")

def main():
    """Application entry point."""
    try:
        logger.info("Starting PokerGlasses application")
        app = PokerGlassesApp()
        app.run()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 