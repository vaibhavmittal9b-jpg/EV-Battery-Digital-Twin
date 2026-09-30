# ============================================
# EV Battery Digital Twin - Configuration
# ============================================

# Cell specifications
CELL_NOMINAL_VOLTAGE = 3.7      # V
CELL_MAX_VOLTAGE = 4.2          # V
CELL_MIN_VOLTAGE = 3.0          # V
CELL_CAPACITY = 3.0             # Ah

# Pack configuration
SERIES_CELLS = 12
PARALLEL_CELLS = 4

# Pack specifications
PACK_NOMINAL_VOLTAGE = CELL_NOMINAL_VOLTAGE * SERIES_CELLS
PACK_MAX_VOLTAGE = CELL_MAX_VOLTAGE * SERIES_CELLS
PACK_MIN_VOLTAGE = CELL_MIN_VOLTAGE * SERIES_CELLS

PACK_CAPACITY = CELL_CAPACITY * PARALLEL_CELLS

PACK_ENERGY = PACK_NOMINAL_VOLTAGE * PACK_CAPACITY

# Initial battery conditions
INITIAL_SOC = 100.0             # %
INITIAL_SOH = 100.0             # %

INITIAL_TEMPERATURE = 25.0      # °C
AMBIENT_TEMPERATURE = 25.0      # °C

# Approximate internal resistance
INTERNAL_RESISTANCE = 0.05      # Ohm

# Equivalent Circuit Model parameters
R0 = 0.03        # Ohm - instantaneous internal resistance
R1 = 0.02        # Ohm - polarization resistance
C1 = 2000        # Farad - polarization capacitance