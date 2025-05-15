import ast
import sys
import tkinter as tk
import pandas as pd
import numpy as np

# For image processing
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from uniformity.uniformity import activate_required_uniformity
from security import decrypt_file


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

list_of_section = []

def regenerate_folder_section(frame, database_folder):
    global list_of_section

    database_loc = database_folder.replace("\\", "/")+"/database_uniformity.csv"
    df_x = pd.read_csv(database_loc)
    df_empty = df_x.iloc[0:0]
    df_empty.to_csv(database_loc, index=False)


    activate_required_uniformity(database_folder)
    regenerated_respose = uniformity_section_builder(frame, regenerate_old=True)


def uniformity_builder(frame):
    # Create a canvas widget inside the frame
    canvas = tk.Canvas(frame, bg="white", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    # Create a scrollbar and link it to the canvas
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.config(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas for content
    inner_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # Configure scrolling for the canvas
    def configure_canvas(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def resize_canvas(event):
        canvas_width = event.width
        canvas.itemconfig(inner_frame_window, width=canvas_width)

    inner_frame.bind("<Configure>", configure_canvas)
    canvas.bind("<Configure>", resize_canvas)

    # Create a reference to the inner frame's window ID
    inner_frame_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    return [canvas, scrollbar, inner_frame]


def uniformity_section_builder(frame, regenerate_old=False):
        global list_of_section

        path = decrypt_file()[1]['storage_location']
        if regenerate_old:
            for packed_folder_section in list_of_section:
                packed_folder_section.destroy()
            list_of_section = []

        for folder in os.listdir(path):
            if "Mean" != folder:
                folder_location = os.path.join(path, folder)
                kind = open(os.path.join(folder_location, "processing_kind.txt"), 'r', encoding="utf-8").read().strip()
                
                if kind == "NPS":
                    # Open uniformity csv of the folder
                    # Do same No graph just text of the mean average
                    df = pd.read_csv(os.path.join(folder_location, "database_uniformity.csv"))

                    folder_frame = tk.Frame(frame, bg=bg_color)
                    folder_frame.pack(side="top", fill="x", pady=2)

                    folder_name = folder.replace("_", "-")
                    folder_name_frame = tk.Label(folder_frame, text=folder_name, bg="#000000", fg="#ffffff", anchor="center")
                    folder_name_frame.pack(side="top", fill="x", pady=5)

                    

                    # Add fancy text with shadow effect
                    slices = ""
                    average_uniformity = ""
                    for index, row in df.iterrows():
                        slices = row['slices']
                        average_uniformity = row['value']

                    # canvas = tk.Canvas(folder_frame, width=200, height=200, bg="black", highlightthickness=0)
                    # canvas.pack()

                    # canvas.create_text(200, 90, text=f"Slices : {str(slices)}", font=("Arial", 30, "bold"), fill="white")
                    # canvas.create_text(202, 102, text=f"Average Uniformity Computed : {str(average_uniformity)}", font=("Arial", 30, "bold"), fill="gray")  # Shadow
                    # canvas.create_text(200, 100, text=f"Average Uniformity Computed : {str(average_uniformity)}", font=("Arial", 30, "bold"), fill="white")  # Main text
                    label = tk.Label(
                        folder_frame,
                        text=f"Slices: {slices}\nAverage Uniformity: {average_uniformity}",
                        font=("Arial", 20, "bold"),
                        fg="white",
                        bg="black",
                    )
                    label.pack(pady=20)


                    # Regenerate button
                    regenerate_button = tk.Button(
                        folder_frame,
                        text="⟳ Regenerate",  # Unicode refresh symbol
                        font=("Segoe UI", 10, "bold"),
                        bg="#27ae60",  # Green color
                        fg="white",
                        activebackground="#219a52",
                        relief="flat",
                        command=lambda fl=folder_location: regenerate_folder_section(frame, fl)
                    )
                    regenerate_button.pack(side="top", pady=8, ipadx=12)

                    list_of_section.append(folder_frame)