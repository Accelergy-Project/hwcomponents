import math
from typing import Callable


# =============================================================================
# General scaling functions
# =============================================================================
def linear(target: float, scalefrom: float) -> float:
    return target / scalefrom


def pow_base(power: float) -> Callable[[float, float], float]:
    return lambda target, scalefrom: (target - scalefrom) ** power


def quadratic(target: float, scalefrom: float) -> float:
    return (target / scalefrom) ** 2


def nlog_base(power: float) -> Callable[[float, float], float]:
    return lambda target, scalefrom: (target * math.log(target, power)) / (
        scalefrom * math.log(scalefrom, power)
    )


def nlog2n(target: float, scalefrom: float) -> float:
    return (target / scalefrom) * math.log(target / scalefrom, 2)


def cacti_depth_energy(target: float, scalefrom: float) -> float:
    return (target / scalefrom) ** (1.56 / 2)  # Based on CACTI scaling


def cacti_depth_area(target: float, scalefrom: float) -> float:
    return (target / scalefrom) ** (1.56 / 2)  # Based on CACTI scaling


def cacti_depth_leak(target: float, scalefrom: float) -> float:
    return (target / scalefrom) ** (1.56 / 2)  # Based on CACTI scaling


def noscale(target: float, scalefrom: float) -> float:
    return 1
