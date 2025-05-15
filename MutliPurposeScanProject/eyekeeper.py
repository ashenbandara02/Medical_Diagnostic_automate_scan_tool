import os
import time
import shutil
from datetime import datetime
import threading
import uuid

import pandas as pd

from detect_type import classify_image

# Directory paths
# WATCHED_DIR = "C:/Users/ashen/OneDrive/Desktop/pictures"
# OUTPUT_DIR = WATCHED_DIR

# Time interval in seconds (1 minutes)
INTERVAL = 60

def organize_files(WATCHED_DIR):
    OUTPUT_DIR = WATCHED_DIR
    while True:
        # Get the current time for folder naming
        timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
        unique_folder = os.path.join(OUTPUT_DIR, timestamp)
        # Check for files in the watched directory
        files = [f for f in os.listdir(WATCHED_DIR) if os.path.isfile(os.path.join(WATCHED_DIR, f))]

        # Create directory for mean file if its not present
        if "Mean" in os.listdir(WATCHED_DIR):
            pass
        else:
            mean_directory = os.path.join(OUTPUT_DIR, "Mean")
            os.makedirs(mean_directory, exist_ok=True)

            for i in range(1, 6):
                file_path = os.path.join(mean_directory, f"database_MEAN_{i}.csv")
                
                # Create DataFrame with specified columns
                df_mean = pd.DataFrame(columns=['unique_id', 'date_time', 'mean'])
                
                df_mean['unique_id'] = [str(uuid.uuid4()) for _ in range(len(df_mean))]
                
                # Save to CSV
                df_mean.to_csv(file_path, index=False)
                print(f"Created: {file_path}")


        if len(files) > 0:
            # Create a unique folder
            os.makedirs(unique_folder, exist_ok=True)
            run = 0
            for file in files:
                
                file_path = os.path.join(WATCHED_DIR, file)
                dest_path = os.path.join(unique_folder, file)

                # Move file to the unique folder
                shutil.move(file_path, dest_path)
                print(f"Moved: {file} -> {unique_folder}")

                if run == 0:
                    mtf = classify_image(dest_path)
                    write_code = ""
                    if mtf:
                        write_code = "MTF"
                    else:
                        write_code = "NPS"

                    with open(unique_folder+"/processing_kind.txt", 'w', encoding="utf-8") as f:
                        f.write(write_code)

        time.sleep(INTERVAL)

def start_monitoring_for_uploads(WATCHED_DIR):
    monitor_thread = threading.Thread(target=organize_files, args=(WATCHED_DIR,), daemon=True)
    monitor_thread.start()
    return monitor_thread
