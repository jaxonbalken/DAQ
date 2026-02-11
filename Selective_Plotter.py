import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, Toplevel, Checkbutton, IntVar, Button, Label
import numpy as np
from scipy.optimize import curve_fit
from scipy import fft

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
selection_window.geometry("300x330")

# Add instruction label
Label(selection_window, text="Select columns to plot:", font=('Arial', 12, 'bold')).pack(pady=10)

# Create checkboxes for each column
checkbox_vars = []
for i, col_name in enumerate(all_column_names):
    var = IntVar(value=1 if i < 4 else 0)  # First 4 checked by default
    checkbox_vars.append(var)
    cb = Checkbutton(selection_window, text=col_name, variable=var, font=('Arial', 10))
    cb.pack(anchor='w', padx=30, pady=5)

# Add separator
Label(selection_window, text="", font=('Arial', 2)).pack()

# Add curve fitting option
curve_fit_var = IntVar(value=0)
curve_fit_cb = Checkbutton(selection_window, text="Sine Wave Curve Fit (FFT) (BETA)", variable=curve_fit_var, font=('Arial', 10, 'bold'))
curve_fit_cb.pack(anchor='w', padx=30, pady=5)

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

# Create x-axis in milliseconds (10000 inputs per second = 0.1 ms per input)
x = [i * 0.1 for i in range(len(df))]  # Convert to milliseconds

# Plot each selected column
for col in selected_columns:
    plt.plot(x, df[col], label=col, linewidth=1.5, alpha=0.7)

# Apply curve fitting if selected
apply_curve_fit = curve_fit_var.get() == 1
fit_results = {}

