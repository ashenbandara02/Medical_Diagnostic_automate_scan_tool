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
from mean.mean import rerun_worker_mean

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

def regenerate_folder_section(frame):
    global list_of_section

    rerun_worker_mean()
    regenerated_respose = mean_section_builder(frame, regenerate_old=True)

def mean_plotter_builder(frame):
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
  
def mean_section_builder(frame, regenerate_old=False, *args):
    global list_of_section

    path = decrypt_file()[1]['storage_location']
    if regenerate_old:
        for packed_folder_section in list_of_section:
            packed_folder_section.destroy()
        list_of_section = []

    graph_row_frame = tk.Frame(frame, bg=bg_color)
    graph_row_frame.pack(side="top", fill="x", pady=5)

    fig = Figure(figsize=(10, 6), dpi=100)
    plot = fig.add_subplot(111)

    for folder in os.listdir(path):
        if folder != "Mean":
            folder_location = os.path.join(path, folder)
            kind = open(os.path.join(folder_location, "processing_kind.txt"), 'r', encoding="utf-8").read().strip()
            
            if kind == "MTF":
                df_perpex = pd.read_csv(os.path.join(path+"/Mean", "database_MEAN_1.csv"))
                df_teflon = pd.read_csv(os.path.join(path+"/Mean", "database_MEAN_2.csv"))
                df_polyethylene = pd.read_csv(os.path.join(path+"/Mean", "database_MEAN_3.csv"))
                df_nylon = pd.read_csv(os.path.join(path+"/Mean", "database_MEAN_4.csv"))
                df_air = pd.read_csv(os.path.join(path+"/Mean", "database_MEAN_5.csv"))

                databases_mean = [
                    (df_perpex, 'blue', 'Perpex'),
                    (df_teflon, 'green', 'Teflon'),
                    (df_polyethylene, 'red', 'Polyethylene'),
                    (df_nylon, 'orange', 'Nylon'),
                    (df_air, 'black', 'Air'),
                ]

                for df_current, color, label in databases_mean:
                    df_current['date_time'] = pd.to_datetime(df_current['date_time']).dt.date
                    df_current = df_current.sort_values(by='date_time')

                    plot.plot(df_current['date_time'], df_current['mean'], label=label, color=color, marker='o', linestyle='-')

    # Now set labels, legends, and limits after adding all lines
    plot.set_title("Mean vs Datetime", fontsize=12, pad=15)
    plot.set_xlabel("Datetime", fontsize=10)
    plot.set_ylabel("Mean", fontsize=10)
    plot.grid(True, alpha=0.3)
    plot.legend(frameon=False)

    all_dates = pd.concat([pd.to_datetime(pd.read_csv(os.path.join(path+"/Mean", "database_MEAN_1.csv"))['date_time']) for f in os.listdir(path)])
    plot.set_xlim([all_dates.min(), all_dates.max()])
    plot.set_ylim(bottom=-5000, top=5000)
    
    plot.set_yticks([tick for tick in plot.get_yticks() if tick != 0])

    fig.tight_layout()

    # Embed plot in Tkinter **outside the loop**
    graph = FigureCanvasTkAgg(fig, master=graph_row_frame)
    graph.draw()
    graph.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10)
    
    list_of_section.append(graph_row_frame)

    #Regenerate button
    regenerate_button = tk.Button(
        frame,
        text="⟳ Regenerate",  # Unicode refresh symbol
        font=("Segoe UI", 10, "bold"),
        bg="#27ae60",  # Green color
        fg="white",
        activebackground="#219a52",
        relief="flat",
        command=lambda fl=path+"/Mean": regenerate_folder_section(frame)
    )
    regenerate_button.pack(side="top", pady=8, ipadx=12)

    list_of_section.append(regenerate_button)
