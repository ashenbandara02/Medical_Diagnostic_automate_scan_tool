import sys
import tkinter as tk
from tkinter import ttk, filedialog
import json

# For image processing
import os
import threading
import time
from tkinter import PhotoImage, Label
import pydicom
from PIL import Image, ImageTk


# For Login !
from security import encrypt_userdata, encrypt_settings, decrypt_file, replace_set, replace_password 

# For Other Essentials
from eyekeeper import start_monitoring_for_uploads
from check_run_system import run_system_thread

from sector_display.twod_mtf_sector import mtf_canvas_builder, mtf_section_builder
from sector_display.threed_mtf_sector import mtf_canvas_builder_3d, mtf_section_builder_3d
from sector_display.nps_sector import mtf_nps_builder, nps_section_builder
from sector_display.mean_sector import mean_plotter_builder, mean_section_builder
from sector_display.uniformity_sector import uniformity_builder ,uniformity_section_builder

# Initialize the main application window
root = tk.Tk()
root.title("Medical Application")
root.geometry("800x600")


# Define colors and styles
theme_colors = {
    "bg_color": "#F4F6F7",
    "sidebar_color": "#2C3E50",
    "other_sections": "#42668a",
    "btn_color": "#3498DB",
    "btn_fg_color": "#FFFFFF",
    "btn_hover_color": "#5DADE2",
    "popup_bg_color": "#ECF0F1",
    "entry_bg_color": "#FFFFFF",
    "entry_fg_color": "#2C3E50",
}


# Other colors
bg_color = "#F7F9F9"  # Background color
sidebar_color = "#2C3E50"  # Sidebar color
btn_color = "#34495E"  # Button color
btn_fg_color = "#FFFFFF"  # Button text color
btn_hover_color = "#1ABC9C"  # Button hover color
login_btn_bg = "#1ABC9C"
login_btn_fg = "#FFFFFF"
loginfailedpopup_bg_color = "#FA8072"


# Automated Path
automated_file_path = (decrypt_file()[1])['storage_location']

# Global variable to hold displayed images
dicom_images = []
dicom_images_loader = []
dicom_container = []

# Folder containers
folder_container = []

# Thread on work
thread_on_work = False
upload_monitor_thread_on_work = False

workflow_thread = False

# Workspace Adjuestion
current_workspace = ""


# Check Login
logged_in_guest = False
logged_in_admin = False


######################################3
#Essential Work Vars
mtf_container = []
three_dmtf_container = []
nps_container = []
nps_3d_container = []
mean_container = []
uniformity_container = []



# Sidebar Frame
sidebar = tk.Frame(root, bg=sidebar_color, width=200)
sidebar.pack(side="left", fill="y", expand=False)


# Sidebar Buttons
def create_sidebar_button(text, command=None, state=tk.NORMAL):
    btn = tk.Button(
        sidebar,
        text=text,
        bg=btn_color,
        fg=btn_fg_color,
        font=("Arial", 12, "bold"),
        relief="flat",
        state=state,
        cursor="hand2",
        activebackground=btn_hover_color,
        activeforeground=btn_fg_color,
        command=command
    )
    btn.pack(fill="x", pady=5, padx=10)
    return btn


buttons = ["Home", "NPS", "3D-NPS", "2D-MTF", "3D-MTF", "Mean-Calculation", "Uniformity", "Settings"]

btn_container = []

for i, btn_text in enumerate(buttons):
    if btn_text == "Home":
        per_btn = create_sidebar_button(btn_text, state=tk.NORMAL)
        btn_container.append(per_btn)
    else:
        per_btn = create_sidebar_button(btn_text, state=tk.DISABLED)
        btn_container.append(per_btn)


# Add a profile icon and login button at the top of the sidebar
profile_frame = tk.Frame(sidebar, bg=sidebar_color)
profile_frame.pack(side="bottom", fill="x", pady=15)

login_button = tk.Button(
    profile_frame,
    text="Login",
    font=("Arial", 12, "bold"),
    bg=login_btn_bg,
    fg=login_btn_fg,
    relief="flat",
    cursor="hand2",
    activebackground=btn_hover_color,
    activeforeground=btn_fg_color
)
login_button.pack(side="bottom", pady=5, padx=10)


# Workspace Area
workspace = tk.Frame(root, bg=bg_color)
workspace.pack(side="right", fill="both", expand=True)

welcome_message = "Please login to the application to use"
welcome_text_box = tk.Text(workspace, height=2, width=40, wrap=tk.WORD, bd=0, fg=theme_colors["btn_fg_color"], font=("Arial", 16, "bold"), bg="#333131", padx=20, pady=10)
welcome_text_box.insert(tk.END, welcome_message)
welcome_text_box.config(state=tk.DISABLED)
welcome_text_box.tag_configure("center", justify="center")
welcome_text_box.tag_add("center", "1.0", "end")
welcome_text_box.pack(expand=True, fill="both")




