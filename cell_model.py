import config


class CellPackModel:

    def __init__(self):

        self.number_of_groups = config.SERIES_CELLS

        # Slight resistance variation between groups
        self.resistance_factors = [
            1.00,
            1.02,
            0.98,
            1.01,
            1.80,   # Group 5 intentionally weaker
            1.03,
            0.99,
            1.01,
            1.00,
            1.02,
            0.98,
            1.01
        ]

        # We deliberately simulate Group 5 as weak
        self.weak_group_index = 4


    def calculate_group_voltages(
        self,
        pack_ocv,
        current
    ):

        # OCV of one series group
        group_ocv = (
            pack_ocv /
            self.number_of_groups
        )

        # Divide pack resistance between 12 groups
        base_group_resistance = (
            config.R0 /
            self.number_of_groups
        )

        group_voltages = []

        for i in range(self.number_of_groups):

            group_resistance = (
                base_group_resistance
                * self.resistance_factors[i]
            )

            voltage = (
                group_ocv
                - current * group_resistance
            )

            # Simulate slight degradation in Group 5
            if i == self.weak_group_index:
                voltage -= 0.08

            group_voltages.append(voltage)

        return group_voltages


    def analyze_imbalance(
        self,
        group_voltages
    ):

        highest_voltage = max(group_voltages)
        lowest_voltage = min(group_voltages)

        voltage_difference = (
            highest_voltage
            - lowest_voltage
        )

        weak_group = (
            group_voltages.index(lowest_voltage)
            + 1
        )

        # 100 mV imbalance threshold
        if voltage_difference > 0.10:

            status = "CELL IMBALANCE DETECTED"

        else:

            status = "BALANCED"

        return {
            "Highest_Cell_Voltage": highest_voltage,
            "Lowest_Cell_Voltage": lowest_voltage,
            "Voltage_Imbalance": voltage_difference,
            "Weak_Group": weak_group,
            "Cell_Status": status
        }


    def step(
        self,
        pack_ocv,
        current
    ):

        voltages = self.calculate_group_voltages(
            pack_ocv,
            current
        )

        analysis = self.analyze_imbalance(
            voltages
        )

        analysis["Group_Voltages"] = voltages

        return analysis