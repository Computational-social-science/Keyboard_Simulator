import cv2
import numpy as np
import os # Added for checking file existence in main
import pytesseract # Added for OCR
from PIL import Image # Added for OCR

class KeyDetector:
    def __init__(self):
        """
        Initializes the KeyDetector.
        """
        # Parameters for blurring and thresholding
        self.gaussian_blur_ksize = (5, 5)
        self.adaptive_thresh_block_size = 11
        self.adaptive_thresh_c = 2

        # Parameters for contour filtering, as specified in the prompt
        self.contour_min_area = 50 * 50
        self.contour_max_area = 200 * 600
        self.contour_min_aspect_ratio = 0.2
        self.contour_max_aspect_ratio = 5.0


    def detect_keys(self, image_path):
        """
        Detects potential key regions in an image using basic computer vision techniques.

        Args:
            image_path (str): Path to the keyboard image.

        Returns:
            list: A list of tuples, where each tuple is (x, y, w, h) for a detected key's bounding box.
                  Returns an empty list if the image cannot be loaded or no keys are found.
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return []

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        blurred_image = cv2.GaussianBlur(gray_image, self.gaussian_blur_ksize, 0)
        
        thresholded_image = cv2.adaptiveThreshold(
            blurred_image, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            self.adaptive_thresh_block_size, 
            self.adaptive_thresh_c
        )

        contours_tuple = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours_tuple) == 2: 
            contours = contours_tuple[0]
        elif len(contours_tuple) == 3: 
            contours = contours_tuple[1]
        else:
            print("Error: Unexpected return format from cv2.findContours")
            return []

        potential_keys_bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            if w == 0 or h == 0:
                continue

            area = w * h
            aspect_ratio = w / h 

            if (area >= self.contour_min_area and
                area <= self.contour_max_area and
                aspect_ratio >= self.contour_min_aspect_ratio and
                aspect_ratio <= self.contour_max_aspect_ratio):
                potential_keys_bboxes.append((x, y, w, h))
        
        return potential_keys_bboxes

    def refine_and_identify_keys(self, image_cv, bboxes):
        """
        Refines detected bounding boxes using heuristics (sorting, simplified row clustering)
        and performs OCR on each ROI to identify key labels.

        Args:
            image_cv: The original color image loaded by OpenCV.
            bboxes (list): The raw list of (x, y, w, h) from detect_keys.

        Returns:
            list: A list of dictionaries, where each dictionary represents an identified key.
        """
        if image_cv is None:
            print("Error: Input image_cv is None in refine_and_identify_keys.")
            return []
        if not bboxes:
            print("No bounding boxes provided to refine_and_identify_keys.")
            return []

        # Sort bboxes by y-coordinate primarily, then x-coordinate
        bboxes.sort(key=lambda b: (b[1], b[0]))

        identified_keys = []
        
        # Simplified row clustering and processing (basic example, more robust logic could be added)
        # For this implementation, we'll process them in sorted order, which approximates row-by-row.
        # A more complex clustering could group by y-coordinate similarity.
        # Let's calculate an average key height from the first few bboxes for row delta.
        # This is a very rough heuristic.
        avg_height_sample = [b[3] for b in bboxes[:min(len(bboxes), 5)] if b[3] > 0]
        average_key_height = np.mean(avg_height_sample) if avg_height_sample else 30 # Fallback
        
        current_row_y_start = -1
        y_delta_threshold = average_key_height * 0.7 # Allow some variance in y for a row

        for i, bbox in enumerate(bboxes):
            x, y, w, h = bbox

            if y > current_row_y_start + y_delta_threshold : # Simple new row detection
                 current_row_y_start = y
            # Further row-based processing could occur here if needed.

            # Extract ROI from the original color image
            roi = image_cv[y:y+h, x:x+w]

            if roi.size == 0: # Check if ROI is empty
                print(f"Warning: Empty ROI at x={x}, y={y}, w={w}, h={h}. Skipping.")
                continue

            # Preprocess ROI for OCR
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # Apply Otsu's thresholding
            _, thresholded_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU) # Invert for white text on black bg if needed
                                                                                                    # Or THRESH_BINARY if black text on white.
                                                                                                    # For typical keyboard images (dark text on light keys),
                                                                                                    # THRESH_BINARY or THRESH_BINARY_INV + bitwise_not might be better.
                                                                                                    # Let's assume keys are lighter than text, so THRESH_BINARY_INV
            
            # Optional: Invert if text is white on dark keys (common for some keyboard designs)
            # if np.mean(gray_roi) < 128: # Heuristic for dark background
            #    thresholded_roi = cv2.bitwise_not(thresholded_roi)


            # Convert processed ROI to PIL Image
            try:
                pil_image = Image.fromarray(thresholded_roi)
            except Exception as e:
                print(f"Error converting ROI to PIL Image: {e}. ROI shape: {thresholded_roi.shape}, dtype: {thresholded_roi.dtype}")
                continue


            # Perform OCR
            # PSM 6: Assume a single uniform block of text.
            # PSM 7: Treat the image as a single text line.
            # PSM 10: Treat the image as a single character. (Often good for single keycaps)
            # Let's try PSM 10 for individual keys, or PSM 7 if that's too restrictive.
            # PSM 6 is often better for blocks of text.
            ocr_config = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`~!@#$%^&*()-_=+[]{};:\'",<.>/?\| '
            try:
                label_text = pytesseract.image_to_string(pil_image, config=ocr_config).strip()
            except pytesseract.TesseractError as e:
                print(f"Pytesseract error during OCR: {e}")
                label_text = ""
            except Exception as e: # Catch any other pytesseract/PIL issues
                print(f"Unexpected error during OCR: {e}")
                label_text = ""


            # Clean up common OCR misinterpretations for single characters or typical key labels
            if len(label_text) > 3 and label_text not in ["Shift", "Enter", "Space", "Ctrl", "Alt", "Tab", "Caps", "Backspace"]: # Arbitrary length for 'too long'
                # If it's a long string and not a known multi-char key, maybe it's noise.
                # Or, try a different PSM mode if PSM 10 is too restrictive.
                # For now, we'll just take it or leave it based on PSM 10.
                pass 
            
            # If label_text is empty, maybe try PSM 7
            if not label_text:
                try:
                    ocr_config_psm7 = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`~!@#$%^&*()-_=+[]{};:\'",<.>/?\| '
                    label_text = pytesseract.image_to_string(pil_image, config=ocr_config_psm7).strip()
                except: # Ignore errors on retry
                    pass


            key_data = {
                "key_id": f"detected_{x}_{y}_{w}_{h}", # Unique ID based on geometry
                "label": label_text if label_text else "Unknown",
                "position": {"x": x, "y": y, "width": w, "height": h},
                "type": "detected", 
                "font_color": "#FF0000", # Red text for detected
                "background_color": "#00FF00", # Green background for detected
                "group": "detected_group", 
                "characters": [label_text.lower()] if label_text else ["unknown"]
            }
            identified_keys.append(key_data)
            
        return identified_keys


if __name__ == '__main__':
    print("Running KeyDetector directly for testing (including refine_and_identify_keys)...")
    detector = KeyDetector()
    image_file = "Keyboard_white.jpg" 
    
    if not os.path.exists(image_file):
        print(f"Test image '{image_file}' not found. Skipping direct test run.")
    else:
        print(f"Attempting to detect keys in image: {image_file}")
        # First, get raw bounding boxes
        raw_bboxes = detector.detect_keys(image_file)
        print(f"detect_keys found {len(raw_bboxes)} raw bounding boxes.")

        if raw_bboxes:
            # Load the image in OpenCV format for refine_and_identify_keys
            image_cv_for_ocr = cv2.imread(image_file)
            if image_cv_for_ocr is None:
                print(f"Error: Could not re-load image {image_file} for OCR.")
            else:
                print("Running refine_and_identify_keys...")
                identified_keys_list = detector.refine_and_identify_keys(image_cv_for_ocr, raw_bboxes)
                print(f"refine_and_identify_keys processed {len(identified_keys_list)} keys:")
                for i, key_info in enumerate(identified_keys_list):
                    print(f"  {i+1}: Label='{key_info['label']}', Pos={key_info['position']}")
        else:
            print("No raw bounding boxes found, skipping refine_and_identify_keys.")
            
    print("\nKeyDetector direct test finished.")
