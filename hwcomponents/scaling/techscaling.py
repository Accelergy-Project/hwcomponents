# CMOS scaling based on: Aaron Stillmaker, Bevan Baas, Scaling equations for the
# accurate prediction of CMOS device performance from 180nm to 7nm, Integration,
# Volume 58, 2017, Pages 74-81, ISSN 0167-9260,
# https://doi.org/10.1016/j.vlsi.2017.02.002.
# Scaling from tech node X to tech node Y involves multiplying area from
# AREA_SCALING[X][Y].
from math import ceil, floor
from typing import Union


TECH_NODES = [130e-9, 90e-9, 65e-9, 45e-9, 32e-9, 20e-9, 16e-9, 14e-9, 10e-9, 7e-9]
AREA_SCALING = [
    [1, 0.44, 0.23, 0.16, 0.072, 0.033, 0.03, 0.027, 0.016, 0.0092],
    [2.3, 1, 0.53, 0.35, 0.16, 0.075, 0.067, 0.061, 0.036, 0.021],
    [4.3, 1.9, 1, 0.66, 0.31, 0.14, 0.13, 0.12, 0.068, 0.039],
    [6.4, 2.8, 1.5, 1, 0.46, 0.21, 0.19, 0.17, 0.1, 0.059],
    [14, 6.1, 3.3, 2.2, 1, 0.46, 0.41, 0.38, 0.22, 0.13],
    [30, 13, 7.1, 4.7, 2.2, 1, 0.89, 0.82, 0.48, 0.28],
    [34, 15, 7.9, 5.3, 2.4, 1.1, 1, 0.91, 0.54, 0.31],
    [37, 16, 8.7, 5.8, 2.7, 1.2, 1.1, 1, 0.59, 0.34],
    [63, 28, 15, 9.8, 4.5, 2.1, 1.9, 1.7, 1, 0.58],
    [110, 48, 25, 17, 7.8, 3.6, 3.2, 2.9, 1.7, 1],
]

# Scaling from tech node X to tech node Y involves multiplying energy by
# ENERGY_SCALING[Y][0]Vdd^2+ENERGY_SCALING[Y][1]Vdd+ENERGY_SCALING[Y][2] and
# dividing by
# ENERGY_SCALING[X][0]Vdd^2+ENERGY_SCALING[X][1]Vdd+ENERGY_SCALING[X][2]
ENERGY_SCALING = [
    [7.171, -6.709, 2.904],
    [4.762, -4.781, 2.092],
    [3.755, -4.398, 1.975],
    [1.103, -0.362, 0.2767],
    [0.9559, -0.7823, 0.471],
    [0.373, -0.1582, 0.04104],
    [0.2958, -0.1241, 0.03024],
    [0.2363, -0.09675, 0.02239],
    [0.2068, -0.09311, 0.02375],
    [0.1776, -0.09097, 0.02447],
]


def _get_technology_node_index(tech_node: float) -> float:
    """Returns the index of the technology node in the TECH_NODES array.
    Interpolates if necessary."""
    larger_idx, smaller_idx = None, None
    for i, t in enumerate(TECH_NODES):
        if tech_node <= t:
            larger_idx = i
        if tech_node >= t:
            smaller_idx = i
            break

    failed = larger_idx is None or smaller_idx is None

    assert not failed, (
        f"Technology node {tech_node} not supported. Ensure all technology "
        f"nodes are in the range [{TECH_NODES[-1]}, {TECH_NODES[0]}]"
    )
    l_node, s_node = TECH_NODES[larger_idx], TECH_NODES[smaller_idx]
    if larger_idx == smaller_idx:
        return larger_idx
    interp = (tech_node - s_node) / (l_node - s_node)
    return larger_idx + (smaller_idx - larger_idx) * interp


def _constrain_to_tech_nodes(tech_node: float):
    if tech_node < min(TECH_NODES):
        return min(TECH_NODES), tech_node / min(TECH_NODES)
    if tech_node > max(TECH_NODES):
        return max(TECH_NODES), tech_node / max(TECH_NODES)
    return tech_node, 1


