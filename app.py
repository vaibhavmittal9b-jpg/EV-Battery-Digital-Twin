from flask import Flask, render_template
import csv
import os

app = Flask(__name__)


def to_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_battery_data():

    file_path = os.path.join(
        app.root_path,
        "data",
        "battery_data.csv"
    )

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError("Battery data file is empty.")

    latest = rows[-1]

    battery = {
        "soc": to_float(latest.get("SOC")),
        "soh": to_float(latest.get("SOH")),
        "voltage": to_float(latest.get("Voltage")),
        "current": to_float(latest.get("Current")),
        "temperature": to_float(
            latest.get("Temperature")
        ),

        "rul": to_float(
            latest.get("RUL_Cycles")
        ),

        "status": latest.get(
            "Battery_Status",
            "UNKNOWN"
        ),

        "faults": latest.get(
            "Faults",
            "None"
        ),

        "weak_group": int(
            to_float(
                latest.get("Weak_Group"),
                0
            )
        ),

        "cell_imbalance": to_float(
            latest.get("Cell_Imbalance")
        ),

        "cell_status": latest.get(
            "Cell_Status",
            "Unknown"
        ),

        "driving_condition": latest.get(
            "Driving_Condition",
            "Unknown"
        )
    }

    # Graph data
    times = [
        to_float(row.get("Time"))
        for row in rows
    ]

    soc_values = [
        to_float(row.get("SOC"))
        for row in rows
    ]

    soh_values = [
        to_float(row.get("SOH"))
        for row in rows
    ]

    voltage_values = [
        to_float(row.get("Voltage"))
        for row in rows
    ]

    current_values = [
        to_float(row.get("Current"))
        for row in rows
    ]

    temperature_values = [
        to_float(row.get("Temperature"))
        for row in rows
    ]

    rul_values = [
        to_float(row.get("RUL_Cycles"))
        for row in rows
    ]

    # Series-group voltages
    group_string = latest.get(
        "Group_Voltages",
        ""
    )

    group_voltages = []

    if group_string:

        for value in group_string.split(","):

            try:
                group_voltages.append(
                    float(value.strip())
                )
            except ValueError:
                pass

    graph_data = {
        "time": times,
        "soc": soc_values,
        "soh": soh_values,
        "voltage": voltage_values,
        "current": current_values,
        "temperature": temperature_values,
        "rul": rul_values
    }

    return battery, graph_data, group_voltages


@app.route("/")
def home():

    try:

        battery, graph_data, groups = (
            load_battery_data()
        )

        return render_template(
            "index.html",
            battery=battery,
            graph=graph_data,
            groups=groups
        )

    except Exception as error:

        return (
            f"<h2>Battery Digital Twin Error</h2>"
            f"<p>{error}</p>"
        )


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )