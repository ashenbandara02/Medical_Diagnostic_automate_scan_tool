import datetime
import statistics
import uuid
import cv2
import os
import numpy as np
import pandas as pd
import pydicom
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security import decrypt_file



def add_or_replace_row(df, new_row):
    new_row['unique_id'] = str(uuid.uuid4())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    return df

def extract_roi_means(dicom_path, centers_radii):
    # Load DICOM image
    dicom = pydicom.dcmread(dicom_path, force=True)
    pixel_array = dicom.pixel_array.astype(np.float32)
    
    roi_means = []
    
    for (x, y, radius) in centers_radii:
        # Create a circular mask
        mask = np.zeros_like(pixel_array, dtype=np.uint8)
        cv2.circle(mask, (x, y), radius, 255, thickness=-1)  # Fill circle with white (255)
        
        # Extract pixel values within the mask
        roi_pixels = pixel_array[mask == 255]
        
        # Compute mean intensity
        mean_value = np.mean(roi_pixels) if roi_pixels.size > 0 else 0
        roi_means.append(mean_value)
    
    return roi_means

def activate_required_mean_plotter(mtf_directory_path):
    s_location = decrypt_file()[1]['storage_location']
    print("Creating Mean Section for new files!!")

    # modify these will changeable settings
    radius_1 = 9
    radius_2 = 13
    radius_3 = 15
    radius_4 = 17
    radius_5 = 19

    centers_radii = [(156, 224, radius_1), (195, 171, radius_2), (275, 151, radius_3), (353, 195, radius_4), (372, 288, radius_5)]


    mean_file1 = s_location+"/Mean/database_MEAN_1.csv"
    mean_file2 = s_location+"/Mean/database_MEAN_2.csv"
    mean_file3 = s_location+"/Mean/database_MEAN_3.csv"
    mean_file4 = s_location+"/Mean/database_MEAN_4.csv"
    mean_file5 = s_location+"/Mean/database_MEAN_5.csv"

    # Get the images 
    # for each part 1,2,3,4,5 find the mean and goto each database and addd a row
    all_dicoms = [f for f in os.listdir(mtf_directory_path) if (".txt" not in str(f) and ".csv" not in str(f) and ".png" not in str(f))]

    # for dicom in all_dicoms:

    row_1 = []
    row_2 = []
    row_3 = []
    row_4 = []
    row_5 = []

    for x in all_dicoms:
        image_path = mtf_directory_path+f"/{x}"
        mean_values_of_image = extract_roi_means(image_path, centers_radii)

        row_1.append(mean_values_of_image[0])
        row_2.append(mean_values_of_image[1])
        row_3.append(mean_values_of_image[2])
        row_4.append(mean_values_of_image[3])
        row_5.append(mean_values_of_image[4])


    d1_row = {
        "unique_id": str(uuid.uuid4()),  # Generates a random unique ID
        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Current date & time
        "mean": statistics.mean(row_1)  # Replace with actual mean value
    }

    d2_row = {
        "unique_id": str(uuid.uuid4()),  # Generates a random unique ID
        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Current date & time
        "mean": statistics.mean(row_2)  # Replace with actual mean value
    }

    d3_row = {
        "unique_id": str(uuid.uuid4()),  # Generates a random unique ID
        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Current date & time
        "mean": statistics.mean(row_3)  # Replace with actual mean value
    }

    d4_row = {
        "unique_id": str(uuid.uuid4()),  # Generates a random unique ID
        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Current date & time
        "mean": statistics.mean(row_4)  # Replace with actual mean value
    }

    d5_row = {
        "unique_id": str(uuid.uuid4()),  # Generates a random unique ID
        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Current date & time
        "mean": statistics.mean(row_5)  # Replace with actual mean value
    }


    df1 = pd.read_csv(mean_file1)
    updated_df1 = add_or_replace_row(df1, d1_row)
    updated_df1.to_csv(mean_file1, index=False)

    df2 = pd.read_csv(mean_file2)
    updated_df2 = add_or_replace_row(df2, d2_row)
    updated_df2.to_csv(mean_file2, index=False)

    df3 = pd.read_csv(mean_file3)
    updated_df3 = add_or_replace_row(df3, d3_row)
    updated_df3.to_csv(mean_file3, index=False)

    df4 = pd.read_csv(mean_file4)
    updated_df4 = add_or_replace_row(df4, d4_row)
    updated_df4.to_csv(mean_file4, index=False)

    df5 = pd.read_csv(mean_file5)
    updated_df5 = add_or_replace_row(df5, d5_row)
    updated_df5.to_csv(mean_file5, index=False)

    return True


def find_mtf_paths(start_path):
    pathsx = []
    
    # Walk through all subdirectories of start_path
    for root, dirs, files in os.walk(start_path):
        if 'processing_kind.txt' in files:
            file_path = os.path.join(root, 'processing_kind.txt')
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if content == 'MTF':
                    pathsx.append(root)
    
    return pathsx


def clean_and_resave_csvs(location):

    # List all CSV files in the 'Mean' directory
    csv_files = [f for f in os.listdir(location) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_path = os.path.join(location, csv_file)
        df = pd.read_csv(csv_path)

        # Keep only the column names (drop all rows)
        df_cleaned = pd.DataFrame(columns=df.columns)
        # Save the cleaned DataFrame (only column names) back to CSV
        df_cleaned.to_csv(csv_path, index=False)
        
        print(f"Cleaned CSV {csv_file}")
    return True


def rerun_worker_mean():
    # get all the folders that has 
    location = decrypt_file()[1]['storage_location']
    mtf_locations = find_mtf_paths(location)
    # clear out all the databases clean em
    mean_location = location+"/Mean"
    clean_csv = clean_and_resave_csvs(mean_location)
    if clean_csv:
        # rerun the activate required_mean_plotter_for each mtf directory
        for each in mtf_locations:
            mean_plotter_reactivation = activate_required_mean_plotter(each)
            if mean_plotter_reactivation:
                print(f"Regenerated {str(each.split("/")[-1])}")
            else:
                print(f"Error!! in {str(each.split("/")[-1])}")
    else:
        print("Error Cleaning CSVs contact developer!!!!")
