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

from security import decrypt_file
from nps.nps import activate_required_nps

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

    database_loc = database_folder.replace("\\", "/")+"/database_NPS.csv"
    df_x = pd.read_csv(database_loc)
    df_empty = df_x.iloc[0:0]
    df_empty.to_csv(database_loc, index=False)


    activate_required_nps(database_folder, database_loc)
    regenerated_respose = nps_section_builder(frame, regenerate_old=True)


def mtf_nps_builder(frame):
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


    
def nps_section_builder(frame, regenerate_old=False):
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
                df = pd.read_csv(os.path.join(folder_location, "database_NPS.csv"))
                folder_frame = tk.Frame(frame, bg=bg_color)
                folder_frame.pack(side="top", fill="x", pady=2)

                folder_name = folder.replace("_", "-")
                folder_name_frame = tk.Label(folder_frame, text=folder_name, bg="#000000", fg="#ffffff", anchor="center")
                folder_name_frame.pack(side="top", fill="x", pady=5)

                graph_row_frame = None

                for index, row in df.iterrows():
                    graph_row_frame = tk.Frame(folder_frame, bg=bg_color)
                    graph_row_frame.pack(side="top", fill="x", pady=5)

                    average_nps = np.loadtxt(row["average_nps"].split(';'), delimiter=',')
                    spatial_freq = np.loadtxt(row["spacial_frequency"].split(';'), delimiter=',')

                    fig = Figure(figsize=(6, 4), dpi=100)
                    plot = fig.add_subplot(111)

                    plot.plot(spatial_freq, average_nps, label="NPS Curve", color='#3498db')

                    # Styling
                    plot.set_title("Noise Power Spectrum", fontsize=12, pad=15)
                    plot.set_xlabel("Spatial Frequency (cycles/mm)", fontsize=10)
                    plot.set_ylabel("NPS (HU² mm²)", fontsize=10)
                    plot.grid(True, alpha=0.3)
                    plot.legend(frameon=False)

                    # Set both x and y axis limits to start from 0
                    plot.set_xlim(left=0)  # Set the minimum value of x-axis to 0
                    plot.set_ylim(bottom=0)  # Set the minimum value of y-axis to 0

                    # Remove zero tick from one of the axes (e.g., y-axis)
                    plot.set_yticks([tick for tick in plot.get_yticks() if tick != 0])

                    fig.tight_layout()

                    # Embed plot in Tkinter
                    graph = FigureCanvasTkAgg(fig, master=graph_row_frame)
                    graph.draw()
                    graph.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10)


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