# Essential Display block codes
#-----home-------
# Create a canvas widget inside the workspace for scrolling
canvas = tk.Canvas(workspace, bg=bg_color, state=tk.DISABLED)
canvas.pack_forget()

# Create a scrollbar and link it to the canvas
scrollbar = tk.Scrollbar(workspace, orient="vertical", command=canvas.yview)
scrollbar.pack_forget()
canvas.config(yscrollcommand=scrollbar.set)

scrollbarx = tk.Scrollbar(workspace, orient="horizontal", command=canvas.xview)
scrollbarx.pack_forget()
canvas.config(xscrollcommand=scrollbarx.set)

# Create a frame to hold images and add it to the canvas
image_frame = tk.Frame(canvas, bg=bg_color, pady=30)

canvas.create_window((0, 0), window=image_frame, anchor="nw")


images_loader_message = "--Images Loaded--"
image_loader = tk.Text(
    workspace, 
    height=2,  # Minimal height
    wrap=tk.WORD, 
    bd=0, 
    fg=theme_colors["btn_fg_color"], 
    font=("Arial", 16, "bold"), 
    bg="#333131", 
    padx=20, 
    pady=10
)
image_loader.insert(tk.END, images_loader_message)
image_loader.config(state=tk.DISABLED)
image_loader.tag_configure("center", justify="center")
image_loader.tag_add("center", "1.0", "end")
image_loader.pack_forget()



#########################################################################################################################
#--------------------------------------------------------Settings--------------------------------------------------------
#########################################################################################################################


path = False
nps = False
mtf = False
threed_mtf_changes = False
mean_changes = False
uniformity_changes = False


current_settings = (decrypt_file()[1]) # {'storage_location': 'C:/Users/ashen/OneDrive/Desktop/pictures', 'nps': [] etc}
new_settings = current_settings

def select_path():
    global path 

    path_dir = filedialog.askdirectory()  # Ask user to select a directory
    if path_dir:
        path_label.config(text=path_dir)  # Display the selected path
        new_settings['storage_location'] = path_dir
        path = True

def re_update_settings():
    """args has order storage, nps etc can have non too"""
    global automated_file_path, path, nps, mtf
    if path:
        path = False
        current_settings['storage_location'] = new_settings['storage_location']
        
        automated_file_path = current_settings['storage_location']

    if nps:
        nps = False
        current_settings['nps'] = new_settings['nps']

    if mtf:
        mtf = False
        current_settings['mtf'] = new_settings['mtf']

    if threed_mtf_changes:
        threed_mtf_changes = False
        current_settings['mtf_3d'] = new_settings['mtf_3d']

    if mean_changes:
        mean_changes = False
        current_settings['mean'] = new_settings['mean']

    if uniformity_changes:
        uniformity_changes = False
        current_settings['uniformity'] = new_settings['uniformity']
    
    
    replace_set(current_settings)
    restart_popup() 

# Frame A (Holds main container)
settings_holder = tk.Frame(workspace, height=200, bg=sidebar_color)
settings_holder.pack_forget()

# Frame 1(storage location change)
storage_field = tk.Frame(settings_holder, height=200, bg=sidebar_color)
storage_field.pack_forget()

select_button = tk.Button(storage_field, 
                        text="Select Path of Images", 
                        bg=btn_color,
                        fg=btn_fg_color,
                        font=("Arial", 12, "bold"),
                        relief="flat",
                        cursor="hand2",
                        activebackground=btn_hover_color,
                        activeforeground=btn_fg_color,
                        command=select_path)

select_button.pack_forget()
path_label = tk.Label(storage_field,
                    text=automated_file_path, 
                    wraplength=300,

                    )
path_label.pack_forget()

# Parent Frame of 1,2
nps_mtf_holder = tk.Frame(workspace, height=400, bg=theme_colors['other_sections'])
nps_mtf_holder.pack_forget()

