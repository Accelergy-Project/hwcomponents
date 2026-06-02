from hwcomponents import ComponentModel, action, ActionCost
from hwcomponents.scaling import (
    tech_node_area,
    tech_node_energy,
    tech_node_latency,
    tech_node_leak,
    tech_node_throughput,
    noscale,
)


class TernaryMAC(ComponentModel):
    """

    A ternary MAC unit, which multiplies two ternary values and accumulates the result.

    Parameters
    ----------
    accum_n_bits : int
        The width of the accumulator in bits.
    tech_node : int
        The technology node in meters.

    Attributes
    ----------
    accum_n_bits : int
        The width of the accumulator in bits.
    tech_node : int
        The technology node in meters.
    """

    component_name: str | list[str] = "TernaryMAC"
    """ Name of the component. Must be a string or list/tuple of strings. """

    priority = 0.3
    """
    Priority determines which model is used when multiple models are available for a
    given component. Higher priority models are used first. Must be a number between 0
    and 1.
    """

    def __init__(self, accum_n_bits: int, tech_node: float):
        # Provide an area and leakage power for the component. All units are in
        # standard units without any prefixes (Joules, Watts, meters, etc.).
        super().__init__(area=5e-12 * accum_n_bits, leak_power=1e-3 * accum_n_bits)

        # Scale to the target tech_node from 40nm. The scaling functions are defined in
        # hwcomponents.scaling. Each *_scale_function affects the corresponding cost
        # returned by @action methods.
        self.tech_node = self.scale(
            "tech_node",
            tech_node,
            40e-9,
            area_scale_function=tech_node_area,
            energy_scale_function=tech_node_energy,
            latency_scale_function=tech_node_latency,
            leak_power_scale_function=tech_node_leak,
            throughput_scale_function=tech_node_throughput,
        )
        self.accum_n_bits = accum_n_bits

        # Raising an error says that this model can't estimate and other models instead
        # should be used instead. Good error messages are essential for users debugging
        # their designs.
        assert (
            4 <= accum_n_bits <= 8
        ), f"Accumulation number of bits {accum_n_bits} outside supported range [4, 8]"

    # The action decorator makes this function visible as an action. The function should
    # return an ActionCost with energy (J), throughput (actions/s), and latency (s).
    @action
    def mac(self, clock_gated: bool = False):
        """
        Returns the cost of one ternary MAC operation.

        Parameters
        ----------
        clock_gated : bool
            Whether the MAC is clock gated during this operation.

        Returns
        -------
        ActionCost
            The cost of this action.
        """

        self.logger.info("TernaryMAC Model is modeling cost for mac.")
        if clock_gated:
            return ActionCost(energy=0.0, throughput=1 / 1e-9, latency=1e-9)
        # 2fJ, 1GHz, 1ns
        return ActionCost(
            energy=2e-15 * (self.accum_n_bits + 0.25),
            throughput=1 / 1e-9,
            latency=1e-9,
        )
