import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, Toplevel, Checkbutton, IntVar, Button, Label

# Create a root window and hide it
root = Tk()
root.withdraw()
root.attributes('-topmost', True)

# Open file dialog to select CSV file
print("Please select a CSV file...")
file_path = filedialog.askopenfilename(
    title="Select CSV File",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

# Check if a file was selected
if not file_path:
    print("No file selected. Exiting.")
    exit()

# Define all possible column names
all_column_names = ['Intensity (V)', 'X DAC (V)', 'Y DAC (V)', 'Beacon X DAC (V)', 'Beacon Y DAC (V)']

# Create a dialog for selecting columns
selection_window = Toplevel(root)
selection_window.title("Select Columns to Plot")
selection_window.attributes('-topmost', True)
selection_window.geometry("300x280")

# Add instruction label
Label(selection_window, text="Select columns to plot:", font=('Arial', 12, 'bold')).pack(pady=10)

# Create checkboxes for each column
checkbox_vars = []
for i, col_name in enumerate(all_column_names):
    var = IntVar(value=1 if i < 4 else 0)  # First 4 checked by default
    checkbox_vars.append(var)
    cb = Checkbutton(selection_window, text=col_name, variable=var, font=('Arial', 10))
    cb.pack(anchor='w', padx=30, pady=5)

# Variable to store whether OK was clicked
selection_made = {'ok': False}

def on_ok():
    selection_made['ok'] = True
    selection_window.destroy()

def on_cancel():
    selection_window.destroy()

# Add Enter button underneath checkboxes
enter_button = Button(selection_window, text="Enter", command=on_ok, width=20, font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white')
enter_button.pack(pady=10)

# Add Cancel button
cancel_button = Button(selection_window, text="Cancel", command=on_cancel, width=20, font=('Arial', 10))
cancel_button.pack(pady=5)

# Wait for the window to be closed
selection_window.wait_window()

# Check if user clicked OK
if not selection_made['ok']:
    print("Selection cancelled. Exiting.")
    exit()

# Get selected columns
selected_indices = [i for i, var in enumerate(checkbox_vars) if var.get() == 1]

if not selected_indices:
    print("No columns selected. Exiting.")
    exit()

# Determine how many columns are in the CSV file
temp_df = pd.read_csv(file_path, header=None, nrows=1)
num_csv_columns = len(temp_df.columns)

# Read the CSV file with all available columns
df = pd.read_csv(file_path, header=None)

# Assign column names only to the columns that exist in the CSV
for idx in selected_indices:
    if idx < num_csv_columns:
        df.rename(columns={idx: all_column_names[idx]}, inplace=True)

# Filter to only selected columns that exist
selected_columns = [all_column_names[idx] for idx in selected_indices if idx < num_csv_columns]

if not selected_columns:
    print("Selected columns do not exist in the CSV file. Exiting.")
    exit()

# Create the plot
plt.figure(figsize=(12, 8))

# Create x-axis as the index (number of inputs)
x = range(len(df))

# Plot each selected column
for col in selected_columns:
    plt.plot(x, df[col], label=col, linewidth=2)

# Customize the plot
plt.xlabel('Number of Inputs', fontsize=12)
plt.ylabel('Voltage (V)', fontsize=12)
plt.title('DAQ Outputs (V)', fontsize=14, fontweight='bold')
plt.legend(loc='best', fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Print information and statistics BEFORE showing the plot
print(f"\nPlotted {len(selected_columns)} column(s) from: {file_path}")
print(f"Columns plotted: {', '.join(selected_columns)}")

# Display statistics for Intensity column if selected
if 'Intensity (V)' in selected_columns:
    intensity_data = df['Intensity (V)']
    print("\n" + "="*50)
    print("INTENSITY (V) STATISTICS")
    print("="*50)
    print(f"Mean:        {intensity_data.mean():.6f} V")
    print(f"Median:      {intensity_data.median():.6f} V")
    print(f"Std Dev:     {intensity_data.std():.6f} V")
    print(f"Min:         {intensity_data.min():.6f} V")
    print(f"Max:         {intensity_data.max():.6f} V")
    print(f"Range:       {intensity_data.max() - intensity_data.min():.6f} V")
    print(f"Count:       {len(intensity_data)} samples")
    print("="*50)

# Display the plot
plt.show()