# Frame 2(nps details)
def create_nps_settings_frame(parent):
    """Creates the NPS Settings frame with the specified layout."""

    # Create the frame
    nps_settings_holder = tk.Frame(parent, height=400, bg=theme_colors['other_sections'])  # Replace with your desired background color

    # Create and grid the widgets
    tk.Label(nps_settings_holder, text="Noise power spectrum, NNPS (f)", fg="white",  bg=theme_colors['other_sections']).grid(row=0, column=0, columnspan=2, pady=10)

    # Distance from centre to records label and entry
    tk.Label(nps_settings_holder, text="Distance from centre to records (mm)", fg="white",  bg=theme_colors['other_sections']).grid(row=1, column=0, sticky="w")
    distance_entry = tk.Entry(nps_settings_holder, width=10)
    distance_entry.grid(row=1, column=1, sticky="w")
    distance_entry.insert(0, current_settings["nps"]["dist_c_to_record"])  # Default value

    # Roi Size
    tk.Label(nps_settings_holder, text="ROI size (height, width)", fg="white",  bg=theme_colors['other_sections']).grid(row=2, column=0, sticky="w")
    roi_size = tk.Entry(nps_settings_holder, width=10)
    roi_size.grid(row=2, column=1, sticky="w")
    roi_size.insert(0, current_settings["nps"]["roi_size"])  # Default value

    
    # Number of records label and entry
    tk.Label(nps_settings_holder, text="Number of rois", fg="white",  bg=theme_colors['other_sections']).grid(row=3, column=0, sticky="w")
    num_rois = tk.Entry(nps_settings_holder, width=10)
    num_rois.grid(row=3, column=1, sticky="w")
    num_rois.insert(0, current_settings["nps"]["no_of_rois"])  # Default value

    # Record size label and entry
    tk.Label(nps_settings_holder, text="Record size (pixels), must be a power of 2", fg="white",  bg=theme_colors['other_sections']).grid(row=4, column=0, sticky="w")
    record_size_entry = tk.Entry(nps_settings_holder, width=10)
    record_size_entry.grid(row=4, column=1, sticky="w")
    record_size_entry.insert(0, current_settings["nps"]["record_size"])  # Default value

    # Frequency rebin increment label and entry
    tk.Label(nps_settings_holder, text="Frequency rebin increment (mm^-1)", fg="white",  bg=theme_colors['other_sections']).grid(row=5, column=0, sticky="w")
    frequency_rebin_entry = tk.Entry(nps_settings_holder, width=10)
    frequency_rebin_entry.grid(row=5, column=1, sticky="w")
    frequency_rebin_entry.insert(0, current_settings["nps"]["f_rebin_increment"])  # Default value

    # Run on the average stack checkbox
    run_on_average_stack_var = tk.BooleanVar(value=current_settings["nps"]["run_avg_stack"])
    run_on_average_stack_check = tk.Checkbutton(nps_settings_holder, text="Run on the average stack", variable=run_on_average_stack_var)
    run_on_average_stack_check.grid(row=6, column=0, sticky="w")
    

    # Min and max slice index labels and entries
    tk.Label(nps_settings_holder, text="Min slice index", fg="white",  bg=theme_colors['other_sections']).grid(row=7, column=0, sticky="w")
    min_slice_index_entry = tk.Entry(nps_settings_holder, width=10)
    min_slice_index_entry.grid(row=7, column=1, sticky="w")
    min_slice_index_entry.insert(0, current_settings["nps"]["min_slice"])  # Default value

    tk.Label(nps_settings_holder, text="to max slice index", fg="white",  bg=theme_colors['other_sections']).grid(row=8, column=0, sticky="w")
    max_slice_index_entry = tk.Entry(nps_settings_holder, width=10)
    max_slice_index_entry.grid(row=8, column=1, sticky="w")
    max_slice_index_entry.insert(0, current_settings["nps"]["max_slice"])  # Default value

    # OK and Cancel buttons
    ok_button = ttk.Button(nps_settings_holder, text="OK")
    ok_button.grid(row=9, column=0, pady=10)
    
    def get_nps_settings():
        global nps
        distance_value = distance_entry.get()
        num_rois_value = num_rois.get()
        roi_size_value = roi_size.get()
        record_size_value = record_size_entry.get()
        frequency_rebin_value = frequency_rebin_entry.get()
        run_on_average_stack_value = run_on_average_stack_var.get()
        min_slice_index_value = min_slice_index_entry.get()
        max_slice_index_value = max_slice_index_entry.get()

        # Do something with the collected values
        data_config = {
            "no_of_rois": num_rois_value,
            "roi_size": roi_size_value,
            "dist_c_to_record": distance_value,
            "record_size": record_size_value,
            "f_rebin_increment": frequency_rebin_value,
            "run_avg_stack": run_on_average_stack_value,
            "min_slice": min_slice_index_value,
            "max_slice": max_slice_index_value
            }
        
        nps = True
        new_settings['nps'] = data_config

        

    # Bind the "OK" button to the get_nps_settings function
    ok_button.configure(command=get_nps_settings)

    return nps_settings_holder

nps_settings_holder = create_nps_settings_frame(nps_mtf_holder)
nps_settings_holder.pack_forget()

