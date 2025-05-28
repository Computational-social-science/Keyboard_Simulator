import sys
import json # Added for JSON export
import os # Added for os.path.exists
import cv2 # Added for loading image for OCR

from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QMenuBar, QMenu, QLabel, QFileDialog, QMessageBox # Added QMessageBox
from PyQt6.QtGui import QAction, QPixmap, QPainter, QColor, QFont # QRect is from QtCore
from PyQt6.QtCore import Qt, QRect, QPoint, QTimer # Added QPoint, QTimer. QRect was already here.

# Attempt to import the layout; handle if not found
try:
    from manual_keyboard_layout import MANUAL_LAYOUT
except ImportError:
    MANUAL_LAYOUT = [] # Default to empty list if not found
    print("Warning: manual_keyboard_layout.py not found or MANUAL_LAYOUT not defined. Initial layout will be empty.")

# Attempt to import KeyDetector; handle if not found
try:
    from key_detector import KeyDetector
except ImportError:
    KeyDetector = None # Placeholder if not found
    print("Warning: key_detector.py not found or KeyDetector class not defined. Detection features will be unavailable.")

class KeyboardDisplayLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent # To call MainWindow methods

    def mousePressEvent(self, event):
        if self.parent_window:
            # event.pos() gives QPoint relative to this QLabel
            self.parent_window.handle_key_press_event(event.pos())
        super().mousePressEvent(event)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("High-Fidelity Keyboard Simulator")
        self.current_layout = list(MANUAL_LAYOUT) # Load initial layout
        self.pressed_keys_visual_feedback = [] # For visual feedback on click
        self.last_clicked_key_id = None # Store ID of last clicked key

        # Create Status Bar first
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Initializing...")

        # Window flags
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        # Menu Bar
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        export_layout_action = QAction("Export Key Layout (JSON)", self)
        export_layout_action.triggered.connect(self.export_key_layout_json)
        file_menu.addAction(export_layout_action)
        file_menu.addSeparator() 
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools Menu
        tools_menu = menu_bar.addMenu("Tools")
        self.run_detection_action = QAction("Run Advanced Key Detection", self) 
        if KeyDetector is None: 
            self.run_detection_action.setEnabled(False)
            self.run_detection_action.setToolTip("KeyDetector module not loaded. Detection unavailable.")
        self.run_detection_action.triggered.connect(self.run_advanced_key_detection) 
        tools_menu.addAction(self.run_detection_action)

        # Image Loading and Display
        self.image_label = KeyboardDisplayLabel(self) # Use custom QLabel subclass
        self.base_pixmap = QPixmap("Keyboard_white.jpg") # Store original pixmap

        if self.base_pixmap.isNull():
            self.handle_image_load_error()
        else:
            self.pixmap = self.base_pixmap.copy() # Working pixmap for drawing
            self.image_label.setPixmap(self.pixmap)
            self.setCentralWidget(self.image_label)
            self.setFixedSize(self.pixmap.width(), self.pixmap.height())
            self.statusBar().showMessage(f"Image loaded: Keyboard_white.jpg ({self.pixmap.width()}x{self.pixmap.height()})")
            self.draw_key_overlays() # Initial draw using self.current_layout

    def handle_image_load_error(self):
        error_message = "Error: Could not load image 'Keyboard_white.jpg'."
        self.statusBar().showMessage(error_message)
        print(error_message)
        self.setFixedSize(600, 400) # Default size if image fails
        self.image_label.setText(error_message) # Display error on the label
        self.setCentralWidget(self.image_label)
        if hasattr(self, 'run_detection_action'):
            self.run_detection_action.setEnabled(False)
            self.run_detection_action.setToolTip("Image 'Keyboard_white.jpg' not loaded. Detection unavailable.")

    def draw_key_overlays(self):
        if self.base_pixmap.isNull(): # Check base_pixmap as self.pixmap might be a copy
            self.statusBar().showMessage("Cannot draw overlays: Base pixmap is not loaded.")
            return

        # Make a fresh copy from the base image to draw on
        self.pixmap = self.base_pixmap.copy()
        
        painter = QPainter(self.pixmap)

        if not self.current_layout:
            # self.statusBar().showMessage("No layout data to draw.") # Can be noisy
            painter.end()
            self.image_label.setPixmap(self.pixmap) # Show clean image if no layout
            return
        
        # Status bar message can be part of the calling function if needed, to avoid repetition
        # self.statusBar().showMessage(f"Drawing {len(self.current_layout)} key overlays...")
        for key_data in self.current_layout:
            pos = key_data["position"]
            label_text = key_data["label"]
            font_color_hex = key_data.get("font_color", "#000000") 
            bg_color_hex = key_data.get("background_color", "#FFFFFF")
            key_id = key_data.get("key_id", "")

            key_rect = QRect(pos['x'], pos['y'], pos['width'], pos['height'])

            # Determine background color based on press feedback
            if key_id in self.pressed_keys_visual_feedback:
                final_bg_color = QColor("#FFA500") # Orange highlight
                final_bg_color.setAlpha(150) # Semi-transparent highlight
            else:
                final_bg_color = QColor(bg_color_hex)
                final_bg_color.setAlpha(128) # Default alpha for normal state
            
            painter.fillRect(key_rect, final_bg_color)

            # Text drawing
            font_color = QColor(font_color_hex)
            painter.setPen(font_color)
            
            font = QFont("SF Pro Rounded", -1)
            font.setPointSizeF(pos['height'] * 0.35) 
            if font.pointSizeF() < 6:
                font.setPointSizeF(6)
            painter.setFont(font)
            
            painter.drawText(key_rect, Qt.AlignmentFlag.AlignCenter, label_text)

        painter.end()
        self.image_label.setPixmap(self.pixmap) # Update display
        # self.statusBar().showMessage("Key overlays drawn successfully.") # Can be noisy if called often


        # Note: Initial call to setFixedSize(800,600) or set_initial_size is removed.
        # The size is now determined by the image or a default if image loading fails.
        # Resizing is disabled by setFixedSize itself.

    # The set_initial_size method is no longer needed as size is based on image.
    # def set_initial_size(self, width, height):
    #     self.resize(width, height)

    # Override closeEvent if further customization is needed
    # def closeEvent(self, event):
    #     event.ignore() 

    def export_key_layout_json(self):
        if not self.current_layout: # Use self.current_layout now
            self.statusBar().showMessage("No key layout data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Key Layout", "keyboard_layout.json", "JSON files (*.json);;All Files (*)"
        )

        if not file_path:
            self.statusBar().showMessage("Export cancelled.")
            return

        try:
            with open(file_path, 'w') as f:
                json.dump(self.current_layout, f, indent=4) # Use self.current_layout
            self.statusBar().showMessage(f"Key layout exported to {file_path}")
        except IOError as e:
            self.handle_export_error(f"Error exporting layout: {e}")
        except Exception as e:
            self.handle_export_error(f"An unexpected error occurred during export: {e}")

    def handle_export_error(self, message):
        print(message)
        self.statusBar().showMessage(message)

    def handle_key_press_event(self, click_pos: QPoint):
        clicked_key_info = None
        for key_data in self.current_layout:
            pos = key_data['position']
            key_rect = QRect(pos['x'], pos['y'], pos['width'], pos['height'])
            if key_rect.contains(click_pos):
                clicked_key_info = key_data
                break
        
        if clicked_key_info:
            self.last_clicked_key_id = clicked_key_info['key_id']
            self.statusBar().showMessage(f"Key pressed: {clicked_key_info['label']} (ID: {self.last_clicked_key_id})")
            
            self.pressed_keys_visual_feedback = [self.last_clicked_key_id]
            self.draw_key_overlays() # Redraw with highlight
            
            QTimer.singleShot(200, self.clear_press_feedback) # Clear feedback after 200ms
        else:
            self.statusBar().showMessage(f"Clicked at ({click_pos.x()},{click_pos.y()}), no key found there.")


    def clear_press_feedback(self):
        self.pressed_keys_visual_feedback = []
        self.draw_key_overlays() # Redraw without highlight
        # Optionally, clear the status bar or set a default message
        # self.statusBar().showMessage("Ready")


    def run_advanced_key_detection(self):
        if KeyDetector is None:
            self.statusBar().showMessage("KeyDetector module is not available.")
            return

        image_path = "Keyboard_white.jpg"
        if not os.path.exists(image_path) or self.base_pixmap.isNull():
            self.statusBar().showMessage(f"Error: Image file '{image_path}' not found or not loaded.")
            print(f"Error: Image file '{image_path}' not found or not loaded for detection.")
            return

        detector = KeyDetector()
        self.statusBar().showMessage(f"Running advanced key detection on {image_path}...")
        QApplication.processEvents() 

        # Load image with OpenCV for processing
        image_cv = cv2.imread(image_path)
        if image_cv is None:
            self.statusBar().showMessage(f"Error: Could not load {image_path} with OpenCV for detection.")
            print(f"Error: Could not load {image_path} with OpenCV for detection.")
            return

        raw_bboxes = detector.detect_keys(image_path) # Still use detect_keys for initial bounding boxes
        if not raw_bboxes:
            self.statusBar().showMessage("No initial key regions found by detect_keys.")
            return
        
        print(f"Initial detection found {len(raw_bboxes)} raw bounding boxes.")
        self.statusBar().showMessage(f"Initial detection found {len(raw_bboxes)} raw boxes. Refining with OCR...")
        QApplication.processEvents()

        identified_keys_list = detector.refine_and_identify_keys(image_cv, raw_bboxes)
        
        count = len(identified_keys_list)
        self.statusBar().showMessage(f"Advanced detection identified {count} keys.")
        print(f"Advanced detection identified {count} keys:")
        if count > 0:
            for i, key_info in enumerate(identified_keys_list):
                print(f"  Key {i+1}: Label='{key_info['label']}', Pos={key_info['position']}")
        
            reply = QMessageBox.question(self, 'Update Display?', 
                                         "Do you want to replace the current keyboard layout with the newly detected keys and redraw the overlays?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                         QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_layout = identified_keys_list
                self.draw_key_overlays() # Redraw with the new layout
                self.statusBar().showMessage(f"Layout updated with {count} detected keys.")
            else:
                self.statusBar().showMessage("Detected layout not applied.")
        else:
            self.statusBar().showMessage("No keys identified after OCR refinement.")


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
