import math
from typing import Callable


# =============================================================================
# General scaling functions
# =============================================================================
def linear(target: float, scalefrom: float) -> float:
    """
    Linear scaling function. Returns target / scalefrom.

    Parameters
    ----------
    target : float
        The target value.
    scalefrom : float
        The value to scale from.

    Returns
    -------
    float
        The scaled value.
    """
    return target / scalefrom


def reciprocal(target: float, scalefrom: float) -> float:
    """
    Reciprocal scaling function. Returns 1 / (target / scalefrom).

    Parameters
    ----------
    target : float
        The target value.
    scalefrom : float
        The value to scale from.

    Returns
    -------
    float
        The scaled value.
    """
    return 1 / (target / scalefrom)


def pow_base(power: float) -> Callable[[float, float], float]:
    """
    Power scaling function. Returns a lambda that computes power **
    (target - scalefrom). For example, pow_base(2) models exponential
    energy/area scaling with an integer resolution: at target=scalefrom the
    multiplier is 1; at target=scalefrom+1 the multiplier is the base (2).

    Parameters
    ----------
    power : float
        The base to scale by.

    Returns
    -------
    Callable[[float, float], float]
        A lambda that computes power ** (target - scalefrom).
    """
    return lambda target, scalefrom: power ** (target - scalefrom)


def quadratic(target: float, scalefrom: float) -> float:
    """Quadratic scaling function. Returns (target / scalefrom) ** 2."""
    return (target / scalefrom) ** 2


def nlog_base(power: float) -> Callable[[float, float], float]:
    """
    Logarithmic scaling function. Returns a lambda that computes (target *
    math.log(target, power)) / (scalefrom * math.log(scalefrom, power)).

    Parameters
    ----------
    power : float
        The power to scale by.

    Returns
    -------
    Callable[[float, float], float]
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

    Parameters
    ----------
    target : float
        The target depth.
    scalefrom : float
        The depth to scale from.

    Returns
    -------
    float
        The scaled energy.
    """
    return (target / scalefrom) ** (1.56 / 2)  # Based on CACTI scaling


def cacti_depth_area(target: float, scalefrom: float) -> float:
    """
    CACTI depth scaling. Based on empirical measurement of CACTI, for which area scales
    linearly with depth.

    Parameters
    ----------
    target : float
        The target depth.
    scalefrom : float
        The depth to scale from.

    Returns
    -------
    float
        The scaled area.
    """
    return target / scalefrom  # Based on CACTI scaling


def cacti_depth_leak(target: float, scalefrom: float) -> float:
    """
    CACTI depth scaling. Based on empirical measurement of CACTI, for which leakage
    power scales linearly with depth.

    Parameters
    ----------
    target : float
        The target depth.
    scalefrom : float
        The depth to scale from.

    Returns
    -------
    float
        The scaled leakage power.
    """
    return target / scalefrom  # Based on CACTI scaling


def noscale(target: float, scalefrom: float) -> float:
    return 1
