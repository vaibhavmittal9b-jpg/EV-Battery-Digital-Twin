from flask import Flask, render_template, request


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(value, minimum, maximum):
    """
    Keep a value between minimum and maximum limits.
    """
    return max(minimum, min(maximum, value))


def safe_float(value, default):
    """
    Convert form input to float safely.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default):
    """
    Convert form input to integer safely.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# OCV - SOC MODEL
# ============================================================

def cell_ocv_from_soc(soc):
    """
    Approximate lithium-ion Open Circuit Voltage (OCV)
    from State of Charge.

    Uses interpolation between approximate Li-ion OCV points.
    """

    soc_points = [
        0,
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        80,
        90,
        100
    ]

    voltage_points = [
        3.00,
        3.40,
        3.55,
        3.65,
        3.72,
        3.78,
        3.85,
        3.95,
        4.05,
        4.15,
        4.20
    ]

    soc = clamp(soc, 0, 100)

    # Find the correct interval
    for i in range(len(soc_points) - 1):

        lower_soc = soc_points[i]
        upper_soc = soc_points[i + 1]

        if lower_soc <= soc <= upper_soc:

            lower_voltage = voltage_points[i]
            upper_voltage = voltage_points[i + 1]

            fraction = (
                (soc - lower_soc)
                / (upper_soc - lower_soc)
            )

            voltage = (
                lower_voltage
                + fraction
                * (upper_voltage - lower_voltage)
            )

            return voltage

    return voltage_points[-1]


# ============================================================
# EV DRIVING CYCLE
# ============================================================

def get_current_and_mode(time):
    """
    Virtual EV driving cycle.

    Positive current:
        Battery discharge

    Negative current:
        Regenerative braking / charging
    """

    cycle_time = time % 120

    # 0 - 10 seconds
    if cycle_time < 10:
        return 1.0, "Idle"

    # 10 - 25 seconds
    elif cycle_time < 25:
        return 25.0, "Strong Acceleration"

    # 25 - 55 seconds
    elif cycle_time < 55:
        return 10.0, "Cruising"

    # 55 - 70 seconds
    elif cycle_time < 70:
        return 18.0, "Acceleration"

    # 70 - 90 seconds
    elif cycle_time < 90:
        return 8.0, "Cruising"

    # 90 - 100 seconds
    elif cycle_time < 100:
        return -12.0, "Regenerative Braking"

    # 100 - 115 seconds
    elif cycle_time < 115:
        return 5.0, "Slow Driving"

    # 115 - 120 seconds
    else:
        return 0.5, "Stopped"


# ============================================================
# MAIN DIGITAL TWIN SIMULATION
# ============================================================

