import math
from typing import Callable


# =============================================================================
# General scaling functions
# =============================================================================
def linear(target: float, scalefrom: float) -> float:
    """
    Linear scaling function. Returns target / scalefrom.

    Args:
        target: The target value.
        scalefrom: The value to scale from.
    Returns:
        The scaled value.
    """
    return target / scalefrom


def pow_base(power: float) -> Callable[[float, float], float]:
    """
    Power scaling function. Returns a lambda that computes (target - scalefrom) **
    power.

    Args:
        power: The power to scale by.
    Returns:
        A lambda that computes (target - scalefrom) ** power.
    """
    return lambda target, scalefrom: (target - scalefrom) ** power


def quadratic(target: float, scalefrom: float) -> float:
    """Quadratic scaling function. Returns (target / scalefrom) ** 2."""
    return (target / scalefrom) ** 2


def nlog_base(power: float) -> Callable[[float, float], float]:
    """
    Logarithmic scaling function. Returns a lambda that computes (target *
    math.log(target, power)) / (scalefrom * math.log(scalefrom, power)).

    Args:
        power: The power to scale by.
    Returns:
        A lambda that computes (target * math.log(target, power)) / (scalefrom *
        math.log(scalefrom, power)).
    """
    return lambda target, scalefrom: (target * math.log(target, power)) / (
        scalefrom * math.log(scalefrom, power)
    )


def nlog2n(target: float, scalefrom: float) -> float:
    """
    Logarithmic scaling function. Returns (target / scalefrom) * math.log(target /
    scalefrom, 2).
    """
    return (target / scalefrom) * math.log(target / scalefrom, 2)


def cacti_depth_energy(target: float, scalefrom: float) -> float:
    """
    CACTI depth scaling. Based on empirical measurement of CACTI, for which energy
    scales with depth to the power of (1.56 / 2).

    Args:
        target: The target depth.
        scalefrom: The depth to scale from.
    Returns:
        The scaled energy.
    """
    return (target / scalefrom) ** (1.56 / 2)  # Based on CACTI scaling


def cacti_depth_area(target: float, scalefrom: float) -> float:
    """
    CACTI depth scaling. Based on empirical measurement of CACTI, for which area scales
    linearly with depth.

    Args:
        target: The target depth.
        scalefrom: The depth to scale from.
    Returns:
        The scaled area.
    """
    return target / scalefrom  # Based on CACTI scaling


def cacti_depth_leak(target: float, scalefrom: float) -> float:
    """
    CACTI depth scaling. Based on empirical measurement of CACTI, for which leakage
    power scales linearly with depth.

    Args:
        target: The target depth.
        scalefrom: The depth to scale from.
    Returns:
        The scaled leakage power.
    """
    return target / scalefrom  # Based on CACTI scaling


def noscale(target: float, scalefrom: float) -> float:
    return 1
