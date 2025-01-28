"""
Main application entry point.
"""
import sys
from pathlib import Path
from typing import Optional

from pokerglasses.core.vision.capture import Camera
from pokerglasses.core.game.cards import CardDetector
from pokerglasses.utils.config import config
from pokerglasses.hardware.glasses import GlassesDisplay
from pokerglasses.hardware.controls import InputController

class PokerGlassesApp:
    """Main application class."""
    
    def __init__(self):
        self.camera: Optional[Camera] = None
        self.card_detector = CardDetector()
        self.display = GlassesDisplay()
        self.controller = InputController()
        self.running = False

    def setup(self) -> bool:
        """Initialize application components."""
        try:
            # Load configuration
            config.create_default_config()
            
            # Initialize camera
            device_id = config.get('camera.device_id', 0)
            self.camera = Camera(device_id)
            if not self.camera.start():
                print("Failed to initialize camera")
                return False

            # Set up display
            if not self.display.initialize():
                print("Failed to initialize display")
                return False

            # Set up input controller
            if not self.controller.initialize():
                print("Failed to initialize input controller")
                return False

            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False

    def run(self) -> None:
        """Main application loop."""
        if not self.setup():
            sys.exit(1)

        self.running = True
        try:
            while self.running and self.camera:
                # Process input events
                self.controller.process_events()

                # Get camera frame
                frame = self.camera.get_frame()
                if frame is None:
                    continue

                # Detect cards
                cards = self.card_detector.detect_multiple_cards(frame)

                # Update display
                self.display.update(cards)

                # Check for quit condition
                if self.controller.should_quit():
                    self.running = False

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.camera:
            self.camera.stop()
        self.display.shutdown()
        self.controller.shutdown()

def main():
    """Application entry point."""
    app = PokerGlassesApp()
    app.run()

if __name__ == "__main__":
    main() 