if apply_curve_fit:
    # Define sine wave function: A * sin(2*pi*f*t + phi) + offset
    def sine_wave(t, amplitude, frequency, phase, offset):
        return amplitude * np.sin(2 * np.pi * frequency * t + phase) + offset
    
    def estimate_frequency_fft(time_data, signal_data, sample_rate=10000):
        """Use FFT to find dominant frequency"""
        # Perform FFT
        N = len(signal_data)
        yf = fft.fft(signal_data - np.mean(signal_data))  # Remove DC component
        xf = fft.fftfreq(N, 1/sample_rate)
        
        # Only look at positive frequencies
        positive_freq_idx = xf > 0
        xf_positive = xf[positive_freq_idx]
        yf_positive = np.abs(yf[positive_freq_idx])
        
        # Find peak frequency
        peak_idx = np.argmax(yf_positive)
        dominant_freq = xf_positive[peak_idx]
        
        return dominant_freq
    
    def remove_outliers_robust(data, threshold=3.0):
        """Remove outliers using modified Z-score (more robust than IQR)"""
        median = np.median(data)
        mad = np.median(np.abs(data - median))  # Median Absolute Deviation
        
        if mad == 0:
            # Fallback to standard deviation if MAD is zero
            std = np.std(data)
            modified_z_scores = np.abs(data - median) / std if std > 0 else np.zeros_like(data)
        else:
            modified_z_scores = 0.6745 * np.abs(data - median) / mad
        
        return modified_z_scores < threshold
    
    # Fit Intensity with aggressive outlier removal
    if 'Intensity (V)' in selected_columns:
        try:
            intensity_data = df['Intensity (V)'].values
            x_array = np.array(x)
            
            print("\nFitting Intensity (V)...")
            
            # Step 1: Remove outliers iteratively
            clean_data = intensity_data.copy()
            clean_x = x_array.copy()
            iteration = 0
            max_iterations = 3
            
            while iteration < max_iterations:
                mask = remove_outliers_robust(clean_data, threshold=2.5)
                if np.sum(~mask) == 0:
                    break
                clean_data = clean_data[mask]
                clean_x = clean_x[mask]
                iteration += 1
            
            outliers_removed = len(intensity_data) - len(clean_data)
            print(f"  Removed {outliers_removed} outliers ({100*outliers_removed/len(intensity_data):.1f}%)")
            
            # Step 2: Estimate frequency using FFT
            freq_estimate = estimate_frequency_fft(clean_x, clean_data)
            print(f"  FFT estimated frequency: {freq_estimate:.4f} Hz")
            
            # Step 3: Initial parameter guesses
            amp_guess = (np.max(clean_data) - np.min(clean_data)) / 2
            offset_guess = np.mean(clean_data)
            phase_guess = 0
            
            # Step 4: Perform curve fit with fixed frequency estimate
            popt_intensity, pcov_intensity = curve_fit(
                sine_wave, 
                clean_x, 
                clean_data,
                p0=[amp_guess, freq_estimate, phase_guess, offset_guess],
                bounds=(
                    [0, freq_estimate*0.8, -2*np.pi, -np.inf],  # Lower bounds
                    [np.inf, freq_estimate*1.2, 2*np.pi, np.inf]  # Upper bounds
                ),
                maxfev=10000
            )
            
            # Generate fitted curve for full dataset
            fitted_intensity = sine_wave(x_array, *popt_intensity)
            plt.plot(x, fitted_intensity, '--', label='Intensity Fit', linewidth=2.5, color='red')
            
            fit_results['Intensity (V)'] = {
                'amplitude': popt_intensity[0],
                'frequency': popt_intensity[1],
                'phase': popt_intensity[2],
                'offset': popt_intensity[3],
                'outliers_removed': outliers_removed,
                'fit_quality': 1 - np.sum((clean_data - sine_wave(clean_x, *popt_intensity))**2) / np.sum((clean_data - np.mean(clean_data))**2)
            }
            
            print(f"  Fit quality (R²): {fit_results['Intensity (V)']['fit_quality']:.4f}")
            
        except Exception as e:
            print(f"  ERROR: Could not fit Intensity data: {e}")
    
    # Fit Beacon X DAC (cleaner signal, less aggressive filtering)
    if 'Beacon X DAC (V)' in selected_columns:
        try:
            beacon_x_data = df['Beacon X DAC (V)'].values
            x_array = np.array(x)
            
            print("\nFitting Beacon X DAC (V)...")
            
            # Step 1: Light outlier removal
            mask = remove_outliers_robust(beacon_x_data, threshold=3.5)
            clean_beacon = beacon_x_data[mask]
            clean_x_beacon = x_array[mask]
            outliers_removed_beacon = len(beacon_x_data) - len(clean_beacon)
            
            if outliers_removed_beacon > 0:
                print(f"  Removed {outliers_removed_beacon} outliers ({100*outliers_removed_beacon/len(beacon_x_data):.1f}%)")
            
            # Step 2: Estimate frequency using FFT
            freq_estimate_beacon = estimate_frequency_fft(clean_x_beacon, clean_beacon)
            print(f"  FFT estimated frequency: {freq_estimate_beacon:.4f} Hz")
            
            # Step 3: Initial parameter guesses
            amp_guess = (np.max(clean_beacon) - np.min(clean_beacon)) / 2
            offset_guess = np.mean(clean_beacon)
            phase_guess = 0
            
            # Step 4: Perform curve fit
            popt_beacon, pcov_beacon = curve_fit(
                sine_wave,
                clean_x_beacon,
                clean_beacon,
                p0=[amp_guess, freq_estimate_beacon, phase_guess, offset_guess],
                bounds=(
                    [0, freq_estimate_beacon*0.9, -2*np.pi, -np.inf],
                    [np.inf, freq_estimate_beacon*1.1, 2*np.pi, np.inf]
                ),
                maxfev=10000
            )
            
            # Generate fitted curve
            fitted_beacon = sine_wave(x_array, *popt_beacon)
            plt.plot(x, fitted_beacon, '--', label='Beacon X DAC Fit', linewidth=2.5, color='orange')
            
            fit_results['Beacon X DAC (V)'] = {
                'amplitude': popt_beacon[0],
                'frequency': popt_beacon[1],
                'phase': popt_beacon[2],
                'offset': popt_beacon[3],
                'outliers_removed': outliers_removed_beacon,
                'fit_quality': 1 - np.sum((clean_beacon - sine_wave(clean_x_beacon, *popt_beacon))**2) / np.sum((clean_beacon - np.mean(clean_beacon))**2)
            }
            
            print(f"  Fit quality (R²): {fit_results['Beacon X DAC (V)']['fit_quality']:.4f}")
            
        except Exception as e:
            print(f"  ERROR: Could not fit Beacon X DAC data: {e}")
    
    # Fit X DAC
    if 'X DAC (V)' in selected_columns:
        try:
            x_dac_data = df['X DAC (V)'].values
            x_array = np.array(x)
            
            print("\nFitting X DAC (V)...")
            
            # Step 1: Light outlier removal
            mask = remove_outliers_robust(x_dac_data, threshold=3.5)
            clean_x_dac = x_dac_data[mask]
            clean_x_time = x_array[mask]
            outliers_removed_x = len(x_dac_data) - len(clean_x_dac)
            
            if outliers_removed_x > 0:
                print(f"  Removed {outliers_removed_x} outliers ({100*outliers_removed_x/len(x_dac_data):.1f}%)")
            
            # Step 2: Estimate frequency using FFT
            freq_estimate_x = estimate_frequency_fft(clean_x_time, clean_x_dac)
            print(f"  FFT estimated frequency: {freq_estimate_x:.4f} Hz")
            
            # Step 3: Initial parameter guesses
            amp_guess = (np.max(clean_x_dac) - np.min(clean_x_dac)) / 2
            offset_guess = np.mean(clean_x_dac)
            phase_guess = 0
            
            # Step 4: Perform curve fit
            popt_x_dac, pcov_x_dac = curve_fit(
                sine_wave,
                clean_x_time,
                clean_x_dac,
                p0=[amp_guess, freq_estimate_x, phase_guess, offset_guess],
                bounds=(
                    [0, freq_estimate_x*0.9, -2*np.pi, -np.inf],
                    [np.inf, freq_estimate_x*1.1, 2*np.pi, np.inf]
                ),
                maxfev=10000
            )
            
            # Generate fitted curve
            fitted_x_dac = sine_wave(x_array, *popt_x_dac)
            plt.plot(x, fitted_x_dac, '--', label='X DAC Fit', linewidth=2.5, color='green')
            
            fit_results['X DAC (V)'] = {
                'amplitude': popt_x_dac[0],
                'frequency': popt_x_dac[1],
                'phase': popt_x_dac[2],
                'offset': popt_x_dac[3],
                'outliers_removed': outliers_removed_x,
                'fit_quality': 1 - np.sum((clean_x_dac - sine_wave(clean_x_time, *popt_x_dac))**2) / np.sum((clean_x_dac - np.mean(clean_x_dac))**2)
            }
            
            print(f"  Fit quality (R²): {fit_results['X DAC (V)']['fit_quality']:.4f}")
            
        except Exception as e:
            print(f"  ERROR: Could not fit X DAC data: {e}")
    
    # Fit Y DAC
    if 'Y DAC (V)' in selected_columns:
        try:
            y_dac_data = df['Y DAC (V)'].values
            x_array = np.array(x)
            
            print("\nFitting Y DAC (V)...")
            
            # Step 1: Light outlier removal
            mask = remove_outliers_robust(y_dac_data, threshold=3.5)
            clean_y_dac = y_dac_data[mask]
            clean_y_time = x_array[mask]
            outliers_removed_y = len(y_dac_data) - len(clean_y_dac)
            
            if outliers_removed_y > 0:
                print(f"  Removed {outliers_removed_y} outliers ({100*outliers_removed_y/len(y_dac_data):.1f}%)")
            
            # Step 2: Estimate frequency using FFT
            freq_estimate_y = estimate_frequency_fft(clean_y_time, clean_y_dac)
            print(f"  FFT estimated frequency: {freq_estimate_y:.4f} Hz")
            
            # Step 3: Initial parameter guesses
            amp_guess = (np.max(clean_y_dac) - np.min(clean_y_dac)) / 2
            offset_guess = np.mean(clean_y_dac)
            phase_guess = 0
            
            # Step 4: Perform curve fit
            popt_y_dac, pcov_y_dac = curve_fit(
                sine_wave,
                clean_y_time,
                clean_y_dac,
                p0=[amp_guess, freq_estimate_y, phase_guess, offset_guess],
                bounds=(
                    [0, freq_estimate_y*0.9, -2*np.pi, -np.inf],
                    [np.inf, freq_estimate_y*1.1, 2*np.pi, np.inf]
                ),
                maxfev=10000
            )
            
            # Generate fitted curve
            fitted_y_dac = sine_wave(x_array, *popt_y_dac)
            plt.plot(x, fitted_y_dac, '--', label='Y DAC Fit', linewidth=2.5, color='purple')
            
            fit_results['Y DAC (V)'] = {
                'amplitude': popt_y_dac[0],
                'frequency': popt_y_dac[1],
                'phase': popt_y_dac[2],
                'offset': popt_y_dac[3],
                'outliers_removed': outliers_removed_y,
                'fit_quality': 1 - np.sum((clean_y_dac - sine_wave(clean_y_time, *popt_y_dac))**2) / np.sum((clean_y_dac - np.mean(clean_y_dac))**2)
            }
            
            print(f"  Fit quality (R²): {fit_results['Y DAC (V)']['fit_quality']:.4f}")
            
        except Exception as e:
            print(f"  ERROR: Could not fit Y DAC data: {e}")

