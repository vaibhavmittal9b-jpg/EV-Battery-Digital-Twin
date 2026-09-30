import config


class BMSMonitor:

    def __init__(self):

        # Safety limits for our simulated battery pack
        self.max_voltage = config.PACK_MAX_VOLTAGE
        self.min_voltage = config.PACK_MIN_VOLTAGE

        self.max_temperature = 50.0
        self.warning_temperature = 45.0

        self.minimum_soc = 10.0

        self.max_discharge_current = 30.0
        self.max_charge_current = -20.0


    def check_battery(
        self,
        voltage,
        current,
        temperature,
        soc
    ):

        faults = []

        # -------------------------------
        # Voltage protection
        # -------------------------------

        if voltage > self.max_voltage:

            faults.append(
                "OVER-VOLTAGE"
            )

        elif voltage < self.min_voltage:

            faults.append(
                "UNDER-VOLTAGE"
            )


        # -------------------------------
        # Temperature protection
        # -------------------------------

        if temperature >= self.max_temperature:

            faults.append(
                "CRITICAL OVER-TEMPERATURE"
            )

        elif temperature >= self.warning_temperature:

            faults.append(
                "HIGH TEMPERATURE WARNING"
            )


        # -------------------------------
        # SOC protection
        # -------------------------------

        if soc <= self.minimum_soc:

            faults.append(
                "LOW SOC WARNING"
            )


        # -------------------------------
        # Current protection
        # -------------------------------

        if current > self.max_discharge_current:

            faults.append(
                "EXCESSIVE DISCHARGE CURRENT"
            )


        if current < self.max_charge_current:

            faults.append(
                "EXCESSIVE CHARGING CURRENT"
            )


        # -------------------------------
        # Battery status
        # -------------------------------

        if len(faults) == 0:

            status = "NORMAL"

        elif (
            "CRITICAL OVER-TEMPERATURE" in faults
            or
            "OVER-VOLTAGE" in faults
            or
            "UNDER-VOLTAGE" in faults
        ):

            status = "CRITICAL"

        else:

            status = "WARNING"


        return status, faults