import numpy as np
import matplotlib.pyplot as plt

# Raw experimental data
frequency_hz = np.array([
    1, 2, 5, 10, 15, 20, 25, 27, 28, 29, 30, 31, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 300, 400, 500
])
displacement_um = np.array([
    394, 387, 392, 401, 560, 461, 646, 1467, 2218, 1846, 1487,
    1410, 1360, 749, 527, 364, 294, 189, 131, 87, 67, 51, 30,
    23, 15, 11, 5, 5, 1
])

# Step 1: Find resonance frequency (max displacement)
max_disp = np.max(displacement_um)
resonance_index = np.argmax(displacement_um)
f0 = frequency_hz[resonance_index]
print(f"Resonance frequency f0: {f0} Hz")

# Step 2: Compute half-power displacement level
half_power_level = max_disp / np.sqrt(2)

# Interpolate to find half-power frequencies (left and right of peak)
# Left side
for i in range(resonance_index - 1, -1, -1):
    if displacement_um[i] < half_power_level:
        f_low = np.interp(
            half_power_level,
            [displacement_um[i], displacement_um[i+1]],
            [frequency_hz[i], frequency_hz[i+1]]
        )
        break

# Right side
for i in range(resonance_index + 1, len(frequency_hz) - 1):
    if displacement_um[i] < half_power_level:
        f_high = np.interp(
            half_power_level,
            [displacement_um[i-1], displacement_um[i]],
            [frequency_hz[i-1], frequency_hz[i]]
        )
        break

# Step 3: Compute bandwidth, Q, damping ratio
bandwidth = f_high - f_low
Q = f0 / bandwidth
zeta = 1 / (2 * Q)

print(f"Half-power frequencies: {f_low:.2f} Hz, {f_high:.2f} Hz")
print(f"Bandwidth: {bandwidth:.2f} Hz")
print(f"Quality factor Q: {Q:.2f}")
print(f"Damping ratio ζ: {zeta:.4f}")

# Step 4: Compute phase shift
def compute_phase(f, f0, zeta):
    numerator = 2 * zeta * f * f0
    denominator = f0**2 - f**2
    phase_rad = np.arctan2(numerator, denominator)
    return np.degrees(phase_rad)

phase_deg = compute_phase(frequency_hz, f0, zeta)

# Step 5: Plotting
plt.figure(figsize=(12, 5))

# Plot 1: Displacement vs frequency

plt.plot(frequency_hz, displacement_um, marker='o', label='Displacement')
plt.axvline(f0, color='r', linestyle='--', label=f'Resonance (f₀ = {f0} Hz)')
plt.axhline(half_power_level, color='gray', linestyle='--', label='Half-power level')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Displacement (μm)')
plt.title('Frequency Response')
plt.grid(True)
plt.legend()
plt.show()

# Plot 2: Phase vs frequency

plt.plot(frequency_hz, phase_deg, marker='s', color='orange')
plt.axhline(90, color='gray', linestyle='--', label='Phase at resonance')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase Shift (degrees)')
plt.title('Phase Shift vs Frequency')
plt.grid(True)
plt.legend()
plt.xlim(0,150)
plt.tight_layout()
plt.show()