# Frame 3(mtf)
def create_mtf_settings_frame(parent):
    """Creates the MTF Settings frame with the specified layout."""

    # Create the frame
    mtf_settings_holder = tk.Frame(parent, height=400, bg=theme_colors['other_sections'])

    # Create and grid the widgets
    tk.Label(mtf_settings_holder, text="Task transfer function, TTF(f)", fg="white", bg=theme_colors['other_sections']).grid(row=0, column=0, columnspan=2, pady=10)

    # Object diameter label and entry
    tk.Label(mtf_settings_holder, text="Object diameter (mm) [Mercury 25, Catphan 12]", fg="white", bg=theme_colors['other_sections']).grid(row=1, column=0, sticky="w")
    object_diameter_entry = tk.Entry(mtf_settings_holder, width=10)
    object_diameter_entry.grid(row=1, column=1, sticky="w")
    object_diameter_entry.insert(0, current_settings["mtf"]["obj_diameter"])

    # circle 1
    tk.Label(mtf_settings_holder, text="Circle 1 {y1, y2} {x1, x2}", fg="white", bg=theme_colors['other_sections']).grid(row=2, column=0, sticky="w")
    object_diameter_entry_circle_1 = tk.Entry(mtf_settings_holder, width=20)
    object_diameter_entry_circle_1.grid(row=2, column=1, sticky="w")
    object_diameter_entry_circle_1.insert(0, current_settings["mtf"]["circle_1"])

    # circle 2
    tk.Label(mtf_settings_holder, text="Circle 2", fg="white", bg=theme_colors['other_sections']).grid(row=3, column=0, sticky="w")
    object_diameter_entry_circle_2 = tk.Entry(mtf_settings_holder, width=20)
    object_diameter_entry_circle_2.grid(row=3, column=1, sticky="w")
    object_diameter_entry_circle_2.insert(0, current_settings["mtf"]["circle_2"])

    # circle 3
    tk.Label(mtf_settings_holder, text="Circle 3", fg="white", bg=theme_colors['other_sections']).grid(row=4, column=0, sticky="w")
    object_diameter_entry_circle_3 = tk.Entry(mtf_settings_holder, width=20)
    object_diameter_entry_circle_3.grid(row=4, column=1, sticky="w")
    object_diameter_entry_circle_3.insert(0, current_settings["mtf"]["circle_3"])

    # circle 4
    tk.Label(mtf_settings_holder, text="Circle 4", fg="white", bg=theme_colors['other_sections']).grid(row=5, column=0, sticky="w")
    object_diameter_entry_circle_4 = tk.Entry(mtf_settings_holder, width=20)
    object_diameter_entry_circle_4.grid(row=5, column=1, sticky="w")
    object_diameter_entry_circle_4.insert(0, current_settings["mtf"]["circle_4"])

    # circle 5
    tk.Label(mtf_settings_holder, text="Circle 5", fg="white", bg=theme_colors['other_sections']).grid(row=6, column=0, sticky="w")
    object_diameter_entry_circle_5 = tk.Entry(mtf_settings_holder, width=20)
    object_diameter_entry_circle_5.grid(row=6, column=1, sticky="w")
    object_diameter_entry_circle_5.insert(0, current_settings["mtf"]["circle_5"])

    # Pixel reduction factor label and entry
    tk.Label(mtf_settings_holder, text="Pixel reduction factor", fg="white", bg=theme_colors['other_sections']).grid(row=7, column=0, sticky="w")
    pixel_reduction_entry = tk.Entry(mtf_settings_holder, width=10)
    pixel_reduction_entry.grid(row=7, column=1, sticky="w")
    pixel_reduction_entry.insert(0, current_settings["mtf"]["pixel_red_factor"])

    # Frequency rebin increment label and entry
    tk.Label(mtf_settings_holder, text="Frequency rebin increment (mm^-1)", fg="white", bg=theme_colors['other_sections']).grid(row=8, column=0, sticky="w")
    frequency_rebin_entry = tk.Entry(mtf_settings_holder, width=10)
    frequency_rebin_entry.grid(row=8, column=1, sticky="w")
    frequency_rebin_entry.insert(0, current_settings["mtf"]["f_rebin_increment"])

    # # Find centre of mass checkbox
    # find_center_of_mass_var = tk.BooleanVar(value=current_settings["mtf"]["find_center_of_mass"])
    # find_center_of_mass_check = tk.Checkbutton(mtf_settings_holder, text="Find centre of mass", variable=find_center_of_mass_var)
    # find_center_of_mass_check.grid(row=4, column=0, sticky="w")



    # Run on the average stack checkbox
    run_on_average_stack_var = tk.BooleanVar(value=current_settings["mtf"]["run_avg_stack"])
    run_on_average_stack_check = tk.Checkbutton(mtf_settings_holder, text="Run on the average stack", variable=run_on_average_stack_var)
    run_on_average_stack_check.grid(row=9, column=0, sticky="w")

    # Min and max slice index labels and entries
    tk.Label(mtf_settings_holder, text="Min slice index", fg="white", bg=theme_colors['other_sections']).grid(row=10, column=0, sticky="w")
    min_slice_index_entry = tk.Entry(mtf_settings_holder, width=10)
    min_slice_index_entry.grid(row=10, column=1, sticky="w")
    min_slice_index_entry.insert(0, current_settings["mtf"]["min_slice"])

    tk.Label(mtf_settings_holder, text="to max slice index", fg="white", bg=theme_colors['other_sections']).grid(row=11, column=0, sticky="w")
    max_slice_index_entry = tk.Entry(mtf_settings_holder, width=10)
    max_slice_index_entry.grid(row=11, column=1, sticky="w")
    max_slice_index_entry.insert(0, current_settings["mtf"]["max_slice"])

    # OK and Cancel buttons
    ok_button = ttk.Button(mtf_settings_holder, text="OK")
    ok_button.grid(row=12, column=0, pady=10)

    def get_mtf_settings():
        global mtf
        object_diameter_value = object_diameter_entry.get()

        object_diameter_entry_circle_1_value = object_diameter_entry_circle_1.get()
        object_diameter_entry_circle_2_value = object_diameter_entry_circle_2.get()
        object_diameter_entry_circle_3_value = object_diameter_entry_circle_3.get()
        object_diameter_entry_circle_4_value = object_diameter_entry_circle_4.get()
        object_diameter_entry_circle_5_value = object_diameter_entry_circle_5.get()


        pixel_reduction_value = pixel_reduction_entry.get()
        frequency_rebin_value = frequency_rebin_entry.get()
        #find_center_of_mass_value = find_center_of_mass_var.get()
        #show_advanced_options_value = show_advanced_options_var.get()
        run_on_average_stack_value = run_on_average_stack_var.get()
        min_slice_index_value = min_slice_index_entry.get()
        max_slice_index_value = max_slice_index_entry.get()

        data_config = {
            "obj_diameter": object_diameter_value,
            "circle_1": object_diameter_entry_circle_1_value,
            "circle_2": object_diameter_entry_circle_2_value,
            "circle_3": object_diameter_entry_circle_3_value,
            "circle_4": object_diameter_entry_circle_4_value,
            "circle_5": object_diameter_entry_circle_5_value,
            "pixel_red_factor": pixel_reduction_value,
            "f_rebin_increment": frequency_rebin_value,
            # "find_center_of_mass": find_center_of_mass_value,
            # "show_advanced_options": show_advanced_options_value,
            "run_avg_stack": run_on_average_stack_value,
            "min_slice": min_slice_index_value,
            "max_slice": max_slice_index_value
        }

        mtf = True
        new_settings['mtf'] = data_config

    ok_button.configure(command=get_mtf_settings)

    return mtf_settings_holder

mtf_settings_holder = create_mtf_settings_frame(nps_mtf_holder)
mtf_settings_holder.pack_forget()


# Save details Button
save_button_settings = tk.Button(workspace, 
                        text="Save Changes", 
                        bg="#0065d1",
                        fg=btn_fg_color,
                        font=("Arial", 12, "bold"),
                        relief="flat",
                        cursor="hand2",
                        activebackground=btn_hover_color,
                        activeforeground=btn_fg_color,
                        command=re_update_settings)
save_button_settings.pack_forget()
#################################################################################################################



def image_per_set_indicator(folder_name, current_row):
    folder_name = folder_name.replace("_", "-")
    display_folder_name = Label(image_frame, text=folder_name, bg="#000000", fg="#ffffff")
    display_folder_name.grid(row=current_row, column=0, padx=10, pady=0, sticky="nw")


# Update the scroll region of the canvas whenever new images are added
#------home---------
def update_scroll_region():
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# Image processing and thread functions
def load_dicom_image(filepath):
    """Load a DICOM file and return a PIL image."""
    try:
        dicom_data = pydicom.dcmread(filepath)
        if hasattr(dicom_data, 'pixel_array'):  # Check if pixel array exists
            pixel_array = dicom_data.pixel_array
            image = Image.fromarray(pixel_array)
            return image
        else:
            print(f"No pixel data found in DICOM file: {filepath}")
            return None
    except Exception as e:
        print(f"Error loading DICOM file {filepath}: {e}")
        return None

