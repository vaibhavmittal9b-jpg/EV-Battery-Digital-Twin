import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------------------------
# Page configuration
# -------------------------------------------------

st.set_page_config(
    page_title="EV Battery Digital Twin",
    page_icon="🔋",
    layout="wide"
)

# -------------------------------------------------
# Title
# -------------------------------------------------

st.title("🔋 EV Battery Pack Digital Twin")

st.markdown(
    """
    Software-based Digital Twin for monitoring and analysing
    an Electric Vehicle Lithium-ion Battery Pack.
    """
)

# -------------------------------------------------
# Load simulation data
# -------------------------------------------------

try:

    df = pd.read_csv("data/battery_data.csv")

except FileNotFoundError:

    st.error(
        "battery_data.csv not found. "
        "Please run simulation.py first."
    )

    st.stop()


# -------------------------------------------------
# Get latest battery data
# -------------------------------------------------

latest = df.iloc[-1]


# -------------------------------------------------
# Battery overview
# -------------------------------------------------

st.subheader("Battery Pack Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "State of Charge",
        f"{latest['SOC']:.2f} %"
    )


with col2:

    st.metric(
        "State of Health",
        f"{latest['SOH']:.2f} %"
    )


with col3:

    st.metric(
        "Pack Voltage",
        f"{latest['Voltage']:.2f} V"
    )


with col4:

    st.metric(
        "Battery Current",
        f"{latest['Current']:.2f} A"
    )


# -------------------------------------------------
# Second metric row
# -------------------------------------------------

col5, col6, col7, col8 = st.columns(4)


with col5:

    st.metric(
        "Temperature",
        f"{latest['Temperature']:.2f} °C"
    )


with col6:

    if "RUL_Cycles" in df.columns:

        st.metric(
            "Remaining Useful Life",
            f"{latest['RUL_Cycles']:.0f} cycles"
        )


with col7:

    st.metric(
        "Weak Cell Group",
        f"Group {int(latest['Weak_Group'])}"
    )


with col8:

    st.metric(
        "Cell Imbalance",
        f"{latest['Cell_Imbalance']:.3f} V"
    )


# -------------------------------------------------
# Battery Status
# -------------------------------------------------

st.divider()

st.subheader("Battery Status")


battery_status = str(
    latest["Battery_Status"]
)


if battery_status == "NORMAL":

    st.success(
        "Battery Status: NORMAL"
    )

elif battery_status == "WARNING":

    st.warning(
        "Battery Status: WARNING"
    )

else:

    st.error(
        f"Battery Status: {battery_status}"
    )


# -------------------------------------------------
# Fault information
# -------------------------------------------------

fault = str(
    latest["Faults"]
)


if fault != "None":

    st.error(
        f"Detected Fault: {fault}"
    )

else:

    st.success(
        "No pack-level fault detected."
    )


# -------------------------------------------------
# Cell status
# -------------------------------------------------

cell_status = str(
    latest["Cell_Status"]
)


if cell_status == "BALANCED":

    st.success(
        "Cell Groups: BALANCED"
    )

else:

    st.warning(
        f"{cell_status} | "
        f"Weak Group: {int(latest['Weak_Group'])}"
    )


# -------------------------------------------------
# SOC Graph
# -------------------------------------------------

st.divider()

st.subheader("Battery Performance")


fig_soc = px.line(
    df,
    x="Time",
    y="SOC",
    title="State of Charge vs Time"
)

fig_soc.update_layout(
    xaxis_title="Time (seconds)",
    yaxis_title="SOC (%)"
)

st.plotly_chart(
    fig_soc,
    use_container_width=True
)


# -------------------------------------------------
# Voltage Graph
# -------------------------------------------------

fig_voltage = px.line(
    df,
    x="Time",
    y="Voltage",
    title="Battery Pack Voltage vs Time"
)

fig_voltage.update_layout(
    xaxis_title="Time (seconds)",
    yaxis_title="Voltage (V)"
)

st.plotly_chart(
    fig_voltage,
    use_container_width=True
)


# -------------------------------------------------
# Current Graph
# -------------------------------------------------

fig_current = px.line(
    df,
    x="Time",
    y="Current",
    title="Battery Current vs Time"
)

fig_current.update_layout(
    xaxis_title="Time (seconds)",
    yaxis_title="Current (A)"
)

st.plotly_chart(
    fig_current,
    use_container_width=True
)


# -------------------------------------------------
# Temperature Graph
# -------------------------------------------------

fig_temperature = px.line(
    df,
    x="Time",
    y="Temperature",
    title="Battery Temperature vs Time"
)

fig_temperature.update_layout(
    xaxis_title="Time (seconds)",
    yaxis_title="Temperature (°C)"
)

st.plotly_chart(
    fig_temperature,
    use_container_width=True
)


# -------------------------------------------------
# SOH Graph
# -------------------------------------------------

fig_soh = px.line(
    df,
    x="Time",
    y="SOH",
    title="Battery State of Health vs Time"
)

fig_soh.update_layout(
    xaxis_title="Time (seconds)",
    yaxis_title="SOH (%)"
)

st.plotly_chart(
    fig_soh,
    use_container_width=True
)


# -------------------------------------------------
# Cell Group Voltages
# -------------------------------------------------

st.divider()

st.subheader("Cell Group Monitoring")


try:

    voltage_string = str(
        latest["Group_Voltages"]
    )

    group_voltages = [
        float(value.strip())
        for value in voltage_string.split(",")
    ]


    cell_df = pd.DataFrame({

        "Cell Group":
            [
                f"Group {i + 1}"
                for i in range(
                    len(group_voltages)
                )
            ],

        "Voltage":
            group_voltages
    })


    fig_cells = px.bar(
        cell_df,
        x="Cell Group",
        y="Voltage",
        title="Series Group Voltages"
    )


    fig_cells.update_layout(
        yaxis_title="Voltage (V)"
    )


    st.plotly_chart(
        fig_cells,
        use_container_width=True
    )


except Exception:

    st.info(
        "Cell group voltage data is not available."
    )


# -------------------------------------------------
# Driving condition
# -------------------------------------------------

st.divider()

st.subheader("Current Vehicle Operating Condition")


st.info(
    f"Driving Mode: "
    f"{latest['Driving_Condition']}"
)


# -------------------------------------------------
# Data table
# -------------------------------------------------

with st.expander(
    "View Complete Simulation Data"
):

    st.dataframe(
        df,
        use_container_width=True
    )