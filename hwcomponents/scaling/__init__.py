from hwcomponents.scaling.scalefuncs import *
from hwcomponents.scaling.techscaling import (
    tech_node_area,
    tech_node_energy,
    tech_node_latency,
    tech_node_leak,
)

__all__ = [
    # From scalefuncs
    "linear",
    "reciprocal",
    "pow_base",
    "quadratic",
    "nlog_base",
    "nlog2n",
    "cacti_depth_energy",
    "cacti_depth_area",
    "cacti_depth_leak",
    "noscale",
    # From techscaling
    "tech_node_area",
    "tech_node_energy",
    "tech_node_latency",
    "tech_node_leak",
]
