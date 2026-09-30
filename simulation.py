from battery_model import BatteryModel
from driving_cycle import get_current
from bms_monitor import BMSMonitor
from cell_model import CellPackModel

import pandas as pd
import os


battery = BatteryModel()
bms = BMSMonitor()
cell_pack = CellPackModel()

print("==============================================")
print("       EV BATTERY DIGITAL TWIN")
print("==============================================")

# Simulation settings
simulation_time = 600
time_step = 5

# Empty list to store results
simulation_data = []

print("\nStarting EV Driving Simulation...\n")


for time in range(0, simulation_time + 1, time_step):

    # Get current from virtual driving cycle
    current = get_current(time)
    

    # Update battery model
    data = battery.step(
        current=current,
        dt=time_step
    )
    cell_data = cell_pack.step(
    pack_ocv=data["OCV"],
    current=current
)

    # Check battery status
    status, faults = bms.check_battery(
        voltage=data["Voltage"],
        current=data["Current"],
        temperature=data["Temperature"],
        soc=data["SOC"]
    )

    # Determine driving condition
    if current >= 20:
        condition = "Strong Acceleration"

    elif current >= 12:
        condition = "Acceleration"

    elif current >= 5:
        condition = "Cruising"

    elif current < 0:
        condition = "Regenerative Braking"

    elif current <= 1:
        condition = "Idle"

    else:
        condition = "Low Load"


    # Store simulation result
    simulation_data.append({
        "Time": time,
        "Driving_Condition": condition,
        "Current": data["Current"],
        "Voltage": data["Voltage"],
        "SOC": data["SOC"],
        "SOH": data["SOH"],
        "Temperature": data["Temperature"],
        "Battery_Status": status,
"Faults": ", ".join(faults) if faults else "None",
"Cell_Imbalance": cell_data["Voltage_Imbalance"],
"Weak_Group": cell_data["Weak_Group"],
"Cell_Status": cell_data["Cell_Status"],
"Group_Voltages": ", ".join(
    f"{v:.3f}"
    for v in cell_data["Group_Voltages"]
),
"RUL_Cycles": data["RUL_Cycles"],
    })


    # Display result in terminal
    print(
    f"Time: {time:4d} s | "
    f"{condition:22s} | "
    f"Current: {data['Current']:6.1f} A | "
    f"Voltage: {data['Voltage']:6.2f} V | "
    f"SOC: {data['SOC']:6.2f} % | "
    f"Temp: {data['Temperature']:5.2f} °C | "
    f"Status: {status}"
)

if cell_data["Cell_Status"] != "BALANCED":

    print(
        f"    ⚠ Cell imbalance detected | "
        f"Weak Group: {cell_data['Weak_Group']} | "
        f"Difference: "
        f"{cell_data['Voltage_Imbalance']:.3f} V"
    )


# Convert collected data into a Pandas DataFrame
df = pd.DataFrame(simulation_data)


# Make sure data folder exists
os.makedirs("data", exist_ok=True)


# Save simulation results
df.to_csv(
    "data/battery_data.csv",
    index=False
)


print("\n==============================================")
print("Simulation Completed")
print("Data saved to: data/battery_data.csv")
print("==============================================")

