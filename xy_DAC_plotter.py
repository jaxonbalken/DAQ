import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, Toplevel, Label, Entry, Button, StringVar

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

# Define all possible column names (matching original script's column order)
all_column_names = ['Intensity (V)', 'X DAC (V)', 'Y DAC (V)', 'Beacon X DAC (V)', 'Beacon Y DAC (V)']

# Read the CSV file
df = pd.read_csv(file_path, header=None)
num_csv_columns = len(df.columns)

# Assign column names based on position
for idx, col_name in enumerate(all_column_names):
    if idx < num_csv_columns:
        df.rename(columns={idx: col_name}, inplace=True)

# Check required columns exist
if 'X DAC (V)' not in df.columns or 'Y DAC (V)' not in df.columns:
    print("ERROR: CSV file must have at least 3 columns (Intensity, X DAC, Y DAC).")
    exit()

total_points = len(df)

# Ask user how many points to plot
limit_window = Toplevel(root)
limit_window.title("Point Limit")
limit_window.attributes('-topmost', True)
limit_window.geometry("280x150")

limit_window.geometry("280x200")

Label(limit_window, text=f"Total samples: {total_points}", font=('Arial', 10)).pack(pady=8)

Label(limit_window, text="Start index:", font=('Arial', 10)).pack()
start_var = StringVar(value="0")
start_entry = Entry(limit_window, textvariable=start_var, font=('Arial', 11), width=15, justify='center')
start_entry.pack(pady=4)

Label(limit_window, text="Number of points to plot:", font=('Arial', 10)).pack()
entry_var = StringVar(value=str(total_points))
entry = Entry(limit_window, textvariable=entry_var, font=('Arial', 11), width=15, justify='center')
entry.pack(pady=4)
entry.select_range(0, 'end')
entry.focus()

limit_result = {'start': 0, 'value': total_points, 'ok': False}

def on_ok():
    try:
        start = int(start_var.get())
        start = max(0, min(start, total_points - 1))
    except ValueError:
        start = 0
    try:
        val = int(entry_var.get())
        val = max(1, min(val, total_points - start))
    except ValueError:
        val = total_points - start
    limit_result['start'] = start
    limit_result['value'] = val
    limit_result['ok'] = True
    limit_window.destroy()

def on_cancel():
    limit_window.destroy()

entry.bind('<Return>', lambda e: on_ok())
start_entry.bind('<Return>', lambda e: entry.focus())

Button(limit_window, text="Plot", command=on_ok, width=12, font=('Arial', 10, 'bold'),
       bg='#4CAF50', fg='white').pack(side='left', padx=20, pady=8)
Button(limit_window, text="Cancel", command=on_cancel, width=12, font=('Arial', 10)).pack(side='right', padx=20, pady=8)

limit_window.wait_window()

if not limit_result['ok']:
    print("Cancelled. Exiting.")
    exit()

num_points = limit_result['value']
start_idx = limit_result['start']
df = df.iloc[start_idx:start_idx + num_points]
print(f"Plotting {num_points} samples starting from index {start_idx} (of {total_points} total).")

x_data = df['X DAC (V)']
y_data = df['Y DAC (V)']

# Print statistics
print("\n" + "="*50)
print("X DAC (V) STATISTICS")
print("="*50)
print(f"Mean:    {x_data.mean():.6f} V")
print(f"Std Dev: {x_data.std():.6f} V")
print(f"Min:     {x_data.min():.6f} V")
print(f"Max:     {x_data.max():.6f} V")

print("\n" + "="*50)
print("Y DAC (V) STATISTICS")
print("="*50)
print(f"Mean:    {y_data.mean():.6f} V")
print(f"Std Dev: {y_data.std():.6f} V")
print(f"Min:     {y_data.min():.6f} V")
print(f"Max:     {y_data.max():.6f} V")
print("="*50)

# Create the XY plot
plt.figure(figsize=(8, 8))
plt.plot(x_data, y_data, linewidth=1.0, alpha=0.7, color='steelblue')

# Mark start and end points
plt.scatter(x_data.iloc[0], y_data.iloc[0], color='green', zorder=5, s=50, label='Start')
plt.scatter(x_data.iloc[-1], y_data.iloc[-1], color='red', zorder=5, s=50, label='End')

plt.xlabel('X DAC (V)', fontsize=12)
plt.ylabel('Y DAC (V)', fontsize=12)
plt.title(f'Y DAC vs X DAC  ({num_points:,} points, start index {start_idx:,})', fontsize=14, fontweight='bold')
plt.legend(loc='best', fontsize=10)
plt.grid(True, alpha=0.3)
plt.axis('equal')  # Equal aspect ratio so circles look like circles

# Force both axes to share the same min/max range
all_min = min(x_data.min(), y_data.min())
all_max = max(x_data.max(), y_data.max())
padding = (all_max - all_min) * 0.05
plt.xlim(all_min - padding, all_max + padding)
plt.ylim(all_min - padding, all_max + padding)
plt.tight_layout()

print(f"\nPlotted {len(df)} samples from: {file_path}")

plt.show()