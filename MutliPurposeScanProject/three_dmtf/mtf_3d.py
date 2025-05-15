import os
import sys
import pydicom
import uuid
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
from scipy.ndimage import gaussian_filter1d, zoom
from scipy.fft import fft, fftfreq

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security import decrypt_file

def add_or_replace_row(df, new_row):
    new_row['unique_id'] = str(uuid.uuid4())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    return df

def rebin(spatial_freq, mtf, bin_size):
    """Rebin the spatial frequency and MTF for smoother representation."""
    
    # If bin_size is 1, return the original arrays unchanged
    if bin_size == 1:
        return spatial_freq, mtf  # No modification
    
    num_bins = int(np.floor(len(spatial_freq) / bin_size))
    
    if num_bins == 0:  # If too few bins, return original data
        return spatial_freq, mtf
    
    adjusted_bin_size = len(spatial_freq) / num_bins

    binned_spatial_freq = []
    binned_mtf = []

    for i in range(num_bins):
        start_index = int(i * adjusted_bin_size)
        end_index = int((i + 1) * adjusted_bin_size)
        
        if end_index > len(spatial_freq):
            end_index = len(spatial_freq)

        bin_spatial_freq = spatial_freq[start_index:end_index]
        bin_mtf = mtf[start_index:end_index]

        if len(bin_spatial_freq) > 0 and len(bin_mtf) > 0:
            binned_spatial_freq.append(np.mean(bin_spatial_freq))
            binned_mtf.append(np.mean(bin_mtf))

    return np.array(binned_spatial_freq), np.array(binned_mtf)

def dicom_maker(dicom_file_path):
    # Load DICOM files into a list
    dicom_files = [pydicom.dcmread(os.path.join(dicom_file_path, f)) for f in sorted(os.listdir(dicom_file_path)) if "." not in f]

    # Stack images into a 3D NumPy array
    images = [file.pixel_array for file in dicom_files]

    # Convert the list into a numpy array (shape: [slices, height, width])
    volume = np.stack(images, axis=0)

    # Cut the volume vertically through the Z-plane (along the X-axis)
    half_volume = volume[:, :, :volume.shape[2] // 2]  # Keep the first half along the X-axis
    combined_image = np.max(half_volume, axis=2)  # Combine along the Z-direction

    normalized_image = (combined_image - combined_image.min()) / (combined_image.max() - combined_image.min()) * 255
    normalized_image = normalized_image.astype(np.uint8)  # Convert to 8-bit

    plt.imsave(os.path.join(dicom_file_path, "3dmtf_z_axis_crossection.png"), normalized_image, cmap='gray', dpi=300)

    ######################################################

    with Image.open(os.path.join(dicom_file_path, "3dmtf_z_axis_crossection.png")) as img:
        width, height = img.size
        rotated_img = img.rotate(-90, expand=True)
        rotated_img.save(os.path.join(dicom_file_path, "3dmtf_z_axis_crossection.png"))

    center_x_left, center_x_right = int((width/2)-10), int((width/2)+10)
    y_top, y_bottom = 0, height

    cropped_image = normalized_image[y_top:y_bottom, center_x_left:center_x_right] # y,x roi applied

    plt.imsave(os.path.join(dicom_file_path, "3d_mtf_final.png"), cropped_image, cmap='gray', dpi=300)

    with Image.open(os.path.join(dicom_file_path, "3d_mtf_final.png")) as img:
        rotated_img = img.rotate(-90, expand=True)
        rotated_img.save(os.path.join(dicom_file_path, "3d_mtf_final.png"))

    ######################################################
    # Save the final output as a DICOM image
    # Create a new DICOM dataset
    # Rotate the cropped image clockwise by 90 degrees
    rotated_cropped_image = np.rot90(cropped_image, k=-1)

    # Save the final output as a DICOM image
    # Create a new DICOM dataset
    new_dicom = pydicom.Dataset()

    # Set the necessary DICOM headers (you can copy some from the original DICOM files)
    original_dicom = dicom_files[0]
    new_dicom.file_meta = original_dicom.file_meta
    new_dicom.PatientName = original_dicom.PatientName
    new_dicom.PatientID = original_dicom.PatientID
    new_dicom.Modality = original_dicom.Modality
    new_dicom.SeriesDescription = "Processed MTF Image"
    new_dicom.Rows, new_dicom.Columns = rotated_cropped_image.shape
    new_dicom.PixelSpacing = original_dicom.PixelSpacing
    new_dicom.BitsStored = 8
    new_dicom.BitsAllocated = 8
    new_dicom.HighBit = 7
    new_dicom.PixelRepresentation = 0
    new_dicom.SamplesPerPixel = 1
    new_dicom.PhotometricInterpretation = "MONOCHROME2"

    # Set the pixel data
    new_dicom.PixelData = rotated_cropped_image.tobytes()

    # Save the new DICOM file
    new_dicom.save_as(os.path.join(dicom_file_path, '3d_mtf_final.dcm'))

def activate_required_3d_mtf(dicom_path, database):
    threed_mtf_settings = decrypt_file()[1]['mtf_3d']

    pixel_spacing=threed_mtf_settings['pixel_spacing']
    sigma=threed_mtf_settings['sigma']
    pixel_reduction_factor=threed_mtf_settings['pixel_reduction_factor']
    rebin_factor=threed_mtf_settings['rebin_factor']
    
    ## Get the Slices / Create 3d stack / Cut rotate and save as dicom the required roi
    dicom_maker(dicom_path)

    ## Final part ###
    dicom_file = os.path.join(dicom_path, "3d_mtf_final.dcm")
    dicom_data = pydicom.dcmread(dicom_file, force=True)
    image = dicom_data.pixel_array
    
    normalized_image = image.astype(np.float64) / np.max(image)
    if pixel_reduction_factor > 1:
        normalized_image = zoom(normalized_image, 1 / pixel_reduction_factor)

    # Compute edge profile (average intensity along columns)
    edge_profile = np.mean(normalized_image, axis=0)

    # Apply Gaussian smoothing to get the ESF (Edge Spread Function)
    esf = gaussian_filter1d(edge_profile, sigma=sigma)

    # Compute the LSF (Line Spread Function) by differentiating the ESF
    lsf = np.gradient(esf)

    # Compute the MTF (Modulation Transfer Function) by FFT of the LSF
    ft_lsf = fft(lsf)
    mtf = np.abs(ft_lsf)
    mtf /= np.max(mtf)  # Normalize the MTF

    # Compute spatial frequency
    spatial_freq = fftfreq(len(mtf), d=pixel_spacing)

    # Keep only positive frequencies
    pos_indices = spatial_freq >= 0
    spatial_freq = spatial_freq[pos_indices]
    mtf = mtf[pos_indices]

    # Apply rebinning
    binned_spatial_freq, binned_mtf = rebin(spatial_freq, mtf, rebin_factor)

    # Flatten the MTF and spatial frequency for saving in the database
    mtf_str = np.array2string(binned_mtf, separator=',').replace('\n', ' ').strip('[]').replace(" ", "").strip()  # Flatten to single line and remove brackets
    spatial_freq_str = np.array2string(binned_spatial_freq, separator=',').replace('\n', ' ').strip('[]').replace(" ", "").strip()
    
    folder_name = str(dicom_path).split("/")[-1]

    row = {'folder_name': folder_name, 'mtf': mtf_str, 'spacial_f': spatial_freq_str}

    df = pd.read_csv(database)
    updated_df = add_or_replace_row(df, row)
    updated_df.to_csv(database, index=False)

    return True