def update_home_with_image(image, image_file_name, current_row):
    """Update the home workspace with a new image."""
    default_width, default_height = 150, 150
    images_per_row = 100  # Define how many images per row

    global dicom_images
    global dicom_images_loader
    if image:
        resized_image = image.resize((default_width, default_height), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(resized_image)  # Convert to PhotoImage
        dicom_images.append(photo)  # Keep a reference to avoid garbage collection
        dicom_images_loader.append(photo)

        # Calculate the row and column index based on the total number of images
        row = current_row
        column = (len(dicom_images_loader) - 1) % images_per_row

        # Create a label for the image and place it in the grid
        img_label = Label(image_frame, image=photo, bg=bg_color)
        img_label.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        # Create a label for the text and place it below the image
        text_label = Label(image_frame, text=image_file_name, bg=bg_color, font=("Helvetica", 8))
        text_label.grid(row=row, column=column, padx=10, pady=5, sticky="s")  # Adjust row for text placement

        # Make sure each row has the same weight for resizing
        image_frame.grid_columnconfigure(column, weight=1, uniform="equal")
        image_frame.grid_rowconfigure(row, weight=1, uniform="equal")

        update_scroll_region()  # Update the scroll region after adding an image

def monitor_directory(directory):
    """Load all DICOM files in the directory"""
    global dicom_images_loader
    current_row = 0

    while True:
        for folder in os.listdir(directory):
            if folder != "Mean":
                if folder not in folder_container:
                    dicom_images_loader = []

                    folder_path = os.path.join(directory, folder)
                    if os.path.isdir(folder_path):  # Check if it's a directory
                        print(f"\nContents of folder: {folder}")
                        
                        existing_files = set(os.listdir(folder_path))
                        for file in existing_files:
                            full_path = os.path.join(folder_path, file)
                            print(f"Processing file: {full_path}")  
                            
                            try:
                                dicom_data = pydicom.dcmread(full_path, stop_before_pixels=True)  # Check if it's a valid DICOM file
                                image = load_dicom_image(full_path)  # Load image if valid DICOM
                                if image:
                                    update_home_with_image(image, str(file), current_row)  # Update the GUI with the image
                            except pydicom.errors.InvalidDicomError:
                                continue
                        
                        dicom_container.append({folder_path: existing_files})

                        image_per_set_indicator(folder, current_row) # display folder for identification
                    current_row = current_row + 1
                    folder_container.append(folder) # added the folder so it wont consider it 2 times after once
                else:
                    pass

        time.sleep(5)

def start_monitoring(): # Monitoring thread
    if thread_on_work and thread_on_work.is_alive():
        return thread_on_work
    else:
        monitor_thread = threading.Thread(target=monitor_directory, args=(automated_file_path,), daemon=True)
        monitor_thread.start()
        return monitor_thread


# Supportive functions
def restart_popup():
    # Create the restart popup
    restart = tk.Toplevel(root)
    restart.grab_set()  # Make the popup modal (it grabs focus)
    restart.title("Restart to Take Changes")
    restart.geometry("400x150")  # Adjusted size for the message and button
    restart.resizable(False, False)
    restart.configure(bg=theme_colors["popup_bg_color"])

    # Title Label
    tk.Label(
        restart, 
        text="Restart to Take Changes!!", 
        font=("Arial", 12, "bold"), 
        fg=loginfailedpopup_bg_color,
        bg=theme_colors["popup_bg_color"]
    ).pack(pady=15)

    # OK button to close the popup and exit the app
    def on_ok():
        restart.destroy()  # Close the popup
        sys.exit()  # Exit the application

    ok_button = tk.Button(restart, text="Close", command=on_ok)
    ok_button.pack(pady=10)

def del_greetins():
    welcome_text_box.destroy()

def login_success(user):
    login_button.destroy()
    logged = tk.Button(
        profile_frame,
        text=user,
        font=("Arial", 12, "bold"),
        bg=login_btn_bg,
        fg=login_btn_fg,
        relief="flat",
        cursor="hand2",
        state=tk.DISABLED,
        activebackground=loginfailedpopup_bg_color,
        activeforeground="#000000"
    )
    logged.pack(side="bottom", pady=5, padx=10)

    if logged_in_admin:
        # Enable all buttons
        for button_index, button in enumerate(btn_container):
            if button_index != 0:
                button['state'] = tk.NORMAL
                if button_index == 1:
                    button['command'] = nps_workspace
                # if button_index == 2:
                #     button['command'] = nps_3d_workspace
                if button_index == 3:
                    button['command'] = two_dmtf_workspace
                
                if button_index == 4:
                    button['command'] = three_d_mtf_workspace

                if button_index == 5:
                    button['command'] = mean_calculation_workspace

                if button_index == 6:
                    button['command'] = uniformity_workspace
                
                if button_index == 7:
                    button['command'] = settings_workspace
                
            else:
                button['command'] = home_workspace
        
    elif logged_in_guest:
        # Enable all buttons except settings
        for button_index, button in enumerate(btn_container):
            if button_index != 0 and button_index != 4:
                button['state'] = tk.NORMAL
            if button_index == 0:
                button['command'] = home_workspace
            if button_index == 1:
                button['command'] = nps_workspace
            # if button_index == 2:
            #     button['command'] = nps_3d_workspace
            if button_index == 3:
                button['command'] = two_dmtf_workspace
            if button_index == 4:
                button['command'] = three_d_mtf_workspace
            if button_index == 5:
                    button['command'] = mean_calculation_workspace
            if button_index == 6:
                    button['command'] = uniformity_workspace
    
    home_workspace()


# Essential Functions
def set_placeholder(entry, placeholder_text):
    entry.insert(0, placeholder_text)
    entry.config(fg="gray")

    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, "end")
            entry.config(fg=theme_colors["entry_fg_color"])

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.config(fg="gray")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

