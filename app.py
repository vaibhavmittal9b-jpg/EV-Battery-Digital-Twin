from flask import Flask, render_template, request
import math

app = Flask(__name__)


def simulate_battery(
    initial_soc=95,
    load_multiplier=1.0,
    ambient_temperature=25,
    aging_cycles=0,
    fault_mode="none"
):
    capacity_ah = 12.0
    r0 = 0.03

    soc = float(initial_soc)
    temperature = float(ambient_temperature)

    # Accelerated aging for demonstration
    soh = max(
        60.0,
        100.0 - aging_cycles * 0.02
    )

    # RUL assuming 80% end-of-life
    if soh <= 80:
        rul = 0
    else:
        rul = (soh - 80) / 0.02

    times = []
    soc_values = []
    voltage_values = []
    current_values = []
    temperature_values = []
    soh_values = []
    rul_values = []

    group_voltages = []

    def get_current(time):
        cycle = time % 120

        if cycle < 10:
            return 1.0

        elif cycle < 25:
            return 25.0

        elif cycle < 55:
            return 10.0

        elif cycle < 70:
            return 18.0

        elif cycle < 90:
            return 8.0

        elif cycle < 100:
            return -12.0

        elif cycle < 115:
            return 5.0

        else:
            return 0.5

    dt = 5

    latest_current = 0
    latest_voltage = 0

    for time in range(0, 601, dt):

        current = (
            get_current(time)
            * load_multiplier
        )

        # SOC calculation
        discharged_ah = (
            current * dt / 3600
        )

        soc_change = (
            discharged_ah
            / capacity_ah
        ) * 100

        soc -= soc_change

        soc = max(
            0,
            min(100, soc)
        )

        # Approximate Li-ion cell OCV
        cell_ocv = (
            3.0
            + 1.2 * (soc / 100)
        )

        pack_ocv = (
            cell_ocv * 12
        )

        # Aging increases resistance
        aging_factor = (
            1
            + (100 - soh) * 0.015
        )

        resistance = (
            r0 * aging_factor
        )

        voltage = (
            pack_ocv
            - current * resistance
        )

        # Simple thermal behaviour
        heat = (
            current ** 2
            * resistance
        )

        temperature += (
            heat * dt * 0.0004
        )

        temperature -= (
            temperature
            - ambient_temperature
        ) * 0.01

        times.append(time)
        soc_values.append(soc)
        voltage_values.append(voltage)
        current_values.append(current)
        temperature_values.append(
            temperature
        )
        soh_values.append(soh)
        rul_values.append(rul)

        latest_current = current
        latest_voltage = voltage

    # -----------------------------------
    # CELL GROUP SIMULATION
    # -----------------------------------

    base_group_voltage = (
        latest_voltage / 12
    )

    for i in range(12):

        voltage = base_group_voltage

        # Small normal variation
        voltage += (
            (i % 3 - 1) * 0.006
        )

        # Simulated weak group
        if i == 4:
            voltage -= 0.04

        # Manual fault injection
        if fault_mode == "cell_fault" and i == 4:
            voltage -= 0.18

        group_voltages.append(
            voltage
        )

    highest = max(group_voltages)
    lowest = min(group_voltages)

    imbalance = (
        highest - lowest
    )

    weak_group = (
        group_voltages.index(
            lowest
        ) + 1
    )

    # -----------------------------------
    # STATUS LOGIC
    # -----------------------------------

    faults = []

    if temperature > 50:
        faults.append(
            "OVER-TEMPERATURE"
        )

    if latest_voltage > 50.4:
        faults.append(
            "OVER-VOLTAGE"
        )

    if latest_voltage < 36:
        faults.append(
            "UNDER-VOLTAGE"
        )

    if abs(latest_current) > 30:
        faults.append(
            "EXCESSIVE CURRENT"
        )

    if imbalance > 0.10:
        faults.append(
            "CELL IMBALANCE"
        )

    if soh < 80:
        faults.append(
            "BATTERY HEALTH CRITICAL"
        )

    if fault_mode == "thermal_fault":
        temperature = 55
        faults.append(
            "SIMULATED THERMAL FAULT"
        )

    if faults:
        status = "WARNING"
    else:
        status = "NORMAL"

    if (
        temperature >= 60
        or latest_voltage < 34
        or soh < 70
    ):
        status = "CRITICAL"

    cell_status = (
        "CELL IMBALANCE DETECTED"
        if imbalance > 0.10
        else "BALANCED"
    )

    battery = {
        "soc": soc,
        "soh": soh,
        "voltage": latest_voltage,
        "current": latest_current,
        "temperature": temperature,
        "rul": rul,
        "status": status,
        "faults": (
            ", ".join(faults)
            if faults
            else "None"
        ),
        "weak_group": weak_group,
        "cell_imbalance": imbalance,
        "cell_status": cell_status,
        "driving_condition":
            "Simulation Complete"
    }

    graph = {
        "time": times,
        "soc": soc_values,
        "soh": soh_values,
        "voltage": voltage_values,
        "current": current_values,
        "temperature": temperature_values,
        "rul": rul_values
    }

    return (
        battery,
        graph,
        group_voltages
    )


@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    initial_soc = float(
        request.form.get(
            "initial_soc",
            95
        )
    )

    load_multiplier = float(
        request.form.get(
            "load_multiplier",
            1
        )
    )

    ambient_temperature = float(
        request.form.get(
            "ambient_temperature",
            25
        )
    )

    aging_cycles = int(
        request.form.get(
            "aging_cycles",
            0
        )
    )

    fault_mode = request.form.get(
        "fault_mode",
        "none"
    )

    battery, graph, groups = (
        simulate_battery(
            initial_soc,
            load_multiplier,
            ambient_temperature,
            aging_cycles,
            fault_mode
        )
    )

    controls = {
        "initial_soc":
            initial_soc,

        "load_multiplier":
            load_multiplier,

        "ambient_temperature":
            ambient_temperature,

        "aging_cycles":
            aging_cycles,

        "fault_mode":
            fault_mode
    }

    return render_template(
        "index.html",
        battery=battery,
        graph=graph,
        groups=groups,
        controls=controls
    )


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )