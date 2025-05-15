import ast
import os
import time
import uuid
import pydicom
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.fft import fft, fftfreq
from scipy.ndimage import zoom
from scipy.fftpack import fft2, fftshift
from scipy.signal import windows


import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security import decrypt_file

window_func = windows.hann

def radial_average(power_spectrum_2d):
    """Convert 2D power spectrum to 1D radial profile."""
    h, w = power_spectrum_2d.shape
    y, x = np.indices((h, w))
    center = (h//2, w//2)
    r = np.sqrt((x - center[1])**2 + (y - center[0])**2).astype(int)
    
    radial_sum = np.bincount(r.ravel(), power_spectrum_2d.ravel())
    radial_count = np.bincount(r.ravel())
    return radial_sum[1:] / radial_count[1:]  # Skip r=0 to avoid DC component


def add_or_replace_row(df, new_row):
    new_row['unique_id'] = str(uuid.uuid4())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

def compute_nps(image, pixel_spacing):
    """Computes the NPS of an image and converts units to HU² mm²."""
    h, w = image.shape
    window = window_func(h)[:, None] * window_func(w)  # Apply 2D window
    image_windowed = image * window
    fft_image = fft2(image_windowed)
    power_spectrum = np.abs(fftshift(fft_image)) ** 2
    
    # Convert NPS units from pixel² to mm² and include HU²
    pixel_area = pixel_spacing[0] * pixel_spacing[1]  # mm² per pixel
    power_spectrum *= pixel_area  # Convert NPS to mm²
    
    return power_spectrum


def extract_roi(image, center, angle, radius, size):
    """Extracts a rectangular ROI at a given angle and radius from the center."""
    h, w = size
    y_c, x_c = center
    y = int(y_c + radius * np.sin(angle))
    x = int(x_c + radius * np.cos(angle))
    return image[y - h//2:y + h//2, x - w//2:x + w//2]


def activate_required_nps(path, database):
    nps_settings = decrypt_file()[1]['nps']

    # roi_size = (64, 64)  # ROI size (height, width)
    # num_rois = 40  # Number of ROIs around the circumference
    # distance_from_center = 150  # Distance of ROIs from center
    # f_rebin_increment = 1
    roi_size = tuple(nps_settings['roi_size'])  # ROI size (height, width)
    num_rois = nps_settings['num_rois']  # Number of ROIs around the circumference
    distance_from_center = nps_settings['dist_c_to_record']  # Distance of ROIs from center
    f_rebin_increment = nps_settings['f_rebin_increment']

    first_slice = int(nps_settings['min_slice'])
    last_slice = int(nps_settings['max_slice'])

    all_dicoms = [f for f in os.listdir(path) if (".txt" not in str(f) and ".csv" not in str(f))] # Above we consider on the image files for mtf processing

    if last_slice > len(all_dicoms):
        last_slice = len(all_dicoms)
    
    time.sleep(10)
    all_dicoms = all_dicoms[first_slice - 1: last_slice] # slicing min - max slice


    images = []
    for f in all_dicoms:
        ds = pydicom.dcmread(path+"/"+f, force=True)
        image = ds.pixel_array.astype(np.float64)
        if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
            image = image * ds.RescaleSlope + ds.RescaleIntercept  # Convert to HU
        images.append((image, ds.PixelSpacing))


    nps_list = []
    center = (images[0][0].shape[0] // 2, images[0][0].shape[1] // 2)  # Center of circular region
    angles = np.linspace(0, 2 * np.pi, num_rois, endpoint=False)
    for img in images:
        for angle in angles:
            roi = extract_roi(img[0], center, angle, distance_from_center, roi_size)
            nps = compute_nps(roi, img[1])
            nps_list.append(nps)

    average_nps_2d = np.mean(nps_list, axis=0)
    average_nps_1d = radial_average(average_nps_2d)  # Convert to 1D

    num_points = len(average_nps_1d)
    freq = fftfreq(num_points * 2, d=f_rebin_increment)[:num_points]

    np.savetxt(f'{path}/temp_average_nps.csv', average_nps_1d, delimiter=',', fmt='%.8f')
    np.savetxt(f'{path}/temp_spatial_freq.csv', freq, delimiter=',', fmt='%.8f')

    # Read the CSV data as strings to store in the database
    with open(f'{path}/temp_average_nps.csv', 'r') as f:
        avg_nps_csv_str = f.read().replace('\n', ';')  # Use ; to separate rows

    with open(f'{path}/temp_spatial_freq.csv', 'r') as f:
        freq_csv_str = f.read().replace('\n', ';')

    folder_name = str(path).split("/")[-1]
    row = {'folder_name': folder_name, 'average_nps': avg_nps_csv_str, 'spacial_frequency': freq_csv_str}

    # Update the CSV database
    df = pd.read_csv(database)
    updated_df = add_or_replace_row(df, row)
    updated_df.to_csv(database, index=False)

    # Cleanup temporary files
    os.remove(f'{path}/temp_average_nps.csv')
    os.remove(f'{path}/temp_spatial_freq.csv')
    
    return True