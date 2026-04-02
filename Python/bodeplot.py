import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Manually define the data (can replace with CSV if needed)
# -----------------------------
###### Horizontal resonance test of PCB 2, 0.230 V Driver #####
data = {
    'Frequency (Hz)': [
        1, 2, 5, 10, 15, 20, 25, 27, 28, 29, 30, 31, 35, 40, 45, 50,
        60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 300, 400, 500
    ],
    'Displacement (Microns)': [
        394,387,392,401,560,461,646,1467,2218,1846,1487,1410,1360,749,527,364,294,189,131,87,67,51,30,23,15,11,5,5,1
    ]
}

df = pd.DataFrame(data)

# -----------------------------
# Plot 1: Displacement vs Frequency (linear)
# -----------------------------
plt.figure(figsize=(10, 6))
plt.plot(df['Frequency (Hz)'], df['Displacement (Microns)'], marker='o')
plt.title('PCB 2 Displacement vs Frequency')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Displacement (Microns)')
plt.grid(True)
plt.tight_layout()
plt.show()

# -----------------------------
# Plot 2: Bode-style Plot (log frequency, dB displacement)
# -----------------------------
# Convert displacement to dB (20 * log10(x))
df['Displacement (dB)'] = 20 * np.log10(df['Displacement (Microns)'])
df['Log Frequency'] = np.log10(df['Frequency (Hz)'])

# Find resonance (peak) and anti-resonance (min)
resonance_idx = df['Displacement (Microns)'].idxmax()
antiresonance_idx = df['Displacement (Microns)'].idxmin()

res_freq = df.loc[resonance_idx, 'Frequency (Hz)']
res_disp = df.loc[resonance_idx, 'Displacement (dB)']

anti_freq = df.loc[antiresonance_idx, 'Frequency (Hz)']
anti_disp = df.loc[antiresonance_idx, 'Displacement (dB)']

plt.figure(figsize=(10, 6))
plt.plot(df['Frequency (Hz)'], df['Displacement (dB)'], marker='o')
plt.xscale('log')
plt.title('PCB 2 Bode Plot: Displacement vs Frequency')
plt.xlabel('Frequency (Hz) [Log Scale]')
plt.ylabel('Displacement (dB)')
plt.grid(True, which='both', ls='--', lw=0.5)

# Highlight resonance & anti-resonance
plt.axvline(res_freq, color='green', linestyle='--', label=f'Resonance: {res_freq} Hz')
plt.axvline(anti_freq, color='red', linestyle='--', label=f'Anti-Resonance: {anti_freq} Hz')
plt.legend()
plt.tight_layout()
plt.show()


# derivation of the bode plot to get the phase change

# -----------------------------
# Plot 2: Phase Change Plot, Derivation of Frequency and Displacement 
# -----------------------------
freq = np.array(data['Frequency (Hz)'])
disp = np.array(data['Displacement (Microns)'])
dx = np.gradient(freq)
dy = np.gradient(disp)
dx_log = np.log10(dx)
dy_dB = 20 * np.log10(dy)



plt.figure(figsize=(10,6))
plt.plot(dx_log, dy_dB, marker = 'o')
plt.xscale('log')
plt.title('PCB 2 Phase Change: Displacement vs Frequency')
plt.xlabel('Frequency (Hz) [Log Scale]')
plt.ylabel('Phase Change')
plt.grid(True, which='both', ls='--', lw=0.5)
plt.tight_layout()

plt.show()

# -----------------------------
# Logarithmic Derivative (Not Actual Phase)
# -----------------------------
# Compute logarithmic frequency and displacement
log_freq = np.log10(freq)
log_disp = np.log10(disp)

# Numerical derivative (slope of log-log curve)
d_log_disp = np.gradient(log_disp, log_freq)  # This is d(log(A))/d(log(f))

plt.figure(figsize=(10, 6))
plt.plot(freq, d_log_disp, marker='o', color='purple')
plt.xscale('log')
plt.title('Logarithmic Slope of Displacement (dB) vs Frequency')
plt.xlabel('Frequency (Hz) [Log Scale]')
plt.ylabel('d(log Amplitude)/d(log Frequency)')
plt.grid(True, which='both', ls='--', lw=0.5)
plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt

# Given values (you can replace these with your actual data)
f_r = 28  # resonance frequency in Hz (from your data)
x_max = 2218  # max displacement at resonance (microns)

# Optional: estimate damping ratio if you know -3dB frequencies
# Example:
f1 = 25   # lower -3dB frequency (example)
f2 = 31   # upper -3dB frequency (example)
zeta = (f2 - f1) / (2 * f_r)

# Frequency range to simulate
f = np.linspace(1, 100, 1000)
omega_ratio = f / f_r

# Compute phase response (in degrees)
phi_rad = np.arctan2(2 * zeta * omega_ratio, 1 - omega_ratio**2)
phi_deg = np.degrees(phi_rad)

# Plot the phase
plt.figure(figsize=(10, 6))
plt.plot(f, phi_deg, label=f'ζ = {zeta:.2f}')
plt.axvline(f_r, color='red', linestyle='--', label=f'Resonance: {f_r} Hz')
plt.title('Theoretical Phase Response of Driven Harmonic Oscillator')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase (degrees)')
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt

# Parameters from your data
f_r = 28  # Resonance frequency in Hz
zeta = 0.0566  # Estimated damping ratio

# Frequency range for plotting
f = np.linspace(1, 100, 1000)
omega_ratio = f / f_r

# Compute phase in radians and convert to degrees
phi_rad = np.arctan2(2 * zeta * omega_ratio, 1 - omega_ratio**2)
phi_deg = np.degrees(phi_rad)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(f, phi_deg, label=f'Damping ratio ζ = {zeta:.3f}')
plt.axvline(f_r, color='red', linestyle='--', label=f'Resonance = {f_r} Hz')
plt.axhline(90, color='gray', linestyle=':', linewidth=1)
plt.title('Theoretical Phase Response of Driven Harmonic Oscillator')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase Shift (degrees)')
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

# -----------------------------
# Step 1: Find Resonance Frequency and Max Displacement
# -----------------------------
resonance_idx = df['Displacement (Microns)'].idxmax()
f_r = df.loc[resonance_idx, 'Frequency (Hz)']
x_max = df.loc[resonance_idx, 'Displacement (Microns)']
print(f"Resonance frequency: {f_r} Hz, Max displacement: {x_max} microns")

# -----------------------------
# Step 2: Compute -3dB Amplitude
# -----------------------------
x_3db = x_max / np.sqrt(2)
print(f"-3dB displacement amplitude: {x_3db:.2f} microns")

# -----------------------------
# Step 3: Interpolate f1 (given) and f2 (from data)
# -----------------------------
# f1 is provided:
f1 = 26.6

# Estimate f2 (between 29 Hz and 30 Hz)
x_29 = df[df['Frequency (Hz)'] == 29]['Displacement (Microns)'].values[0]
x_30 = df[df['Frequency (Hz)'] == 30]['Displacement (Microns)'].values[0]

# Linear interpolation to find f2 where displacement = x_3db
f2 = 29 + (x_29 - x_3db) / (x_29 - x_30)
print(f"Estimated f2 (upper -3dB point): {f2:.2f} Hz")

# -----------------------------
# Step 4: Calculate Damping Ratio
# -----------------------------
zeta = (f2 - f1) / (2 * f_r)
Q = 1 / (2 * zeta)
print(f"Estimated damping ratio (ζ): {zeta:.4f}")
print(f"Estimated quality factor (Q): {Q:.2f}")

# -----------------------------
# Step 5: Plot Theoretical Phase Response
# -----------------------------
f = np.linspace(1, 100, 1000)
omega_ratio = f / f_r
phi_rad = np.arctan2(2 * zeta * omega_ratio, 1 - omega_ratio**2)
phi_deg = np.degrees(phi_rad)

plt.figure(figsize=(10, 6))
plt.plot(f, phi_deg, label=f'ζ = {zeta:.3f}')
plt.axvline(f_r, color='red', linestyle='--', label=f'Resonance = {f_r} Hz')
plt.axhline(90, color='gray', linestyle=':', linewidth=1, label='90° Phase Shift')
plt.title('Theoretical Phase Response of Driven Harmonic Oscillator')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase Shift (degrees)')
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()
