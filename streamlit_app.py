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
# Custom CSS
# -------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #0f172a;
    color: white;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 30px;
}

[data-testid="stMetric"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 14px;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8;
}

[data-testid="stMetricValue"] {
    font-size: 28px;
}

.status-box {
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    font-size: 22px;
    font-weight: bold;
}

.normal {
    background-color: #064e3b;
    border: 1px solid #10b981;
}

.warning {
    background-color: #78350f;
    border: 1px solid #f59e0b;
}

.critical {
    background-color: #7f1d1d;
    border: 1px solid #ef4444;
}

.section-title {
    font-size: 26px;
    font-weight: bold;
    margin-top: 20px;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# Header
# -------------------------------------------------

st.markdown(
    '<div class="main-title">🔋 EV Battery Pack Digital Twin</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Software-Based Intelligent Monitoring, Fault Detection and '
    'Remaining Useful Life Prediction'
    '</div>',
    unsafe_allow_html=True
)


# -------------------------------------------------
# Load simulation data
# -------------------------------------------------

try:
    df = pd.read_csv("data/battery_data.csv")

except FileNotFoundError:

    st.error(
        "battery_data.csv not found. "
        "Run simulation.py first."
    )

    st.stop()


if df.empty:

    st.error("Battery simulation data is empty.")
    st.stop()


latest = df.iloc[-1]


# -------------------------------------------------
# Battery Overview
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Battery Pack Overview</div>',
    unsafe_allow_html=True
)

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

    else:

        st.metric(
            "Remaining Useful Life",
            "N/A"
        )


with col7:

    if "Weak_Group" in df.columns:

        st.metric(
            "Weak Cell Group",
            f"Group {int(latest['Weak_Group'])}"
        )


with col8:

    if "Cell_Imbalance" in df.columns:

        st.metric(
            "Cell Imbalance",
            f"{latest['Cell_Imbalance']:.3f} V"
        )


# -------------------------------------------------
# Battery Status
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Battery Health Status</div>',
    unsafe_allow_html=True
)

battery_status = str(
    latest.get("Battery_Status", "UNKNOWN")
)


if battery_status == "NORMAL":

    st.markdown(
        '<div class="status-box normal">'
        '✓ BATTERY STATUS: NORMAL'
        '</div>',
        unsafe_allow_html=True
    )

elif battery_status == "WARNING":

    st.markdown(
        '<div class="status-box warning">'
        '⚠ BATTERY STATUS: WARNING'
        '</div>',
        unsafe_allow_html=True
    )

else:

    st.markdown(
        f'<div class="status-box critical">'
        f'🚨 BATTERY STATUS: {battery_status}'
        f'</div>',
        unsafe_allow_html=True
    )


# -------------------------------------------------
# Fault and cell status
# -------------------------------------------------

fault_col1, fault_col2 = st.columns(2)

with fault_col1:

    st.subheader("Pack-Level Faults")

    fault = str(
        latest.get("Faults", "None")
    )

    if fault == "None":

        st.success(
            "No pack-level fault detected."
        )

    else:

        st.error(
            f"Detected Fault: {fault}"
        )


with fault_col2:

    st.subheader("Cell Group Status")

    cell_status = str(
        latest.get(
            "Cell_Status",
            "Unknown"
        )
    )

    if cell_status == "BALANCED":

        st.success(
            "Cell groups are balanced."
        )

    else:

        weak_group = int(
            latest.get(
                "Weak_Group",
                0
            )
        )

        st.warning(
            f"{cell_status} | "
            f"Weak Group: {weak_group}"
        )


# -------------------------------------------------
# Operating condition
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Vehicle Operating Condition</div>',
    unsafe_allow_html=True
)

st.info(
    f"Current Driving Mode: "
    f"{latest['Driving_Condition']}"
)


# -------------------------------------------------
# Graph section
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Battery Performance Analysis</div>',
    unsafe_allow_html=True
)

graph_col1, graph_col2 = st.columns(2)


# SOC Graph
with graph_col1:

    fig_soc = px.line(
        df,
        x="Time",
        y="SOC",
        title="State of Charge vs Time"
    )

    fig_soc.update_layout(
        template="plotly_dark",
        xaxis_title="Time (seconds)",
        yaxis_title="SOC (%)"
    )

    st.plotly_chart(
        fig_soc,
        use_container_width=True
    )


