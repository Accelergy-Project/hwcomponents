from hwcomponents import ComponentModel, action
from hwcomponents.scaling import tech_node_area, tech_node_energy, tech_node_leak, noscale


class TernaryMAC(ComponentModel):
    """

    A ternary MAC unit, which multiplies two ternary values and accumulates the result.

    Parameters
    ----------
    accum_datawidth : int
        The width of the accumulator in bits.
    tech_node : int
        The technology node in meters.

    Attributes
    ----------
    accum_datawidth : int
        The width of the accumulator in bits.
    tech_node : int
        The technology node in meters.
    """

    component_name: str | list[str] = 'TernaryMAC'
    """ Name of the component. Must be a string or list/tuple of strings. """

    priority = 0.3
    """
    Priority determines which model is used when multiple models are available for a
    given component. Higher priority models are used first. Must be a number between 0
    and 1.
    """

    def __init__(self, accum_datawidth: int, tech_node: int):
        # Provide an area and leakage power for the component. All units are in
        # standard units without any prefixes (Joules, Watts, meters, etc.).
        super().__init__(
            area=5e-12 * accum_datawidth,
            leak_power=1e-3 * accum_datawidth
        )

        # The following scales the tech_node to the given tech_node node from 40nm.
        # The scaling functions for area, energy, and leakage are defined in
        # hwcomponents.scaling. The energy scaling will affect the functions decorated
        # with @action.
        self.tech_node = self.scale(
            "tech_node",
            tech_node,
            40e-9,
            tech_node_area,
            tech_node_energy,
            noscale,
            tech_node_leak,
        )
        self.accum_datawidth = accum_datawidth

        # Raising an error says that this model can't estimate and other models instead
        # should be used instead. Good error messages are essential for users debugging
        # their designs.
        assert 4 <= accum_datawidth <= 8, \
            f'Accumulation datawidth {accum_datawidth} outside supported ' \
            f'range [4, 8]!'

    # The action decorator makes this function visible as an action. The
    # function should return a tuple of (energy, latency).
    @action
    def mac(self, clock_gated: bool = False):
        """
        Returns the energy and latency to perform a ternary MAC operation.

        Parameters
        ----------
        clock_gated : bool
            Whether the MAC is clock gated during this operation.

        Returns
        -------
        (energy, latency)
            The energy in Joules and latency in seconds for a ternary MAC operation.
        """

        self.logger.info(f'TernaryMAC Model is modeling energy and latency for mac.')
        if clock_gated:
            return 0.0, 1e-9
        # .002pJ, 1ns
        return 0.002e-12 * (self.accum_datawidth + 0.25), 1e-9
