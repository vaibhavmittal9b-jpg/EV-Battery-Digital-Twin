from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)


@app.route("/")
def home():

    try:
        df = pd.read_csv("data/battery_data.csv")

        latest = df.iloc[-1]

        battery_data = {
            "soc": round(latest["SOC"], 2),
            "soh": round(latest["SOH"], 2),
            "voltage": round(latest["Voltage"], 2),
            "current": round(latest["Current"], 2),
            "temperature": round(latest["Temperature"], 2),
            "status": latest["Battery_Status"],
            "faults": latest["Faults"],
            "weak_group": int(latest["Weak_Group"]),
            "cell_imbalance": round(
                latest["Cell_Imbalance"],
                3
            ),
            "rul": round(
                latest["RUL_Cycles"]
            )
        }

        return render_template(
            "index.html",
            battery=battery_data
        )

    except Exception as error:

        return f"Error loading battery data: {error}"


if __name__ == "__main__":
    app.run(debug=True)