def simulate_battery(
    initial_soc=95,
    load_multiplier=1.0,
    ambient_temperature=25,
    aging_cycles=0,
    fault_mode="none"
):

    # ========================================================
    # BATTERY PACK CONFIGURATION
    # ========================================================

    nominal_capacity_ah = 12.0

    series_groups = 12

    # Fresh battery internal resistance
    base_r0 = 0.03

    # RC polarization model
    base_r1 = 0.02

    c1 = 2000.0

    # ========================================================
    # INITIAL CONDITIONS
    # ========================================================

    soc = clamp(
        float(initial_soc),
        0,
        100
    )

    temperature = float(
        ambient_temperature
    )

    # Polarization voltage
    polarization_voltage = 0.0


    # ========================================================
    # STATE OF HEALTH
    # ========================================================

    # Demo aging model:
    # 0.02% SOH reduction per equivalent aging cycle

    soh = (
        100.0
        - aging_cycles * 0.02
    )

    soh = clamp(
        soh,
        60.0,
        100.0
    )


    # ========================================================
    # EFFECTIVE BATTERY CAPACITY
    # ========================================================

    # As SOH decreases, usable capacity decreases.

    effective_capacity_ah = (
        nominal_capacity_ah
        * soh
        / 100.0
    )


    # ========================================================
    # REMAINING USEFUL LIFE
    # ========================================================

    end_of_life_soh = 80.0

    degradation_per_cycle = 0.02

    if soh <= end_of_life_soh:

        rul_cycles = 0.0

    else:

        rul_cycles = (
            soh
            - end_of_life_soh
        ) / degradation_per_cycle


    # ========================================================
    # AGING EFFECT ON INTERNAL RESISTANCE
    # ========================================================

    # Older batteries generally have higher internal resistance.

    aging_resistance_factor = (
        1.0
        + (100.0 - soh) * 0.015
    )

    r0 = (
        base_r0
        * aging_resistance_factor
    )

    r1 = (
        base_r1
        * aging_resistance_factor
    )


    # ========================================================
    # DATA STORAGE FOR GRAPHS
    # ========================================================

    times = []

    soc_values = []

    voltage_values = []

    current_values = []

    temperature_values = []

    soh_values = []

    rul_values = []

    driving_modes = []


    # ========================================================
    # VALUES FOR SAFETY ANALYSIS
    # ========================================================

    highest_temperature = temperature

    highest_voltage = 0.0

    lowest_voltage = 1000.0

    highest_discharge_current = 0.0

    highest_charge_current = 0.0


    # ========================================================
    # SIMULATION PARAMETERS
    # ========================================================

    simulation_time = 600

    dt = 5


    latest_current = 0.0

    latest_voltage = 0.0

    latest_mode = "Idle"

    latest_pack_ocv = 0.0


    # ========================================================
    # MAIN SIMULATION LOOP
    # ========================================================

    for time in range(
        0,
        simulation_time + 1,
        dt
    ):

        # ----------------------------------------------------
        # EV DRIVING CONDITION
        # ----------------------------------------------------

        current, driving_mode = (
            get_current_and_mode(time)
        )

        # Apply user-selected load multiplier

        current = (
            current
            * load_multiplier
        )


        # ----------------------------------------------------
        # OPTIONAL OVERCURRENT FAULT SUPPORT
        # ----------------------------------------------------

        if fault_mode == "overcurrent_fault":

            if 120 <= time <= 180:

                current = 45.0


        # ----------------------------------------------------
        # SOC CALCULATION
        # ----------------------------------------------------

        discharged_ah = (
            current
            * dt
            / 3600.0
        )

        soc_change = (
            discharged_ah
            / effective_capacity_ah
        ) * 100.0

        soc -= soc_change

        soc = clamp(
            soc,
            0.0,
            100.0
        )


        # ----------------------------------------------------
        # OCV CALCULATION
        # ----------------------------------------------------

        cell_ocv = (
            cell_ocv_from_soc(soc)
        )

        pack_ocv = (
            cell_ocv
            * series_groups
        )


        # ----------------------------------------------------
        # 1-RC EQUIVALENT CIRCUIT MODEL
        # ----------------------------------------------------

        dv1_dt = (
            -polarization_voltage
            / (r1 * c1)
            + current / c1
        )

        polarization_voltage += (
            dv1_dt
            * dt
        )


        # Terminal voltage equation

        terminal_voltage = (
            pack_ocv
            - current * r0
            - polarization_voltage
        )


        # ----------------------------------------------------
        # THERMAL MODEL
        # ----------------------------------------------------

        heat_generated = (
            current ** 2
            * r0
        )


        heating_effect = (
            heat_generated
            * dt
            * 0.0004
        )


        cooling_effect = (
            temperature
            - ambient_temperature
        ) * 0.01


        temperature += (
            heating_effect
            - cooling_effect
        )


        # ----------------------------------------------------
        # THERMAL FAULT INJECTION
        # ----------------------------------------------------

        # Inject near the end of the simulation
        # so the dashboard clearly displays the fault.

        if (
            fault_mode == "thermal_fault"
            and time >= 500
        ):

            temperature = max(
                temperature,
                55.0
            )


        # ----------------------------------------------------
        # STORE GRAPH DATA
        # ----------------------------------------------------

        times.append(time)

        soc_values.append(soc)

        voltage_values.append(
            terminal_voltage
        )

        current_values.append(
            current
        )

        temperature_values.append(
            temperature
        )

        soh_values.append(
            soh
        )

        rul_values.append(
            rul_cycles
        )

        driving_modes.append(
            driving_mode
        )


        # ----------------------------------------------------
        # TRACK EXTREME VALUES
        # ----------------------------------------------------

        highest_temperature = max(
            highest_temperature,
            temperature
        )

        highest_voltage = max(
            highest_voltage,
            terminal_voltage
        )

        lowest_voltage = min(
            lowest_voltage,
            terminal_voltage
        )

        highest_discharge_current = max(
            highest_discharge_current,
            current
        )

        highest_charge_current = min(
            highest_charge_current,
            current
        )


        # ----------------------------------------------------
        # STORE LATEST VALUES
        # ----------------------------------------------------

        latest_current = current

        latest_voltage = (
            terminal_voltage
        )

        latest_mode = driving_mode

        latest_pack_ocv = pack_ocv


    # ========================================================
    # CELL GROUP SIMULATION
    # ========================================================

    group_voltages = []


    # Approximate voltage of each series group

    base_group_voltage = (
        latest_voltage
        / series_groups
    )


    for i in range(series_groups):

        # Small manufacturing variation
        normal_variation = (
            (i % 3 - 1)
            * 0.006
        )


        group_voltage = (
            base_group_voltage
            + normal_variation
        )


        # ----------------------------------------------------
        # NORMAL WEAK GROUP
        # ----------------------------------------------------

        # Group 5 is intentionally slightly weaker.

        if i == 4:

            group_voltage -= 0.04


        # ----------------------------------------------------
        # MANUAL CELL FAULT INJECTION
        # ----------------------------------------------------

        if (
            fault_mode == "cell_fault"
            and i == 4
        ):

            group_voltage -= 0.18


        group_voltages.append(
            group_voltage
        )


    # ========================================================
    # CELL IMBALANCE ANALYSIS
    # ========================================================

    highest_group_voltage = max(
        group_voltages
    )

    lowest_group_voltage = min(
        group_voltages
    )


    voltage_imbalance = (
        highest_group_voltage
        - lowest_group_voltage
    )


    weak_group = (
        group_voltages.index(
            lowest_group_voltage
        )
        + 1
    )


    if voltage_imbalance > 0.10:

        cell_status = (
            "CELL IMBALANCE DETECTED"
        )

    else:

        cell_status = "BALANCED"


    # ========================================================
    # BMS FAULT DETECTION
    # ========================================================

    faults = []


    # --------------------------------------------------------
    # VOLTAGE SAFETY
    # --------------------------------------------------------

    if highest_voltage > 50.4:

        faults.append(
            "OVER-VOLTAGE"
        )


    if lowest_voltage < 36.0:

        faults.append(
            "UNDER-VOLTAGE"
        )


    # --------------------------------------------------------
    # TEMPERATURE SAFETY
    # --------------------------------------------------------

    if highest_temperature >= 50.0:

        faults.append(
            "HIGH BATTERY TEMPERATURE"
        )


    if highest_temperature >= 60.0:

        faults.append(
            "CRITICAL OVER-TEMPERATURE"
        )


    # --------------------------------------------------------
    # CURRENT SAFETY
    # --------------------------------------------------------

    if highest_discharge_current > 30.0:

        faults.append(
            "EXCESSIVE DISCHARGE CURRENT"
        )


    if highest_charge_current < -20.0:

        faults.append(
            "EXCESSIVE CHARGING CURRENT"
        )


    # --------------------------------------------------------
    # CELL BALANCING
    # --------------------------------------------------------

    if voltage_imbalance > 0.10:

        faults.append(
            "CELL IMBALANCE"
        )


    # --------------------------------------------------------
    # BATTERY HEALTH
    # --------------------------------------------------------

    if soh <= 80.0:

        faults.append(
            "LOW BATTERY HEALTH"
        )


    # --------------------------------------------------------
    # SIMULATED FAULT DESCRIPTION
    # --------------------------------------------------------

    if fault_mode == "thermal_fault":

        faults.append(
            "SIMULATED THERMAL FAULT"
        )


    if fault_mode == "cell_fault":

        faults.append(
            "SIMULATED WEAK CELL FAULT"
        )


    # Remove duplicate fault messages

    faults = list(
        dict.fromkeys(faults)
    )


    # ========================================================
    # BATTERY STATUS
    # ========================================================

    status = "NORMAL"


    if len(faults) > 0:

        status = "WARNING"


    # Critical conditions

    if (
        highest_temperature >= 60.0
        or lowest_voltage < 34.0
        or soh < 70.0
    ):

        status = "CRITICAL"


    # ========================================================
    # RESULT FOR DASHBOARD
    # ========================================================

    battery = {

        "soc":
            soc,

        "soh":
            soh,

        "voltage":
            latest_voltage,

        "current":
            latest_current,

        "temperature":
            temperature,

        "rul":
            rul_cycles,

        "status":
            status,

        "faults":
            ", ".join(faults)
            if faults
            else "None",

        "weak_group":
            weak_group,

        "cell_imbalance":
            voltage_imbalance,

        "cell_status":
            cell_status,

        "driving_condition":
            latest_mode,

        # Extra values available for future UI features

        "effective_capacity":
            effective_capacity_ah,

        "peak_temperature":
            highest_temperature,

        "pack_ocv":
            latest_pack_ocv
    }


    # ========================================================
    # GRAPH DATA
    # ========================================================

    graph = {

        "time":
            times,

        "soc":
            soc_values,

        "soh":
            soh_values,

        "voltage":
            voltage_values,

        "current":
            current_values,

        "temperature":
            temperature_values,

        "rul":
            rul_values,

        "driving_mode":
            driving_modes
    }


    return (
        battery,
        graph,
        group_voltages
    )


