import config
import numpy as np
from degradation_model import DegradationModel
from rul_model import RULModel

class BatteryModel:

    def __init__(self):

        self.soc = config.INITIAL_SOC
        self.soh = config.INITIAL_SOH
        self.temperature = config.INITIAL_TEMPERATURE

        self.capacity_ah = config.PACK_CAPACITY

        # Equivalent circuit parameters
        self.r0 = config.R0
        self.r1 = config.R1
        self.c1 = config.C1

        # Polarization voltage
        self.v1 = 0.0
        self.degradation = DegradationModel(
    config.PACK_CAPACITY  
)
        self.rul_model = RULModel()


    def calculate_ocv(self):

        """
        Estimate open-circuit voltage from SOC.

        This uses an approximate Li-ion OCV-SOC curve
        instead of a simple linear relationship.
        """

        soc_points = np.array([
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
        ])

        cell_ocv_points = np.array([
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
        ])

        # Find cell OCV corresponding to current SOC
        cell_ocv = np.interp(
            self.soc,
            soc_points,
            cell_ocv_points
        )

        # Convert cell voltage to pack voltage
        pack_ocv = (
            cell_ocv
            * config.SERIES_CELLS
        )

        return pack_ocv


    def update_soc(self, current, dt):

        """
        Update State of Charge using Coulomb Counting.

        Positive current = discharge
        Negative current = charging/regeneration
        """

        discharged_ah = (
            current * dt
        ) / 3600

        soc_change = (
            discharged_ah
            / self.capacity_ah
        ) * 100

        self.soc -= soc_change

        # Keep SOC between 0 and 100%
        self.soc = max(
            0,
            min(
                100,
                self.soc
            )
        )


    def update_polarization_voltage(
        self,
        current,
        dt
    ):

        """
        RC polarization voltage.

        dV1/dt =
        -V1/(R1*C1) + I/C1
        """

        dv1_dt = (
            -(self.v1 / (self.r1 * self.c1))
            + (current / self.c1)
        )

        self.v1 += (
            dv1_dt * dt
        )


    def calculate_terminal_voltage(
        self,
        current
    ):

        ocv = self.calculate_ocv()

        # Instantaneous voltage drop
        ohmic_drop = (
            current * self.r0
        )

        terminal_voltage = (
            ocv
            - ohmic_drop
            - self.v1
        )

        return terminal_voltage


    def update_temperature(
        self,
        current,
        dt
    ):

        """
        Simplified thermal model.

        Heat mainly comes from I²R losses.
        """

        heat_generated = (
            current ** 2
            * self.r0
        )

        heating_effect = (
            heat_generated
            * dt
            * 0.0005
        )

        cooling_effect = (
            self.temperature
            - config.AMBIENT_TEMPERATURE
        ) * 0.01

        self.temperature += (
            heating_effect
            - cooling_effect
        )


    def step(
        self,
        current,
        dt
    ):

        # Update SOC
        self.update_soc(
            current,
            dt
        )

        # Update RC polarization
        self.update_polarization_voltage(
            current,
            dt
        )

        # Update temperature
        self.update_temperature(
            current,
            dt
        )
        self.soh = self.degradation.update(
    current=current,
    dt=dt
)
        rul_cycles = (
    self.rul_model.predict_cycles_remaining(
        self.soh
    )
)

        # Calculate output voltage
        voltage = (
            self.calculate_terminal_voltage(
                current
            )
        )

        return {

            "SOC": self.soc,

            "SOH": self.soh,

            "Voltage": voltage,

            "Current": current,

            "Temperature":
                self.temperature,

            "OCV":
                self.calculate_ocv(),

            "Polarization_Voltage":
                self.v1,
            "RUL_Cycles": rul_cycles
        }