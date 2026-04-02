import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal

# -----------------------------
# 1. Original Measured Data
# -----------------------------
data = {
    'Frequency (Hz)': [
        1, 2, 5, 10, 15, 20, 25, 27, 28, 29, 30, 31, 35, 40, 45, 50,
        60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 300, 400, 500
    ],
    'Displacement (Microns)': [
        394, 387, 392, 401, 560, 461, 646, 1467, 2218, 1846, 1487, 1410,
        1360, 749, 527, 364, 294, 189, 131, 87, 67, 51, 30, 23, 15, 11, 5, 5, 1
    ]
}
df = pd.DataFrame(data)

# -----------------------------
# 2. Resonance & Damping Calculation
# -----------------------------
f_r = df.loc[df['Displacement (Microns)'].idxmax(), 'Frequency (Hz)']  # Resonance freq
x_max = df['Displacement (Microns)'].max()
x_3db = x_max / np.sqrt(2)

# Provided lower -3dB frequency
f1 = 26.6
# Interpolated upper -3dB point between 29 and 30 Hz
x_29 = df[df['Frequency (Hz)'] == 29]['Displacement (Microns)'].values[0]
x_30 = df[df['Frequency (Hz)'] == 30]['Displacement (Microns)'].values[0]
f2 = 29 + (x_29 - x_3db) / (x_29 - x_30)

# Damping ratio and Q
zeta = (f2 - f1) / (2 * f_r)
Q = 1 / (2 * zeta)
print(f"f_r = {f_r} Hz, ζ = {zeta:.4f}, Q = {Q:.2f}")

# -----------------------------
# 3. Plot Measured Amplitude + Theoretical Phase
# -----------------------------
# Frequency range for phase response
f_plot = np.linspace(1, 300, 1000)
omega_ratio = f_plot / f_r
phi_rad = np.arctan2(2 * zeta * omega_ratio, 1 - omega_ratio**2)
phi_deg = np.degrees(phi_rad)

fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot measured displacement
ax1.set_title('Measured Displacement & Theoretical Phase')
ax1.set_xlabel('Frequency (Hz)')
ax1.set_ylabel('Displacement (Microns)', color='tab:blue')
ax1.plot(df['Frequency (Hz)'], df['Displacement (Microns)'], 'o-', color='tab:blue', label='Displacement')
ax1.tick_params(axis='y', labelcolor='tab:blue')

# Create second y-axis for phase
ax2 = ax1.twinx()
ax2.set_ylabel('Phase Shift (Degrees)', color='tab:red')
ax2.plot(f_plot, phi_deg, color='tab:red', linestyle='--', label='Phase (Theoretical)')
ax2.tick_params(axis='y', labelcolor='tab:red')
ax2.axhline(90, color='gray', linestyle=':', linewidth=1)
ax1.set_xlim([0, 125])
fig.tight_layout()
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.show()

# -----------------------------
# 4. Build Transfer Function
# -----------------------------
omega_n = 2 * np.pi * f_r  # Natural freq (rad/s)

# Transfer function: H(s) = wn^2 / (s^2 + 2ζwn s + wn^2)
num = [omega_n**2]
den = [1, 2*zeta*omega_n, omega_n**2]
sys = signal.TransferFunction(num, den)

# -----------------------------
# 5. Simulate Time-Domain Response to Sine Input
# -----------------------------
t = np.linspace(0, 2, 1000)  # 2 seconds
input_signal = np.sin(2 * np.pi * f_r * t)  # Sine wave at resonance freq

# Simulate output using lsim (time-domain response)
t_out, y_out, _ = signal.lsim(sys, U=input_signal, T=t)

# Plot the time response
plt.figure(figsize=(10, 6))
plt.plot(t, input_signal, label='Input (Driving Signal)', linestyle='--')
plt.plot(t_out, y_out, label='Output (Displacement Response)', linewidth=2)
plt.title('Simulated Response to Sine Wave at Resonance')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (arbitrary units)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

from scipy.signal import step

t = np.linspace(0, 2, 1000)
t_out, y_step = step(sys, T=t)

plt.figure(figsize=(10, 5))
plt.plot(t_out, y_step, label='Step Response')
plt.title('Step Response of Driven Harmonic Oscillator')
plt.xlabel('Time (s)')
plt.ylabel('Displacement (arbitrary units)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()


from scipy.signal import impulse

t_out, y_impulse = impulse(sys, T=t)

plt.figure(figsize=(10, 5))
plt.plot(t_out, y_impulse, label='Impulse Response', color='orange')
plt.title('Impulse Response of Driven Harmonic Oscillator')
plt.xlabel('Time (s)')
plt.ylabel('Displacement (arbitrary units)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()


import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# System parameters (assumed already defined in your previous code)
# f_r = resonance frequency
# zeta = damping ratio
# omega_n = 2 * np.pi * f_r

# Define transfer function of the system
num = [omega_n**2]
den = [1, 2*zeta*omega_n, omega_n**2]
sys = signal.TransferFunction(num, den)

# Time vector (you may increase duration for lower frequencies)
t = np.linspace(0, 0.5, 2000)  # 0.5 seconds total

# Frequencies to sweep through
frequencies = [10, 50, 100, 200, 300, 400, 500]

# Plot responses
plt.figure(figsize=(12, 8))

for f in frequencies:
    # Generate square wave at frequency f
    input_force = signal.square(2 * np.pi * f * t)
    
    # Simulate response
    t_out, y_out, _ = signal.lsim(sys, U=input_force, T=t)
    
    # Plot
    plt.plot(t_out, y_out, label=f'{f} Hz')

plt.title('System Response to Square Wave Input at Varying Frequencies')
plt.xlabel('Time (s)')
plt.ylabel('Displacement (arbitrary units)')
plt.grid(True)
plt.legend(title='Square Wave Frequency')
plt.tight_layout()
plt.show()
