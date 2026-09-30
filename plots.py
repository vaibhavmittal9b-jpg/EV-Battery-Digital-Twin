import pandas as pd
import matplotlib.pyplot as plt


# Load simulation data
df = pd.read_csv("data/battery_data.csv")


# -------------------------------
# Current vs Time
# -------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    df["Time"],
    df["Current"]
)

plt.xlabel("Time (seconds)")
plt.ylabel("Current (A)")
plt.title("EV Battery Current vs Time")

plt.grid()

plt.show()


# -------------------------------
# Voltage vs Time
# -------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    df["Time"],
    df["Voltage"]
)

plt.xlabel("Time (seconds)")
plt.ylabel("Voltage (V)")
plt.title("Battery Voltage vs Time")

plt.grid()

plt.show()


# -------------------------------
# SOC vs Time
# -------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    df["Time"],
    df["SOC"]
)

plt.xlabel("Time (seconds)")
plt.ylabel("State of Charge (%)")
plt.title("Battery SOC vs Time")

plt.grid()

plt.show()


# -------------------------------
# Temperature vs Time
# -------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    df["Time"],
    df["Temperature"]
)

plt.xlabel("Time (seconds)")
plt.ylabel("Temperature (°C)")
plt.title("Battery Temperature vs Time")

plt.grid()

plt.show()
