import ast
import sys
import tkinter as tk
import pandas as pd

# For image processing
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security import decrypt_file
from three_dmtf.mtf_3d import activate_required_3d_mtf


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

    database_loc = database_folder.replace("\\", "/")+"/database_3dmtf.csv"
    df_x = pd.read_csv(database_loc)
    df_empty = df_x.iloc[0:0]
    df_empty.to_csv(database_loc, index=False)


    activate_required_3d_mtf(database_folder, database_loc)
    regenerated_respose = mtf_section_builder_3d(frame, regenerate_old=True)


def mtf_canvas_builder_3d(frame):
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

    
def mtf_section_builder_3d(frame, regenerate_old=False, *args):
    global list_of_section

    path = decrypt_file()[1]['storage_location']
    if regenerate_old:
        for packed_folder_section in list_of_section:
            packed_folder_section.destroy()

        list_of_section = []

    for folder in os.listdir(path):
        if folder != "Mean":
            folder_location = os.path.join(path, folder)
            kind = open(os.path.join(folder_location, "processing_kind.txt"), 'r', encoding="utf-8").read().strip()
            
            if kind == "MTF":
                df = pd.read_csv(os.path.join(folder_location, "database_3dmtf.csv"))
                folder_frame = tk.Frame(frame, bg=bg_color)
                folder_frame.pack(side="top", fill="x", pady=2)

                folder_name = folder.replace("_", "-")
                folder_name_frame = tk.Label(folder_frame, text=folder_name, bg="#000000", fg="#ffffff", anchor="center")
                folder_name_frame.pack(side="top", fill="x", pady=5)

                graph_row_frame = None
                for index, row in df.iterrows():
                    # if index % 2 == 0:  # Create a new row frame for every 2 graphs
                    graph_row_frame = tk.Frame(folder_frame, bg=bg_color)
                    graph_row_frame.pack(side="top", fill="x", pady=5)

                    mtf = ast.literal_eval(row["mtf"])
                    spatial_frequency = ast.literal_eval(row["spacial_f"])
                    
                    fig = Figure(figsize=(6, 4), dpi=100)  # Adjust figsize for better aspect ratio
                    plot = fig.add_subplot(111)
                    plot.plot(spatial_frequency[:len(spatial_frequency)//2], mtf[:len(mtf)//2], label="MTF Curve")
                    
                    plot.set_title("3D MTF Curve")
                    plot.set_xlabel("Spatial Frequency (cycles/mm)")
                    plot.set_ylabel("MTF (Normalized)")
                    plot.grid(True)
                    plot.legend()

                    graph = FigureCanvasTkAgg(fig, master=graph_row_frame)
                    graph.draw()
                    graph.get_tk_widget().pack(side="left", fill="both", expand=True, padx=0)

                # Add Regenerate button after graphs
                regenerate_button = tk.Button(
                    folder_frame,
                    text="Regenerate",
                    font=("Helvetica", 12),
                    bg="#333333",  # Dark grey background
                    fg="#FFFFFF",  # White text
                    activebackground="#555555",
                    activeforeground="#EEEEEE",
                    padx=10,
                    pady=5,
                    relief="flat",
                    command=lambda folder_location=folder_location: regenerate_folder_section(frame, folder_location)
                )
                regenerate_button.pack(side="top", fill="y", pady=10)

                list_of_section.append(folder_frame)
