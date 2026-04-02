import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# -----------------------------
# File paths
# -----------------------------
vertical_file = r'C:\Users\ASE\Documents\GitHub\FTA-Calibration-and-Circle-Detection\Plots\PCB2_full_vertical_throw.csv'
horizontal_file = r'C:\Users\ASE\Documents\GitHub\FTA-Calibration-and-Circle-Detection\CSV Files\PCB2horizontalthrow.csv'

# Save settings
save_plots = True
output_folder = r'C:\Users\ASE\Documents\GitHub\FTA-Calibration-and-Circle-Detection\Plots'

if save_plots and not os.path.exists(output_folder):
    os.makedirs(output_folder)

# -----------------------------
# Load CSVs
# -----------------------------
vertical_data = pd.read_csv(vertical_file)
horizontal_data = pd.read_csv(horizontal_file)

print("Vertical columns:", vertical_data.columns.tolist())
print("Horizontal columns:", horizontal_data.columns.tolist())

# -----------------------------
# Function to plot with linear fit
# -----------------------------
def plot_with_fit(x, y, title, color, filename):
    # Linear fit (1st degree polynomial)
    coeffs = np.polyfit(x, y, deg=1)
    slope_per_amp = coeffs[0]
    intercept = coeffs[1]
    slope_per_point1amp = slope_per_amp * 0.1  # Convert to µm per 0.1 A
    fit_line = np.poly1d(coeffs)

    # Plot data and fit
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color=color, label='')
    #plt.plot([], [], ' ', label=f'Slope: {slope_per_point1amp:.2f} µm / 0.1 A')

    # Annotate slope in µm per 0.1 A
    plt.text(0.05, 0.95, f'Slope: {slope_per_point1amp:.2f} µm / 0.1 A',
             transform=plt.gca().transAxes,
             fontsize=12, verticalalignment='top',
             bbox=dict(facecolor='white', alpha=0.6))

    plt.title(title)
    plt.xlabel('Current (I)')
    plt.ylabel('Throw (Microns)')
    plt.axhline(y=0, color='black', linewidth=2)  # Bold horizontal line at y = 0

    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save_plots:
        path = os.path.join(output_folder, filename)
        plt.savefig(path)
        print(f"✅ Plot saved to: {path}")

    plt.show()


plot_with_fit(
    x=vertical_data['Current (I)'],
    y=vertical_data['Throw (Microns)'],
    title='PCB 2 Vertical Throw vs. Current',
    color='blue',
    filename='vertical_throw_plot_with_fit.pdf'
)

# -----------------------------
# Plot Horizontal Throw with Fit
# -----------------------------
plot_with_fit(
    x=horizontal_data['Current (I)'],
    y=horizontal_data['Throw (Microns)'],
    title='PCB 2 Horizontal Throw vs. Current',
    color='red',
    filename='horizontal_throw_plot_with_fit.pdf'
)

