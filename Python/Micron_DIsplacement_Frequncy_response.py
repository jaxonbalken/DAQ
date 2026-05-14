import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog
import numpy as np
from scipy.fft import fft, fftfreq

# --- Conversion constants ---
MICRONS_PER_PIXEL = 3.391685
FRAME_RATE = 226.67  # frames per second
seconds_per_frame = 1 / FRAME_RATE

# --- File selection ---
root = Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select CSV File",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

if not file_path:
    print("No file selected. Exiting.")
    exit()

# --- Load and clean data ---
df = pd.read_csv(file_path, na_values=['None'])
df.columns = df.columns.str.strip()
numeric_cols = ['Centroid_X', 'Centroid_Y', 'Movement (pixels)']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df = df.dropna()
df = df.sort_values(by='Frame').reset_index(drop=True)

# --- Convert movement to microns ---
df['Movement (µm)'] = df['Movement (pixels)'] * MICRONS_PER_PIXEL
df['Movement_X (µm)'] = df['Movement_X (dX)'] * MICRONS_PER_PIXEL
df['Movement_Y (µm)'] = df['Movement_Y (dY)'] * MICRONS_PER_PIXEL

# --- Calculate the max displacement --- 
max_displacement_x_px = max(df['Centroid_X'])
max_displacement_y_px = max(df['Centroid_Y'])

min_displacement_x_px = min(df['Centroid_X'])
min_displacement_y_px = min(df['Centroid_Y'])

total_displacement_x_px = abs(min_displacement_x_px - max_displacement_x_px)
total_displacement_y_px = abs(min_displacement_y_px - max_displacement_y_px)

total_displacement_x_micron = total_displacement_x_px * MICRONS_PER_PIXEL
total_displacement_y_micron = total_displacement_y_px * MICRONS_PER_PIXEL

print(f'min x px: {min_displacement_x_px}')
print(f'min y px: {min_displacement_y_px}')
print(f'max x px: {max_displacement_x_px}')
print(f'max y px: {max_displacement_y_px}')
print(f'Total X pixel displacement: {total_displacement_x_px}')
print(f'Total Y pixel displacement: {total_displacement_y_px}')
print(f'Total X Miron displacement: {total_displacement_x_micron}')
print(f'Total Y Miron displacement: {total_displacement_y_micron}')

# --- Calculate velocity (µm/s) and acceleration (µm/s²) ---
df['Velocity (µm/s)'] = df['Movement (µm)'].diff() / seconds_per_frame
df['Acceleration (µm/s²)'] = df['Velocity (µm/s)'].diff() / seconds_per_frame

# Drop first two rows with NaNs
df = df.dropna().reset_index(drop=True)

# --- Compute average magnitudes ---
avg_speed = df['Velocity (µm/s)'].abs().mean()
avg_accel = df['Acceleration (µm/s²)'].abs().mean()

avg_mx = df['Movement_X (µm)'].abs().mean()
max_mx = df['Movement_X (µm)'].abs().max()

avg_my = df['Movement_Y (µm)'].abs().mean()
max_my = df['Movement_Y (µm)'].abs().max()

avg_m = df['Movement (µm)'].abs().mean()
max_m = df['Movement (µm)'].abs().max()

# --- Calculate displacement vector ---
min_x, min_y = df['Centroid_X'].min() * MICRONS_PER_PIXEL, df['Centroid_Y'].min() * MICRONS_PER_PIXEL
max_x, max_y = df['Centroid_X'].max() * MICRONS_PER_PIXEL, df['Centroid_Y'].max() * MICRONS_PER_PIXEL
disp_vec = (max_x - min_x, max_y - min_y)

# --- Calculate max velocity ---
max_velocity = df['Velocity (µm/s)'].abs().max()

# --- Velocity components for vector field (in microns/frame) ---
vel_x = df['Centroid_X'].diff() * MICRONS_PER_PIXEL
vel_y = df['Centroid_Y'].diff() * MICRONS_PER_PIXEL

plt.plot(df['Frame'], df['Centroid_X'], label='Centroid X (px)', color='blue')
plt.plot(df['Frame'], df['Centroid_Y'], label='Centroid Y (px)', color='green')
plt.xlabel('Frame')
plt.ylabel('Centroid Position (px)')
plt.title('Centroid X and Y over Frames')
plt.legend()
plt.grid(True)
plt.show()