# Customize the plot
plt.xlabel('Time (ms)', fontsize=12)
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

# Display curve fit results and phase analysis
if apply_curve_fit and fit_results:
    print("\n" + "="*50)
    print("SINE WAVE CURVE FIT RESULTS")
    print("="*50)
    
    for col_name, params in fit_results.items():
        print(f"\n{col_name}:")
        print(f"  Amplitude:     {params['amplitude']:.6f} V")
        print(f"  Frequency:     {params['frequency']:.6f} Hz")
        print(f"  Period:        {1000/params['frequency']:.3f} ms")
        #print(f"  Phase:         {params['phase']:.6f} rad ({np.degrees(params['phase']):.2f}°)")
        print(f"  Offset:        {params['offset']:.6f} V")
        print(f"  Fit Quality:   {params['fit_quality']:.4f} (R²)")
        if params['outliers_removed'] > 0:
            print(f"  Outliers:      {params['outliers_removed']} removed")
    
    # Calculate phase difference if both columns are fitted
    if 'Intensity (V)' in fit_results and 'Beacon X DAC (V)' in fit_results:
        phase_intensity = fit_results['Intensity (V)']['phase']
        phase_beacon = fit_results['Beacon X DAC (V)']['phase']
        freq_intensity = fit_results['Intensity (V)']['frequency']
        freq_beacon = fit_results['Beacon X DAC (V)']['frequency']
        freq_avg = (freq_intensity + freq_beacon) / 2
        
        # Phase difference (wrapped to [-π, π])
        phase_diff_rad = (phase_beacon - phase_intensity)
        # Wrap to [-π, π]
        phase_diff_rad = np.arctan2(np.sin(phase_diff_rad), np.cos(phase_diff_rad))
        
        phase_diff_deg = np.degrees(phase_diff_rad)
        
        # Time delay in milliseconds
        if freq_avg > 0:
            period_ms = 1000 / freq_avg
            phase_diff_ms = (phase_diff_rad / (2 * np.pi)) * period_ms
        else:
            phase_diff_ms = 0
        
        print("\n" + "="*50)
        print("PHASE DIFFERENCE ANALYSIS")
        print("(Beacon X DAC - Intensity)")
        print("="*50)
        print(f"  Phase Diff:    {phase_diff_rad:.6f} radians")
        print(f"                 {phase_diff_deg:.2f}°")
        print(f"  Time Delay:    {phase_diff_ms:.3f} ms")
        print(f"  Freq Match:    Intensity={freq_intensity:.6f} Hz, Beacon={freq_beacon:.6f} Hz")
        print(f"  Freq Diff:     {abs(freq_intensity-freq_beacon):.6f} Hz ({100*abs(freq_intensity-freq_beacon)/freq_avg:.2f}%)")
        print("="*50)
    
    # Calculate phase difference between X DAC and Y DAC
    if 'X DAC (V)' in fit_results and 'Y DAC (V)' in fit_results:
        phase_x = fit_results['X DAC (V)']['phase']
        phase_y = fit_results['Y DAC (V)']['phase']
        freq_x = fit_results['X DAC (V)']['frequency']
        freq_y = fit_results['Y DAC (V)']['frequency']
        freq_avg_xy = (freq_x + freq_y) / 2
        
        # Phase difference (wrapped to [-π, π])
        phase_diff_rad_xy = (phase_y - phase_x)
        # Wrap to [-π, π]
        phase_diff_rad_xy = np.arctan2(np.sin(phase_diff_rad_xy), np.cos(phase_diff_rad_xy))
        
        phase_diff_deg_xy = np.degrees(phase_diff_rad_xy)
        
        # Time delay in milliseconds
        if freq_avg_xy > 0:
            period_ms_xy = 1000 / freq_avg_xy
            phase_diff_ms_xy = (phase_diff_rad_xy / (2 * np.pi)) * period_ms_xy
        else:
            phase_diff_ms_xy = 0
        
        print("\n" + "="*50)
        print("PHASE DIFFERENCE ANALYSIS")
        print("(Y DAC - X DAC)")
        print("="*50)
        print(f"  Phase Diff:    {phase_diff_rad_xy:.6f} radians")
        print(f"                 {phase_diff_deg_xy:.2f}°")
        print(f"  Time Delay:    {phase_diff_ms_xy:.3f} ms")
        print(f"  Freq Match:    X DAC={freq_x:.6f} Hz, Y DAC={freq_y:.6f} Hz")
        print(f"  Freq Diff:     {abs(freq_x-freq_y):.6f} Hz ({100*abs(freq_x-freq_y)/freq_avg_xy:.2f}%)")
        print("="*50)

# Display the plot
plt.show()