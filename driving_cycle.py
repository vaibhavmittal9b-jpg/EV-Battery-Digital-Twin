def get_current(time):
    """
    Virtual EV driving cycle.

    Positive current  = battery discharging
    Negative current  = regenerative braking / charging
    """

    cycle_time = time % 120

    # Vehicle standing / idle
    if cycle_time < 10:
        return 1.0

    # Strong acceleration
    elif cycle_time < 25:
        return 25.0

    # Normal cruising
    elif cycle_time < 55:
        return 10.0

    # Light acceleration
    elif cycle_time < 70:
        return 18.0

    # Cruising
    elif cycle_time < 90:
        return 8.0

    # Regenerative braking
    elif cycle_time < 100:
        return -12.0

    # Slow city driving
    elif cycle_time < 115:
        return 5.0

    # Vehicle stopped
    else:
        return 0.5