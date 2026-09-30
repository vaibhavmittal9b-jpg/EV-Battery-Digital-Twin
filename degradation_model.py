class DegradationModel:
    def __init__(self, nominal_capacity_ah):
        self.nominal_capacity_ah = nominal_capacity_ah

        # Total charge moved through the battery
        self.cumulative_ah = 0.0

        # Equivalent Full Cycles
        self.equivalent_cycles = 0.0

        # Battery State of Health
        self.soh = 100.0

        # Capacity fade per equivalent full cycle
        self.degradation_per_cycle = 0.02   # % per cycle


    def update(self, current, dt):
        """
        Update battery degradation.

        current = battery current in A
        dt = simulation timestep in seconds
        """

        # Ah throughput during this timestep
        ah_throughput = abs(current) * dt / 3600

        self.cumulative_ah += ah_throughput

        # Equivalent Full Cycle:
        # one full charge + discharge ≈ 2 × battery capacity
        self.equivalent_cycles = (
            self.cumulative_ah
            / (2 * self.nominal_capacity_ah)
        )

        # Estimate SOH from cycle aging
        capacity_loss = (
            self.equivalent_cycles
            * self.degradation_per_cycle
        )

        self.soh = 100.0 - capacity_loss

        # Prevent unrealistic values
        self.soh = max(60.0, self.soh)

        return self.soh