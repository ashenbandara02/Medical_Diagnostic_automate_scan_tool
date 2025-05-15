import ast
import os
import uuid
import pydicom
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.fft import fft, fftfreq
from scipy.ndimage import zoom


import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security import decrypt_file


def add_or_replace_row(df, new_row):
    circle_name = new_row['circle_name']

    # if circle_name in df['circle_name'].values:
    #     index = df[df['circle_name'] == circle_name].index[0]
    #     new_row['unique_id'] = df.loc[index, 'unique_id']  # Preserve existing unique_id
    #     df.loc[index] = new_row

    # else:
        # Append the new row with a new unique_id
    new_row['unique_id'] = str(uuid.uuid4())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    return df


def rebin(spatial_freq, mtf, bin_size):
    """Rebin the spatial frequency and MTF for smoother representation."""
    
    # Calculate the number of bins, ensuring it's an integer (floor if needed)
    num_bins = int(np.floor(len(spatial_freq) / bin_size))
    
    # Adjust bin_size so we don't exceed the length of the array
    adjusted_bin_size = len(spatial_freq) / num_bins if num_bins else len(spatial_freq)
    
    binned_spatial_freq = []
    binned_mtf = []
    
    # Iterate over the number of bins and average the corresponding values
    for i in range(num_bins):
        start_index = int(i * adjusted_bin_size)
        end_index = int((i + 1) * adjusted_bin_size)
        
        # Ensure that we don't go out of bounds for the last bin
        if end_index > len(spatial_freq):
            end_index = len(spatial_freq)
        
        # Slice the arrays for this bin
        bin_spatial_freq = spatial_freq[start_index:end_index]
        bin_mtf = mtf[start_index:end_index]
        
        # Check if the bin has values, avoid empty bins
        if len(bin_spatial_freq) > 0 and len(bin_mtf) > 0:
            binned_spatial_freq.append(np.mean(bin_spatial_freq))
            binned_mtf.append(np.mean(bin_mtf))
        else:
            binned_spatial_freq.append(np.nan)  # Insert NaN if the bin is empty (which shouldn't happen)
            binned_mtf.append(np.nan)

    return np.array(binned_spatial_freq), np.array(binned_mtf)




def activate_required_mtf(path, database):
    mtf_settings = decrypt_file()[1]['mtf']
    circles = [mtf_settings['circle_1'], mtf_settings['circle_2'], mtf_settings['circle_3'],
               mtf_settings['circle_4'], mtf_settings['circle_5']]
    
    first_slice = int(mtf_settings['min_slice'])
    last_slice = int(mtf_settings['max_slice'])

    all_dicoms = [f for f in os.listdir(path) if (".txt" not in str(f) and ".csv" not in str(f))] # Above we consider on the image files for mtf processing

    if last_slice > len(all_dicoms):
        last_slice = len(all_dicoms)
    
    all_dicoms = all_dicoms[first_slice - 1: last_slice] # slicing min - max slice

    for circle_in_image in circles:
        circle_in_image = ast.literal_eval(circle_in_image)
        mtf_list = [] # Initialize a list to store MTFs

        for file_name in all_dicoms:
            dicom_path = os.path.join(path, file_name)
            dicom_data = pydicom.dcmread(dicom_path, force=True)
            dicom_image = dicom_data.pixel_array.astype(np.float64)
            normalized_image = (dicom_image - dicom_image.min()) / (dicom_image.max() - dicom_image.min())

            # Crop the region containing the edge
            cropped_image = normalized_image[circle_in_image[0][0]:circle_in_image[0][1]
                                             , circle_in_image[1][0]:circle_in_image[1][1]] # y,x
            
            pixel_reduction_factor = int(mtf_settings['pixel_red_factor'])
            reduced_image = ""

             # Apply pixel reduction (downsample the cropped image)
            if pixel_reduction_factor != 1:
                # Apply downsampling by zooming the image (reduce resolution)
                reduced_image = zoom(cropped_image, 1 / pixel_reduction_factor)
            else:
                reduced_image = cropped_image

            # Extract the edge profile (average intensity along rows or columns)
            edge_profile = np.mean(reduced_image, axis=0)  # Adjust axis based on edge orientation
            esf = gaussian_filter1d(edge_profile, sigma=2) # Smooth the edge profile to obtain the ESF (Edge Spread Function)
            lsf = np.gradient(esf) # Calculate the LSF (Line Spread Function) by differentiating the ESF

            # Compute the MTF (Modulation Transfer Function) using the Fourier Transform
            ft_lsf = fft(lsf)
            mtf = np.abs(ft_lsf)
            mtf = mtf / np.max(mtf)  # Normalize the MTF to make the maximum value 1
            mtf_list.append(mtf)


        average_mtf = np.mean(mtf_list, axis=0)# Compute the average MTF
        pixel_spacing = float(pydicom.dcmread(os.path.join(path, all_dicoms[0])).PixelSpacing[0]) # Generate the spatial frequency axis (based on the first image's metadata)
        spatial_freq = fftfreq(len(average_mtf), d=pixel_spacing)

        # Apply frequency rebinning (new modification)
        bin_size = float(mtf_settings['f_rebin_increment'])
        binned_spatial_freq, binned_mtf = rebin(spatial_freq, average_mtf, bin_size)

        # Flatten the MTF and spatial frequency for saving in the database
        avg_mtf_str = np.array2string(binned_mtf, separator=',').replace('\n', ' ').strip('[]').replace(" ", "").strip()  # Flatten to single line and remove brackets
        spatial_freq_str = np.array2string(binned_spatial_freq, separator=',').replace('\n', ' ').strip('[]').replace(" ", "").strip()
        
        # Add to database or Replace exisiting
        folder_name = str(path).split("/")[-1]


        current_circle_name = next((k for k, v in mtf_settings.items() if v == str(circle_in_image)), None)
        row = {'folder_name': folder_name, 'circle_name': str(current_circle_name), 'applied_roi': str(circle_in_image), 'avg_mtf': avg_mtf_str, 'spacial_frequency': spatial_freq_str}

        df = pd.read_csv(database)
        updated_df = add_or_replace_row(df, row)
        updated_df.to_csv(database, index=False)
        
    return True

