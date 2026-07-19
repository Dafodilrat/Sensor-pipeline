import numpy as np
import matplotlib.pyplot as plt

t = np.linspace(0, 1, 1000)
y1 = np.sin(2 * np.pi * 5 * t)  # 5 Hz
y2 = np.sin(2 * np.pi * 6 * t)  # 6 Hz
y_sum = y1 + y2

plt.figure(figsize=(10, 4))
plt.plot(t, y1, label="5 Hz", alpha=0.7)
plt.plot(t, y2, label="6 Hz", alpha=0.7)
plt.plot(t, y_sum, label="Sum (5 Hz + 6 Hz)", color="black", linewidth=2)
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.legend()
plt.title("Beating Effect: Sum of 5 Hz and 6 Hz Sine Waves")
plt.grid(True)
plt.savefig("test.png", dpi=200, bbox_inches="tight")