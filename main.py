import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
import csv
import os
import subprocess
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

materials = {
    "Silica": 1.44,
    "Fluoride Glass": 1.38,
    "Polymer (PMMA)": 1.40,
    "Sapphire": 1.76
}

data_store = []
CSV_FILENAME = "fiber_calculations.csv"

# Check if CSV exists, if not create it with headers
def initialize_csv():
    """Initialize CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Core Material", "Core RI", "Cladding Material", "Cladding RI", "NA"])

# Load existing data from CSV
def load_data_from_csv():
    """Load existing calculations from CSV into data_store and treeview."""
    if os.path.exists(CSV_FILENAME):
        try:
            df = pd.read_csv(CSV_FILENAME)
            for _, row in df.iterrows():
                data_store.append({
                    "Core Material": row["Core Material"],
                    "Cladding Material": row["Cladding Material"],
                    "NA": row["NA"]
                })
                
                core_name_str = f"{row['Core Material']} ({row['Core RI']})"
                cladding_name_str = f"{row['Cladding Material']} ({row['Cladding RI']})"
                
                tree.insert("", "end", values=(core_name_str, cladding_name_str, row["NA"]))
        except Exception as e:
            messagebox.showwarning("CSV Load Error", f"Could not load existing data: {str(e)}")

def toggle_entry_state(*args):
    """Enable or disable entries based on dropdown selection."""
    if core_var.get() == "Custom":
        core_index_var.configure(state="normal")
        core_name_var.configure(state="normal")
    else:
        core_index_var.configure(state="disabled")
        core_name_var.configure(state="disabled")
    
    if cladding_var.get() == "Custom":
        cladding_index_var.configure(state="normal")
        cladding_name_var.configure(state="normal")
    else:
        cladding_index_var.configure(state="disabled")
        cladding_name_var.configure(state="disabled")

def save_to_csv(core_name, n_core, cladding_name, n_cladding, na):
    """Save calculation to CSV file."""
    try:
        with open(CSV_FILENAME, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([core_name, n_core, cladding_name, n_cladding, na])
    except Exception as e:
        messagebox.showwarning("CSV Save Error", f"Could not save data: {str(e)}")

def calculate_na():
    """Calculate Numerical Aperture and validate inputs."""
    core_material = next((item for item in materials.keys() if core_var.get().startswith(item)), 'Custom')
    cladding_material = next((item for item in materials.keys() if cladding_var.get().startswith(item)), 'Custom')

    core_name = core_name_var.get() if core_material == "Custom" else core_material
    cladding_name = cladding_name_var.get() if cladding_material == "Custom" else cladding_material

    if(core_name == "" or cladding_name == ""):
        raise ValueError("Core and Cladding material name should be provided")
    
    try:
        n_core = float(core_index_var.get()) if core_material == "Custom" else materials[core_material]
        n_cladding = float(cladding_index_var.get()) if cladding_material == "Custom" else materials[cladding_material]
        
        if n_cladding >= n_core:
            raise ValueError("Core refractive index must be greater than Cladding refractive index.")
        
        NA = np.sqrt(n_core**2 - n_cladding**2)

        core_name_str = f"{core_name} ({n_core})"
        cladding_name_str = f"{cladding_name} ({n_cladding})"
        
        data_store.append({
            "Core Material": core_name,
            "Cladding Material": cladding_name,
            "NA": round(NA, 3)
        })
        
        # Save to CSV
        save_to_csv(core_name, n_core, cladding_name, n_cladding, round(NA, 3))
        
        # Update treeview
        tree.insert("", "end", values=(core_name_str, cladding_name_str, round(NA, 3)))
        
    except ValueError as e:
        messagebox.showerror("Input Error", f"Invalid input: {str(e)}")

def plot_bar_graph():
    """Plot NA vs Cladding Material as a bar graph."""
    if not os.path.exists(CSV_FILENAME) or os.path.getsize(CSV_FILENAME) == 0:
        messagebox.showwarning("No Data", "Run at least one calculation before plotting.")
        return
    
    try:
        df = pd.read_csv(CSV_FILENAME)
        plt.figure(figsize=(8, 5))
        plt.bar(df["Cladding Material"], df["NA"], color=['blue', 'red', 'green', 'purple'])
        plt.xlabel("Cladding Material")
        plt.ylabel("Numerical Aperture (NA)")
        plt.title("Effect of Cladding Material on Numerical Aperture (Bar Graph)")
        plt.ylim(0, max(df["NA"]) + 0.1)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    except Exception as e:
        messagebox.showerror("Plot Error", f"Error creating bar plot: {str(e)}")

def plot_line_graph():
    """Plot NA vs Cladding Refractive Index as a line graph with material labels."""
    if not os.path.exists(CSV_FILENAME) or os.path.getsize(CSV_FILENAME) == 0:
        messagebox.showwarning("No Data", "Run at least one calculation before plotting.")
        return
    
    try:
        df = pd.read_csv(CSV_FILENAME)
        plt.figure(figsize=(10, 6))
        
        # Sort by cladding RI for a smoother line
        df = df.sort_values(by="Cladding RI")
        
        # Extract values for plotting
        cladding_ri_values = df['Cladding RI'].values
        na_values = df['NA'].values
        cladding_materials = df['Cladding Material'].values
        
        # Plot the line
        plt.scatter(cladding_ri_values, na_values, marker='o', color='blue')
        
        # Add material labels to each point
        for i, (x, y, material) in enumerate(zip(cladding_ri_values, na_values, cladding_materials)):
            plt.annotate(material, (x, y), textcoords="offset points", 
                         xytext=(0, 10), ha='center', fontsize=9)
        
        plt.xlabel("Cladding Refractive Index")
        plt.ylabel("Numerical Aperture (NA)")
        plt.title("Numerical Aperture vs Cladding Refractive Index")
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Add a legend for the line
        plt.legend(['NA values'], loc='best')
        
        plt.tight_layout()
        plt.show()
    except Exception as e:
        messagebox.showerror("Plot Error", f"Error creating line plot: {str(e)}")


# Initialize GUI
root = ctk.CTk()
root.title("Optical Fiber Simulation")
root.geometry("750x450")

frame_left = ctk.CTkFrame(root)
frame_left.pack(side="left", padx=10, pady=10, fill="both", expand=True)

frame_right = ctk.CTkFrame(root)
frame_right.pack(side="right", padx=10, pady=10, fill="both", expand=True)

ctk.CTkLabel(frame_left, text="Select Core Material:").pack(pady=5)
core_var = ctk.StringVar(value="Silica")
core_var.trace_add("write", toggle_entry_state)
core_menu = ctk.CTkOptionMenu(frame_left, variable=core_var, values=[f"{x} ({materials[x]})" for x in materials.keys()] + ["Custom"])
core_menu.pack()
core_index_var = ctk.CTkEntry(frame_left, placeholder_text="Enter Core RI (if Custom)", state="disabled")
core_index_var.pack(pady=5)
core_name_var = ctk.CTkEntry(frame_left, placeholder_text="Enter Core Material Name", state="disabled")
core_name_var.pack(pady=5)

ctk.CTkLabel(frame_left, text="Select Cladding Material:").pack(pady=5)
cladding_var = ctk.StringVar(value="Silica")
cladding_var.trace_add("write", toggle_entry_state)
cladding_menu = ctk.CTkOptionMenu(frame_left, variable=cladding_var, values=[f"{x} ({materials[x]})" for x in materials.keys()] + ["Custom"])
cladding_menu.pack()
cladding_index_var = ctk.CTkEntry(frame_left, placeholder_text="Enter Cladding RI (if Custom)", state="disabled")
cladding_index_var.pack(pady=5)
cladding_name_var = ctk.CTkEntry(frame_left, placeholder_text="Enter Cladding Material Name", state="disabled")
cladding_name_var.pack(pady=5)

# Buttons frame
buttons_frame = ctk.CTkFrame(frame_left)
buttons_frame.pack(pady=10, fill="x")

ctk.CTkButton(buttons_frame, text="Calculate NA", command=calculate_na).pack(pady=5, fill="x")

# Plot buttons frame
plot_buttons_frame = ctk.CTkFrame(frame_left)
plot_buttons_frame.pack(pady=5, fill="x")

ctk.CTkButton(plot_buttons_frame, text="Bar Graph", command=plot_bar_graph).pack(pady=5, fill="x")
ctk.CTkButton(plot_buttons_frame, text="Line Graph", command=plot_line_graph).pack(pady=5, fill="x")

style = Style()
style.configure("Treeview", rowheight=25, font=("Arial", 12))
style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
style.layout("Treeview", [("Treeview.treearea", {'sticky': 'nswe'})])

columns = ("Core", "Cladding", "NA")
tree = Treeview(frame_right, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=150, anchor="center")

tree.pack(fill="both", expand=True)



def install_packages():
        """Install required packages if not already installed."""
        required_packages = [
            "numpy", 
            "pandas", 
            "matplotlib", 
            "customtkinter", 
            "tk"
        ]
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    install_packages()

    # Initialize CSV and load existing data
    initialize_csv()
    load_data_from_csv()

    root.mainloop()