# ============================================================
# MAIN WEB PAGE
# ============================================================

@app.route(
    "/",
    methods=[
        "GET",
        "POST"
    ]
)
def home():

    # ========================================================
    # READ SIMULATION CONTROL PANEL VALUES
    # ========================================================

    initial_soc = safe_float(
        request.form.get(
            "initial_soc"
        ),
        95.0
    )


    load_multiplier = safe_float(
        request.form.get(
            "load_multiplier"
        ),
        1.0
    )


    ambient_temperature = safe_float(
        request.form.get(
            "ambient_temperature"
        ),
        25.0
    )


    aging_cycles = safe_int(
        request.form.get(
            "aging_cycles"
        ),
        0
    )


    fault_mode = request.form.get(
        "fault_mode",
        "none"
    )


    # ========================================================
    # SAFETY LIMITS FOR USER INPUT
    # ========================================================

    initial_soc = clamp(
        initial_soc,
        10.0,
        100.0
    )


    load_multiplier = clamp(
        load_multiplier,
        0.5,
        2.0
    )


    ambient_temperature = clamp(
        ambient_temperature,
        -10.0,
        60.0
    )


    aging_cycles = int(
        clamp(
            aging_cycles,
            0,
            1500
        )
    )


    valid_fault_modes = [
        "none",
        "cell_fault",
        "thermal_fault",
        "overcurrent_fault"
    ]


    if fault_mode not in valid_fault_modes:

        fault_mode = "none"


    # ========================================================
    # RUN DIGITAL TWIN
    # ========================================================

    battery, graph, groups = (
        simulate_battery(

            initial_soc=
                initial_soc,

            load_multiplier=
                load_multiplier,

            ambient_temperature=
                ambient_temperature,

            aging_cycles=
                aging_cycles,

            fault_mode=
                fault_mode
        )
    )


    # ========================================================
    # RETURN CONTROL VALUES TO HTML
    # ========================================================

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


    # ========================================================
    # DISPLAY DASHBOARD
    # ========================================================

    return render_template(

        "index.html",

        battery=
            battery,

        graph=
            graph,

        groups=
            groups,

        controls=
            controls
    )


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )