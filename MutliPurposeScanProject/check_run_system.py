import os
import time
import shutil
from datetime import datetime
import threading
import uuid
from security import decrypt_file
import pandas as pd

from two_dmtf.mtf import activate_required_mtf
from three_dmtf.mtf_3d import activate_required_3d_mtf
from nps.nps import activate_required_nps
from mean.mean import activate_required_mean_plotter
from uniformity.uniformity import activate_required_uniformity


def regulate_system_calculations(path, database, database_3d, type):
    # check for recalculations or not
    if type == "MTF":   # connect with mtf or nps do the work and save it
        activate_2d_mtf = activate_required_mtf(path, database)
        activate_3d_mtf = activate_required_3d_mtf(path, database_3d)
        activate_mean_calculations = activate_required_mean_plotter(path)

    elif type == "NPS":
        activate_nps = activate_required_nps(path, database)
        activate_uniformity = activate_required_uniformity(path)


def run_system():
    """All this do is check if database is there and if not creates and send for loadup"""
    print("Run System Activated !!\n\n")

    folder_container = []
    while True:
        location = decrypt_file()[1]['storage_location']
        for folder in os.listdir(location):
            if folder != "Mean":
                if folder not in folder_container:
                    folder_path = os.path.join(location, folder)
                    if os.path.isdir(folder_path):  # Check if it's a directory    
                        existing_files = set(os.listdir(folder_path))
                        kind = ""
                        if "processing_kind.txt" in existing_files:
                            with open(folder_path+"/processing_kind.txt", "r", encoding="utf-8") as process_kind:
                                kind = process_kind.read().strip()
                            if f"database_{kind}.csv" not in existing_files:
                                if kind == "MTF":
                                    df = pd.DataFrame(columns=['unique_id', 'folder_name', 'circle_name', 'applied_roi', 'avg_mtf', 'spacial_frequency'])
                                    df_3d = pd.DataFrame(columns=['unique_id', 'folder_name', 'mtf', 'spacial_f'])

                                    # create the part for mean calculations
                                    df_3d['unique_id'] = [str(uuid.uuid4()) for _ in range(len(df_3d))]
                                    df_3d.to_csv(f"{folder_path}/database_3dmtf.csv", index=False)


                                elif kind == "NPS":
                                    # Nps database creation here 
                                    df = pd.DataFrame(columns=['unique_id', 'folder_name', 'average_nps', 'spacial_frequency'])

                                    # For uniformity each Section
                                    df_uniformity = pd.DataFrame(columns=['unique_id', 'folder_name', 'slices','value'])
                                    df_uniformity['unique_id'] = [str(uuid.uuid4()) for _ in range(len(df_uniformity))]
                                    df_uniformity.to_csv(f"{folder_path}/database_uniformity.csv")


                                df['unique_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
                                df.to_csv(f"{folder_path}/database_{kind}.csv", index=False)  

                                arg_d2 = f"{folder_path}/database_3dmtf.csv" if kind == "MTF" else None

                                while True:
                                    files_present = any(os.path.isfile(os.path.join(location, f)) for f in os.listdir(location))
                                    if files_present:
                                        print("Files Are Still Present!!! and Processing")
                                        time.sleep(10)
                                    else:
                                        break

                                regulate_system_calculations(folder_path, f"{folder_path}/database_{kind}.csv", arg_d2, kind)
                            else:
                                pass
                        

def run_system_thread():
    # Thread
    runsys_thread = threading.Thread(target=run_system, daemon=True)
    runsys_thread.start()
    return runsys_thread
