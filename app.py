from flask import Flask, render_template, request


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def safe_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# LI-ION OCV - SOC MODEL
# ============================================================

def cell_ocv_from_soc(soc):

    soc_points = [
        0, 10, 20, 30, 40,
        50, 60, 70, 80, 90, 100
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

            return (
                lower_voltage
                + fraction
                * (upper_voltage - lower_voltage)
            )

    return voltage_points[-1]


# ============================================================
# EV DRIVING CYCLE
# ============================================================

def get_current_and_mode(time):

    cycle_time = time % 120

    if cycle_time < 10:
        return 1.0, "Idle"

    elif cycle_time < 25:
        return 25.0, "Strong Acceleration"

    elif cycle_time < 55:
        return 10.0, "Cruising"

    elif cycle_time < 70:
        return 18.0, "Acceleration"

    elif cycle_time < 90:
        return 8.0, "Cruising"

    elif cycle_time < 100:
        return -12.0, "Regenerative Braking"

    elif cycle_time < 115:
        return 5.0, "Slow Driving"

    else:
        return 0.5, "Stopped"


# ============================================================
# DIGITAL TWIN SIMULATION
# ============================================================

def simulate_battery(
    initial_soc=95,
    load_multiplier=1.0,
    ambient_temperature=25,
    aging_cycles=0,
    fault_mode="none"
):

    # --------------------------------------------------------
    # BATTERY CONFIGURATION
    # --------------------------------------------------------

    nominal_capacity_ah = 12.0

    series_groups = 12

    base_r0 = 0.03
    base_r1 = 0.02

    c1 = 2000.0

    simulation_time = 600
    dt = 5


    # --------------------------------------------------------
    # INITIAL CONDITIONS
    # --------------------------------------------------------

    soc = clamp(
        float(initial_soc),
        0,
        100
    )

    temperature = float(
        ambient_temperature
    )

    polarization_voltage = 0.0


    # --------------------------------------------------------
    # SOH MODEL
    # --------------------------------------------------------

    soh = (
        100.0
        - aging_cycles * 0.02
    )

    soh = clamp(
        soh,
        60.0,
        100.0
    )


    # --------------------------------------------------------
    # EFFECTIVE CAPACITY
    # --------------------------------------------------------

    effective_capacity_ah = (
        nominal_capacity_ah
        * soh
        / 100.0
    )


    # --------------------------------------------------------
    # RUL
    # --------------------------------------------------------

    end_of_life_soh = 80.0
    degradation_per_cycle = 0.02

    if soh <= end_of_life_soh:

        rul_cycles = 0.0

    else:

        rul_cycles = (
            soh
            - end_of_life_soh
        ) / degradation_per_cycle


    # --------------------------------------------------------
    # AGING EFFECT ON RESISTANCE
    # --------------------------------------------------------

    resistance_factor = (
        1.0
        + (100.0 - soh) * 0.015
    )

    r0 = (
        base_r0
        * resistance_factor
    )

    r1 = (
        base_r1
        * resistance_factor
    )


    # --------------------------------------------------------
    # GRAPH STORAGE
    # --------------------------------------------------------

    times = []

    soc_values = []

    soh_values = []

    voltage_values = []

    current_values = []

    temperature_values = []

    rul_values = []

    driving_modes = []

    consumed_energy_values = []

    regen_energy_values = []

    group_voltage_history = []


    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    consumed_energy_wh = 0.0

    regen_energy_wh = 0.0


    # --------------------------------------------------------
    # EXTREME VALUES
    # --------------------------------------------------------

    highest_temperature = temperature

    highest_voltage = 0.0

    lowest_voltage = 1000.0

    highest_discharge_current = 0.0

    highest_charge_current = 0.0


    # --------------------------------------------------------
    # LATEST VALUES
    # --------------------------------------------------------

    latest_voltage = 0.0

    latest_current = 0.0

    latest_mode = "Idle"

    latest_pack_ocv = 0.0

    latest_group_voltages = []


    # ========================================================
    # MAIN SIMULATION LOOP
    # ========================================================

    for time in range(
        0,
        simulation_time + 1,
        dt
    ):

        # ----------------------------------------------------
        # DRIVING CYCLE
        # ----------------------------------------------------

        current, driving_mode = (
            get_current_and_mode(time)
        )

        current *= load_multiplier


        # ----------------------------------------------------
        # OVERCURRENT FAULT
        # ----------------------------------------------------

        if (
            fault_mode == "overcurrent_fault"
            and 120 <= time <= 180
        ):

            current = 45.0


        # ----------------------------------------------------
        # SOC - COULOMB COUNTING
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
        # OPEN CIRCUIT VOLTAGE
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
        # THERMAL FAULT
        # ----------------------------------------------------

        if (
            fault_mode == "thermal_fault"
            and time >= 500
        ):

            temperature = max(
                temperature,
                55.0
            )


        # ----------------------------------------------------
        # CELL GROUP VOLTAGES
        # ----------------------------------------------------

        group_voltages = []

        base_group_voltage = (
            terminal_voltage
            / series_groups
        )

        for i in range(series_groups):

            normal_variation = (
                (i % 3 - 1)
                * 0.006
            )

            group_voltage = (
                base_group_voltage
                + normal_variation
            )

            # Group 5 slightly weaker
            if i == 4:

                group_voltage -= 0.04

            # Manual cell fault
            if (
                fault_mode == "cell_fault"
                and i == 4
            ):

                group_voltage -= 0.18

            group_voltages.append(
                group_voltage
            )


        # ----------------------------------------------------
        # ENERGY CALCULATION
        # ----------------------------------------------------

        power_w = (
            terminal_voltage
            * current
        )

        if current >= 0:

            consumed_energy_wh += (
                max(power_w, 0)
                * dt
                / 3600.0
            )

        else:

            regen_energy_wh += (
                abs(power_w)
                * dt
                / 3600.0
            )


        # ----------------------------------------------------
        # STORE DATA
        # ----------------------------------------------------

        times.append(time)

        soc_values.append(soc)

        soh_values.append(soh)

        voltage_values.append(
            terminal_voltage
        )

        current_values.append(
            current
        )

        temperature_values.append(
            temperature
        )

        rul_values.append(
            rul_cycles
        )

        driving_modes.append(
            driving_mode
        )

        consumed_energy_values.append(
            consumed_energy_wh
        )

        regen_energy_values.append(
            regen_energy_wh
        )

        group_voltage_history.append(
            group_voltages
        )


        # ----------------------------------------------------
        # TRACK PEAKS
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
        # LATEST VALUES
        # ----------------------------------------------------

        latest_voltage = (
            terminal_voltage
        )

        latest_current = current

        latest_mode = driving_mode

        latest_pack_ocv = pack_ocv

        latest_group_voltages = (
            group_voltages
        )


    # ========================================================
    # CELL IMBALANCE
    # ========================================================

    highest_group_voltage = max(
        latest_group_voltages
    )

    lowest_group_voltage = min(
        latest_group_voltages
    )

    voltage_imbalance = (
        highest_group_voltage
        - lowest_group_voltage
    )

    weak_group = (
        latest_group_voltages.index(
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
    # FAULT ANALYSIS
    # ========================================================

    fault_cards = []


    def add_fault(
        title,
        severity,
        detail,
        action
    ):

        fault_cards.append({

            "title": title,

            "severity": severity,

            "detail": detail,

            "action": action
        })


    # --------------------------------------------------------
    # VOLTAGE
    # --------------------------------------------------------

    if highest_voltage > 50.4:

        add_fault(
            "Over-Voltage",
            "warning",
            "Pack voltage exceeded the configured maximum.",
            "Reduce charging or regenerative current."
        )


    if lowest_voltage < 36.0:

        add_fault(
            "Under-Voltage",
            "critical",
            "Pack voltage dropped below the safe operating limit.",
            "Reduce load and recharge the battery."
        )


    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    if highest_temperature >= 60:

        add_fault(
            "Critical Over-Temperature",
            "critical",
            "Battery temperature exceeded 60°C.",
            "Stop operation and activate thermal protection."
        )

    elif highest_temperature >= 50:

        add_fault(
            "High Battery Temperature",
            "warning",
            "Battery temperature exceeded the warning threshold.",
            "Reduce load and improve cooling."
        )


    # --------------------------------------------------------
    # CURRENT
    # --------------------------------------------------------

    if highest_discharge_current > 30:

        add_fault(
            "Excessive Discharge Current",
            "warning",
            "Discharge current exceeded the configured BMS limit.",
            "Reduce acceleration or motor load."
        )


    if highest_charge_current < -20:

        add_fault(
            "Excessive Charging Current",
            "warning",
            "Regenerative charging current exceeded the limit.",
            "Reduce regenerative braking intensity."
        )


    # --------------------------------------------------------
    # CELL IMBALANCE
    # --------------------------------------------------------

    if voltage_imbalance > 0.10:

        add_fault(
            "Cell Imbalance",
            "warning",
            f"Group {weak_group} has the lowest voltage.",
            "Inspect the weak group and perform cell balancing."
        )


    # --------------------------------------------------------
    # BATTERY HEALTH
    # --------------------------------------------------------

    if soh <= 80:

        add_fault(
            "Low Battery Health",
            "warning",
            f"Battery SOH has fallen to {soh:.1f}%.",
            "Plan battery service or replacement."
        )


    # --------------------------------------------------------
    # SIMULATED FAULTS
    # --------------------------------------------------------

    if fault_mode == "thermal_fault":

        add_fault(
            "Injected Thermal Fault",
            "warning",
            "A thermal fault was deliberately injected for testing.",
            "Use this scenario to demonstrate BMS fault detection."
        )


    if fault_mode == "cell_fault":

        add_fault(
            "Injected Weak Cell Fault",
            "warning",
            "Group 5 was deliberately degraded.",
            "Observe imbalance detection and weak-group identification."
        )


    if fault_mode == "overcurrent_fault":

        add_fault(
            "Injected Overcurrent Fault",
            "warning",
            "A 45 A load was deliberately applied.",
            "Observe BMS overcurrent protection."
        )


    # ========================================================
    # BATTERY STATUS
    # ========================================================

    status = "NORMAL"

    if fault_cards:

        status = "WARNING"


    if any(
        fault["severity"] == "critical"
        for fault in fault_cards
    ):

        status = "CRITICAL"


    # ========================================================
    # REGENERATION EFFICIENCY INDICATOR
    # ========================================================

    if consumed_energy_wh > 0:

        regen_ratio = (
            regen_energy_wh
            / consumed_energy_wh
            * 100
        )

    else:

        regen_ratio = 0.0


    # ========================================================
    # DASHBOARD RESULT
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

        "weak_group":
            weak_group,

        "cell_imbalance":
            voltage_imbalance,

        "cell_status":
            cell_status,

        "driving_condition":
            latest_mode,

        "effective_capacity":
            effective_capacity_ah,

        "peak_temperature":
            highest_temperature,

        "peak_current":
            highest_discharge_current,

        "pack_ocv":
            latest_pack_ocv,

        "energy_consumed":
            consumed_energy_wh,

        "regen_energy":
            regen_energy_wh,

        "regen_ratio":
            regen_ratio
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
            driving_modes,

        "energy_consumed":
            consumed_energy_values,

        "regen_energy":
            regen_energy_values,

        "group_voltages":
            group_voltage_history
    }


    return (
        battery,
        graph,
        latest_group_voltages,
        fault_cards
    )


# ============================================================
# MAIN ROUTE
# ============================================================


def simulate_charging(initial_soc=20, target_soc=90, charging_current=6,
                      ambient_temperature=25, aging_cycles=0):
    """Illustrative 12S4P charging model; taper/thermal coefficients are assumptions."""
    import math
    def number(value, default, low, high):
        value = safe_float(value, default)
        return clamp(value if math.isfinite(value) else default, low, high)
    soc = number(initial_soc, 20, 0, 100)
    start_soc = soc
    target = number(target_soc, 90, 0, 100)
    requested_current = number(charging_current, 6, 0.5, 12)
    ambient = number(ambient_temperature, 25, -10, 60)
    aging = number(aging_cycles, 0, 0, 1500)
    soh = clamp(100 - aging * 0.02, 60, 100)
    capacity = 12 * soh / 100
    resistance = 0.03 * (1 + (100 - soh) * 0.015)
    temperature = ambient
    peak_temperature = ambient
    energy = elapsed = 0.0
    current = 0.0
    phase = "Ready to charge"
    reason = "Target reached"
    faults = []
    graph = {key: [] for key in ['time', 'soc', 'soh', 'voltage', 'current',
             'temperature', 'rul', 'driving_mode', 'energy_consumed', 'regen_energy',
             'group_voltages']}
    def record():
        voltage = min(50.4, cell_ocv_from_soc(soc)*12 + current*resistance)
        groups = [voltage/12 + (i % 3 - 1)*0.006 - (0.04 if i == 4 else 0)
                  for i in range(12)]
        values = [elapsed, soc, soh, voltage, -current, temperature,
                  max(0, (soh-80)/0.02), phase, energy, 0.0, groups]
        for key, value in zip(graph, values): graph[key].append(value)
    record()
    if target <= start_soc:
        reason = "Starting SOC already meets or exceeds target"
        phase = "No charging needed"
    elif not 0 <= ambient < 45:
        reason = "Charging blocked by temperature limit"
        phase = "Temperature protection"
        faults.append(dict(title="Charging temperature limit", severity="warning",
                           detail="This model permits charging from 0°C to below 45°C.",
                           action="Choose an ambient temperature within the model's range."))
    else:
        while soc < target - 1e-9 and elapsed < 24*3600:
            if temperature >= 45:
                reason = "Stopped at temperature limit"
                phase = "Temperature protection"
                faults.append(dict(title="Charging stopped", severity="warning",
                                   detail="The modeled pack reached 45°C before the target SOC.",
                                   action="Try a lower charging current or ambient temperature."))
                break
            # Approximate constant-current bulk phase and high-SOC taper.
            taper = 1 if soc < 80 else max(0.1, (100-soc)/20)
            current = requested_current * taper
            phase = "Constant current" if soc < 80 else "Taper charging"
            seconds_to_target = (target-soc)/100*capacity*3600/(current*0.95)
            step = min(30.0, seconds_to_target, 24*3600-elapsed)
            voltage = min(50.4, cell_ocv_from_soc(soc)*12 + current*resistance)
            # Lumped thermal balance: 1000 J/K heat capacity and 2 W/K cooling.
            equilibrium = ambient + current*current*resistance/2.0
            next_temperature = equilibrium + (temperature-equilibrium)*math.exp(-step/500)
            # Land on the thermal cutoff rather than overshooting it.
            cutoff = next_temperature >= 45 and equilibrium > 45
            if cutoff:
                step = -500*math.log((45-equilibrium)/(temperature-equilibrium))
                next_temperature = 45.0
            soc = min(target, soc + current*0.95*step/3600/capacity*100)
            energy += voltage*current*step/3600
            elapsed += step
            temperature = next_temperature
            peak_temperature = max(peak_temperature, temperature)
            record()
        if elapsed >= 24*3600 and soc < target-1e-9:
            reason = "Stopped at 24-hour simulation limit"
            phase = "Time limit"
            faults.append(dict(title="Simulation time limit", severity="warning",
                               detail="The target was not reached within 24 simulated hours.",
                               action="Choose a higher charging current or a lower target."))
    current = 0.0
    if soc >= target and target > start_soc: phase = "Charging complete"
    record()
    groups=graph['group_voltages'][-1]
    battery=dict(soc=soc, soh=soh, voltage=graph['voltage'][-1], current=0,
                 temperature=temperature, rul=max(0,(soh-80)/0.02),
                 status='WARNING' if faults else 'NORMAL', weak_group=5,
                 cell_imbalance=max(groups)-min(groups), cell_status='BALANCED',
                 driving_condition=phase, effective_capacity=capacity,
                 peak_temperature=peak_temperature, peak_current=requested_current,
                 pack_ocv=cell_ocv_from_soc(soc)*12, energy_consumed=energy,
                 regen_energy=0, regen_ratio=0)
    summary=dict(minutes=elapsed/60, target=target, start_soc=start_soc,
                 reached=soc>=target, reason=reason, energy_wh=energy,
                 peak_temperature=peak_temperature)
    # Limit rendered points while retaining start, finish, and cutoff state.
    if len(graph['time']) > 360:
        indices=sorted(set(range(0,len(graph['time']),math.ceil(len(graph['time'])/359)))
                       | {len(graph['time'])-1})
        graph={key:[values[i] for i in indices] for key,values in graph.items()}
    return battery,graph,groups,faults,summary


@app.route('/charging', methods=['GET', 'POST'])
def charging():
    import math
    def value(name, default, low, high):
        parsed=safe_float(request.form.get(name),default)
        return clamp(parsed if math.isfinite(parsed) else default,low,high)
    controls=dict(initial_soc=value('initial_soc',20,0,100),
                  target_soc=value('target_soc',90,0,100),
                  charging_current=value('charging_current',6,0.5,12),
                  ambient_temperature=value('ambient_temperature',25,-10,60),
                  aging_cycles=int(value('aging_cycles',0,0,1500)),
                  load_multiplier=1, fault_mode='none')
    battery,graph,groups,fault_cards,summary=simulate_charging(**{
        key:controls[key] for key in ['initial_soc','target_soc','charging_current',
                                     'ambient_temperature','aging_cycles']})
    return render_template('index.html',battery=battery,graph=graph,groups=groups,
                           fault_cards=fault_cards,controls=controls,animate=False,
                           charging_mode=True,charging_summary=summary)


@app.route(
    "/",
    methods=[
        "GET",
        "POST"
    ]
)
def home():

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


    # --------------------------------------------------------
    # INPUT LIMITS
    # --------------------------------------------------------

    initial_soc = clamp(
        initial_soc,
        10,
        100
    )

    load_multiplier = clamp(
        load_multiplier,
        0.5,
        2.0
    )

    ambient_temperature = clamp(
        ambient_temperature,
        -10,
        60
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


    # --------------------------------------------------------
    # RUN DIGITAL TWIN
    # --------------------------------------------------------

    (
        battery,
        graph,
        groups,
        fault_cards
    ) = simulate_battery(

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

        battery=
            battery,

        graph=
            graph,

        groups=
            groups,

        controls=
            controls,

        fault_cards=
            fault_cards,

        animate=
            request.method == "POST"
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