def show_login_popup():
    popup = tk.Toplevel(root)
    popup.grab_set()
    popup.title("Login")
    popup.geometry("400x300")
    popup.resizable(False, False)
    popup.configure(bg=theme_colors["popup_bg_color"])

    # Title
    tk.Label(
        popup, 
        text="User Login", 
        font=("Arial", 16, "bold"), 
        bg=theme_colors["popup_bg_color"],
        fg=btn_hover_color
    ).pack(pady=15)

    # Username Entry
    username_entry = tk.Entry(
        popup, 
        font=("Arial", 12), 
        bg=theme_colors["entry_bg_color"], 
        fg=theme_colors["entry_fg_color"], 
        relief="flat"
    )
    set_placeholder(username_entry, "Enter Username")
    username_entry.pack(pady=10, ipadx=5, ipady=8, padx=20, fill="x")

    # Password Entry
    password_entry = tk.Entry(
        popup, 
        font=("Arial", 12), 
        bg=theme_colors["entry_bg_color"], 
        fg=theme_colors["entry_fg_color"], 
        show="*", 
        relief="flat"
    )
    set_placeholder(password_entry, "Enter Password")
    password_entry.pack(pady=10, ipadx=5, ipady=8, padx=20, fill="x")

    # Buttons
    login_btn = tk.Button(
        popup, 
        text="Login", 
        font=("Arial", 12, "bold"), 
        bg=btn_hover_color, 
        fg=theme_colors["btn_fg_color"], 
        relief="flat", 
        cursor="hand2",
        activebackground=theme_colors["btn_hover_color"],
        activeforeground=theme_colors["btn_fg_color"],
        command=lambda: login_admin(username_entry, password_entry, popup)  # Pass entries
    )
    login_btn.pack(pady=10, ipadx=30, ipady=8)

    guest_btn = tk.Button(
        popup, 
        text="Guest", 
        font=("Arial", 12, "bold"), 
        bg=btn_hover_color, 
        fg=theme_colors["btn_fg_color"], 
        relief="flat", 
        cursor="hand2",
        activebackground=theme_colors["btn_hover_color"],
        activeforeground=theme_colors["btn_fg_color"],
        command=lambda: login_guest(popup)
    )
    guest_btn.pack(pady=5, ipadx=30, ipady=8)

def login_admin(username_entry, password_entry, popup):
    # Get the entered username and password
    global logged_in_admin

    username = username_entry.get()
    password = password_entry.get()
    admin_data = decrypt_file()[0]

    admin_user = admin_data['admin']
    admin_passw = admin_data['pass']
    if admin_user == username and admin_passw == password:
        logged_in_admin = True
        popup.destroy()
        del_greetins()
        login_success(admin_user)
    else:
        logfailed_popup = tk.Toplevel(root)
        logfailed_popup.grab_set()
        logfailed_popup.title("Invalid")
        logfailed_popup.geometry("400x50")
        logfailed_popup.resizable(False, False)
        logfailed_popup.configure(bg=theme_colors["popup_bg_color"])

        # Title
        tk.Label(
            logfailed_popup, 
            text="Invalid details, Check Again!", 
            font=("Arial", 10, "bold"), 
            fg=loginfailedpopup_bg_color
        ).pack(pady=15)

def login_guest(popup):
    global logged_in_guest
    logged_in_guest = True
    popup.destroy()
    del_greetins()
    login_success("Guest")

def check_folders_and_do_system():
    global workflow_thread

    if workflow_thread:
        pass
    else:
        workflow_thread = run_system_thread()

def forget_all_packs():
    global mtf_container
    global three_dmtf_container
    global nps_container
    global mean_container
    global uniformity_container
    global nps_3d_container

    try:
        image_loader.pack_forget()
        canvas.pack_forget()
        scrollbar.pack_forget()
        scrollbarx.pack_forget()

        settings_holder.pack_forget()
        storage_field.pack_forget()
        select_button.pack_forget()
        path_label.pack_forget()

        nps_mtf_holder.pack_forget()
        nps_settings_holder.pack_forget()
        mtf_settings_holder.pack_forget()
        save_button_settings.pack_forget()

        for x in mtf_container:
            x.pack_forget()
        for y in three_dmtf_container:
            y.pack_forget()
        for z in nps_container:
            z.pack_forget()
        for u in nps_3d_container:
            u.pack_forget()
        for a in mean_container:
            a.pack_forget()
        for b in uniformity_container:
            b.pack_forget()


        mtf_container = []
        three_dmtf_container = []
        nps_container = []
        mean_container = []
        uniformity_container = []

    except Exception as e:
        print(e)
        pass


# Functions
def uniformity_workspace():
    global current_workspace

    if current_workspace != "uniformity":
        forget_all_packs()
        canvas_uniformity, scrollbar_uniformity, innerframe_uniformity = uniformity_builder(workspace)
        uniformity_section_builder(innerframe_uniformity)

        uniformity_container.append(innerframe_uniformity)
        uniformity_container.append(scrollbar_uniformity)
        uniformity_container.append(canvas_uniformity)

    current_workspace = "uniformity"

def mean_calculation_workspace():
    global current_workspace

    if current_workspace != "mean_plotter":
        forget_all_packs()
        canvas_mean, scrollbar_mean, innerframe_mean = mean_plotter_builder(workspace)
        mean_section_builder(innerframe_mean)

        mean_container.append(innerframe_mean)
        mean_container.append(scrollbar_mean)
        mean_container.append(canvas_mean)

    current_workspace = "mean_plotter"
    
def nps_workspace():
    global current_workspace

    if current_workspace != "nps":
        forget_all_packs()
        canvas_nps, scrollbar_nps, innerframe_nps = mtf_nps_builder(workspace)
        nps_section_builder(innerframe_nps)

        nps_container.append(innerframe_nps)
        nps_container.append(scrollbar_nps)
        nps_container.append(canvas_nps)

    current_workspace = "nps"

# def nps_3d_workspace():
#     global current_workspace
#     global nps_3d_container

#     if current_workspace != "3d_nps":
#         forget_all_packs()
#         canvas_nps_3d, scrollbar_nps_3d, innerframe_3d_nps = nps_canvas_builder_3d(workspace)

#         nps_section_builder_3d(innerframe_3d_nps)
        
#         nps_3d_container.append(innerframe_3d_nps)
#         nps_3d_container.append(scrollbar_nps_3d)
#         nps_3d_container.append(canvas_nps_3d)

#     current_workspace = "3d_nps"


def three_d_mtf_workspace():
    global current_workspace
    global three_dmtf_container

    if current_workspace != "3d_mtf":
        forget_all_packs()
        canvas_mtf_3d, scrollbar_mtf_3d, innerframe_3d = mtf_canvas_builder_3d(workspace)

        mtf_section_builder_3d(innerframe_3d)
        
        three_dmtf_container.append(innerframe_3d)
        three_dmtf_container.append(scrollbar_mtf_3d)
        three_dmtf_container.append(canvas_mtf_3d)

    current_workspace = "3d_mtf"

def two_dmtf_workspace():
    global current_workspace
    global mtf_container

    if current_workspace != "2d-mtf":
        forget_all_packs()
        canvas_mtf, scrollbar_mtf, innerframe = mtf_canvas_builder(workspace)

        mtf_section_builder(innerframe)
        
        mtf_container.append(canvas_mtf)
        mtf_container.append(scrollbar_mtf)
        mtf_container.append(innerframe)

        # canvas_mtf.pack(side="left", fill="both", expand=True)
        # scrollbar_mtf.pack(side="right", fill="y")

    current_workspace = "2d-mtf"

def settings_workspace():
    global current_workspace

    if current_workspace != "settings":
        forget_all_packs()

        settings_holder.pack(fill="x")
        storage_field.pack(padx=5, pady=2, fill="x")
        select_button.pack(side="left", pady=20, expand=True)
        path_label.pack(side="left", pady=10, expand=True)

        nps_mtf_holder.pack(pady=2, fill="x")
        nps_settings_holder.pack(fill="y", side="left", expand=True)
        mtf_settings_holder.pack(fill="y", side="left", expand=True)
        save_button_settings.pack(pady=10)

    current_workspace = "settings"

def home_workspace():
    global thread_on_work
    global upload_monitor_thread_on_work

    global current_workspace
    
    if current_workspace != "home":
        forget_all_packs()

        
        image_loader.pack()
        scrollbarx.pack(side="top", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    # Display Images Message
    if not upload_monitor_thread_on_work:
        upload_monitor_thread_on_work = start_monitoring_for_uploads(automated_file_path)
    
    thread_on_work = start_monitoring() # Does self manual checking if thread is already running!
    
    if thread_on_work: # we must only proceed if folders are created etc
        system_thread = check_folders_and_do_system()
    
    current_workspace = "home"
    

login_button.configure(command=show_login_popup)
root.mainloop()

