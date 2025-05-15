import os
import uuid
import pandas as pd
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from skimage.draw import disk


def add_or_replace_row(df, new_row):
    new_row['unique_id'] = str(uuid.uuid4())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df


def load_dicom_image(dicom_path):
    """ Load a DICOM image and return pixel array. """
    dicom_data = pydicom.dcmread(dicom_path, force=True)
    return dicom_data.pixel_array


def extract_roi_mean(image, center, radius):
    """ Extract mean intensity from a circular ROI. """
    rr, cc = disk(center, radius, shape=image.shape)  # Get coordinates for circular mask
    roi_values = image[rr, cc]  # Extract pixel values inside the ROI
    return np.mean(roi_values)  # Compute mean intensity


def compute_uniformity_for_images(dicom_folder):
    """ Compute uniformity across multiple DICOM images. """
    dicom_files = [f for f in os.listdir(dicom_folder) if (".txt" not in str(f) and ".csv" not in str(f))]
    
    all_roi_means = []
    
    for dicom_file in dicom_files:
        dicom_file_path = os.path.join(dicom_folder, dicom_file)
        image = load_dicom_image(dicom_file_path)
        h, w = image.shape
        radius = int(0.1 * (w / 2))  # ROI area = 10% of full circle
        
        # Define 5 ROI centers
        roi_centers = [
            (h//2, w//2),  # Center
            (h//2 - int(0.4*w/2), w//2),  # Top
            (h//2 + int(0.4*w/2), w//2),  # Bottom
            (h//2, w//2 - int(0.4*h/2)),  # Left
            (h//2, w//2 + int(0.4*h/2))   # Right
        ]

        roi_means = [extract_roi_mean(image, center, radius) for center in roi_centers]
        all_roi_means.append(roi_means)

    # Convert to NumPy array for easy averaging
    all_roi_means = np.array(all_roi_means)  # Shape: (num_images, 5)

    # Compute mean HU values for each ROI across all images
    avg_roi_means = np.mean(all_roi_means, axis=0)  # Shape: (5,)
    mean_roi_value = np.mean(avg_roi_means)

    # Compute uniformity (max deviation from mean)
    uniformity = max(abs(roi - mean_roi_value) for roi in avg_roi_means)

    return mean_roi_value, uniformity, str(len(dicom_files))



def activate_required_uniformity(folder_path):
    """
        1. Loads the DICOM image and extracts pixel values.
        2. Places 5 circular ROIs:
            One at the center.
            Four around it at equal distances (similar to your image).
            The ROI size is 10% of the full circle area.

        3. Extracts mean intensity from each ROI.
        4. Computes the uniformity:
            Finds the mean ROI value.
            Calculates the maximum deviation from the mean ROI value.
            This value represents the uniformity deviation.
    """
    mean, average_uniformity, slices = compute_uniformity_for_images(folder_path)

    folder_name = str(folder_path).split("/")[-1]
    row = {'folder_name': folder_name, 'slices': slices, 'value': average_uniformity}

    database = os.path.join(folder_path, "database_uniformity.csv")
    df = pd.read_csv(database)
    updated_df = add_or_replace_row(df, row)
    updated_df.to_csv(database, index=False)

    return True