# Voltage Graph
with graph_col2:

    fig_voltage = px.line(
        df,
        x="Time",
        y="Voltage",
        title="Battery Pack Voltage vs Time"
    )

    fig_voltage.update_layout(
        template="plotly_dark",
        xaxis_title="Time (seconds)",
        yaxis_title="Voltage (V)"
    )

    st.plotly_chart(
        fig_voltage,
        use_container_width=True
    )


graph_col3, graph_col4 = st.columns(2)


# Current graph
with graph_col3:

    fig_current = px.line(
        df,
        x="Time",
        y="Current",
        title="Battery Current vs Time"
    )

    fig_current.update_layout(
        template="plotly_dark",
        xaxis_title="Time (seconds)",
        yaxis_title="Current (A)"
    )

    st.plotly_chart(
        fig_current,
        use_container_width=True
    )


# Temperature graph
with graph_col4:

    fig_temperature = px.line(
        df,
        x="Time",
        y="Temperature",
        title="Battery Temperature vs Time"
    )

    fig_temperature.update_layout(
        template="plotly_dark",
        xaxis_title="Time (seconds)",
        yaxis_title="Temperature (°C)"
    )

    st.plotly_chart(
        fig_temperature,
        use_container_width=True
    )


# -------------------------------------------------
# SOH + RUL
# -------------------------------------------------

graph_col5, graph_col6 = st.columns(2)


with graph_col5:

    fig_soh = px.line(
        df,
        x="Time",
        y="SOH",
        title="State of Health vs Time"
    )

    fig_soh.update_layout(
        template="plotly_dark",
        xaxis_title="Time (seconds)",
        yaxis_title="SOH (%)"
    )

    st.plotly_chart(
        fig_soh,
        use_container_width=True
    )


with graph_col6:

    if "RUL_Cycles" in df.columns:

        fig_rul = px.line(
            df,
            x="Time",
            y="RUL_Cycles",
            title="Remaining Useful Life Prediction"
        )

        fig_rul.update_layout(
            template="plotly_dark",
            xaxis_title="Time (seconds)",
            yaxis_title="Remaining Cycles"
        )

        st.plotly_chart(
            fig_rul,
            use_container_width=True
        )


# -------------------------------------------------
# Cell group monitoring
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Cell Group Monitoring</div>',
    unsafe_allow_html=True
)


if "Group_Voltages" in df.columns:

    try:

        voltage_string = str(
            latest["Group_Voltages"]
        )

        group_voltages = [
            float(value.strip())
            for value in voltage_string.split(",")
        ]

        cell_df = pd.DataFrame({
            "Cell Group": [
                f"Group {i + 1}"
                for i in range(
                    len(group_voltages)
                )
            ],

            "Voltage": group_voltages
        })


        fig_cells = px.bar(
            cell_df,
            x="Cell Group",
            y="Voltage",
            title="12-Series Group Voltage Monitoring"
        )

        fig_cells.update_layout(
            template="plotly_dark",
            xaxis_title="Battery Series Group",
            yaxis_title="Voltage (V)"
        )

        st.plotly_chart(
            fig_cells,
            use_container_width=True
        )


        st.dataframe(
            cell_df,
            use_container_width=True,
            hide_index=True
        )


    except Exception as error:

        st.warning(
            f"Unable to display cell voltages: {error}"
        )


# -------------------------------------------------
# Simulation Information
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Digital Twin Information</div>',
    unsafe_allow_html=True
)


info1, info2, info3 = st.columns(3)


with info1:

    st.info(
        """
        **Battery Configuration**

        12S4P Lithium-ion Pack

        48 physical cells represented
        """
    )


with info2:

    st.info(
        """
        **Battery Models**

        SOC estimation

        Equivalent Circuit Model

        Thermal model

        SOH degradation model
        """
    )


with info3:

    st.info(
        """
        **Intelligent Monitoring**

        BMS protection

        Cell imbalance detection

        Weak-group identification

        RUL prediction
        """
    )


# -------------------------------------------------
# Complete Data
# -------------------------------------------------

with st.expander(
    "View Complete Battery Simulation Data"
):

    st.dataframe(
        df,
        use_container_width=True
    )


# -------------------------------------------------
# Footer
# -------------------------------------------------

st.divider()

st.caption(
    "EV Battery Pack Digital Twin | "
    "Software-Based Battery Monitoring and Predictive Analysis"
)