class RULModel:

    def __init__(self):

        # Battery end-of-life threshold
        self.end_of_life_soh = 80.0

        # Must match degradation model
        self.degradation_per_cycle = 0.02


    def predict_cycles_remaining(self, soh):

        """
        Estimate remaining equivalent full cycles
        before battery reaches end-of-life SOH.
        """

        if soh <= self.end_of_life_soh:
            return 0

        remaining_soh = (
            soh - self.end_of_life_soh
        )

        remaining_cycles = (
            remaining_soh /
            self.degradation_per_cycle
        )

        return remaining_cycles