def tech_node_area(to_node: float, from_node: float) -> float:
    """
    Returns the scaling factor for area from the technology node
    `from_node` to the technology node `to_node`. Interpolates if necessary.

    Args:
        to_node: The technology node to scale to.
        from_node: The technology node to scale from.
    Returns:
        The scaling factor for area.
    """
    from_node, x = _constrain_to_tech_nodes(from_node)
    to_node, y = _constrain_to_tech_nodes(to_node)
    scale = y / x

    x = _get_technology_node_index(from_node)
    y = _get_technology_node_index(to_node)

    # Any unaccounted for scaling with "scale" variable is assumed to scale
    # linearly with tech node based on IDRS 2016 and 2017 predicted estimated
    # SoC area
    return scale * sum(
        [
            AREA_SCALING[floor(x)][floor(y)] * (1 - x % 1) * (1 - y % 1),
            AREA_SCALING[floor(x)][ceil(y)] * (1 - x % 1) * (y % 1),
            AREA_SCALING[ceil(x)][floor(y)] * (x % 1) * (1 - y % 1),
            AREA_SCALING[ceil(x)][ceil(y)] * (x % 1) * (y % 1),
        ]
    )


def tech_node_energy(
    to_node: float, from_node: float, vdd: Union[float, None] = None
) -> float:
    """Returns the scaling factor for energy from the technology node
    `from_node` to the technology node `to_node`. Interpolates if necessary.

    Args:
        to_node: The technology node to scale to.
        from_node: The technology node to scale from.
        vdd: The voltage to scale by. If not provided, 0.8V is used.
    Returns:
        The scaling factor for energy.
    """
    # Based on IRDS 2022, energy stops scaling after 1nm
    from_node = max(from_node, 1e-9)
    to_node = max(to_node, 1e-9)

    from_node, x = _constrain_to_tech_nodes(from_node)
    to_node, y = _constrain_to_tech_nodes(to_node)
    scale = (y / x) ** 0.5

    x = _get_technology_node_index(from_node)
    y = _get_technology_node_index(to_node)

    if vdd is None:
        vdd = 0.8
    # Outer sum does linear interpolation
    x_e_factor = sum(
        [
            # These sums do aVdd^2 + bVdd + c
            sum(ENERGY_SCALING[floor(x)][i] * vdd ** (2 - i) for i in range(3))
            * (1 - x % 1),
            sum(ENERGY_SCALING[ceil(x)][i] * vdd ** (2 - i) for i in range(3))
            * (x % 1),
        ]
    )
    # Outer sum does linear interpolation
    y_e_factor = sum(
        [
            # These sums do aVdd^2 + bVdd + c
            sum(ENERGY_SCALING[floor(y)][i] * vdd ** (2 - i) for i in range(3))
            * (1 - y % 1),
            sum(ENERGY_SCALING[ceil(y)][i] * vdd ** (2 - i) for i in range(3))
            * (y % 1),
        ]
    )

    # Any unaccounted for scaling with "scale" variable is assumed to scale with
    # square root of tech node based on IDRS 2016 and 2017 predicted estimated
    # fJ/switch
    return y_e_factor / x_e_factor * scale


def tech_node_leak(
    to_node: float, from_node: float, vdd: Union[float, None] = None
) -> float:
    """Returns the scaling factor for leakage power from the technology node
    `from_node` to the technology node `to_node`. Interpolates if necessary.

    Args:
        to_node: The technology node to scale to.
        from_node: The technology node to scale from.
        vdd: The voltage to scale by. If not provided, 0.8V is used.
    Returns:
        The scaling factor for leakage power.
    """
    return tech_node_energy(to_node, from_node, vdd)


def tech_node_latency(to_node: float, from_node: float) -> float:
    """Returns the scaling factor for latency from the technology node
    `from_node` to the technology node `to_node`. Interpolates if necessary.

    Args:
        to_node: The technology node to scale to.
        from_node: The technology node to scale from.
    Returns:
        The scaling factor for latency.
    """
    return to_node / from_node
