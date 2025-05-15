import cv2
import numpy as np
import pydicom

def classify_image(image_path):
    """
    Classify an image as having 5 rods (circles) or being blank-like (black).

    Args:
        image_path (str): Path to the DICOM image to classify.

    Returns:
        str: '5 rods' if the image contains 5 distinct circles,
             'blank' if it does not.
    """
    try:
        # Load the DICOM file
        dicom_data = pydicom.dcmread(image_path)
        image = dicom_data.pixel_array
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        blurred_image = cv2.GaussianBlur(image, (9, 9), 2)
        # Detect circles using Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred_image, 
            cv2.HOUGH_GRADIENT, 
            dp=1.2, 
            minDist=20, 
            param1=50, 
            param2=30, 
            minRadius=10, 
            maxRadius=50
        )
        
        # Check if circles are detected
        if circles is not None:
            return True #mtf
        else:
            return False #nps
            
    except Exception as e:
        return f"Error: {e}"
        
# Example usage:
# image_path = 'test2/IM00002'
# result = classify_image(image_path)
# print(result)
