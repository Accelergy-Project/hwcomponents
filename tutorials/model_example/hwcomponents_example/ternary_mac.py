from hwcomponents import EnergyAreaModel, actionDynamicEnergy
from hwcomponents.scaling import tech_node_area, tech_node_energy, tech_node_leak

class TernaryMAC(EnergyAreaModel):
    # REQUIRED: Give the name of the components supported by this Model.
    component_name: str | list[str] = 'TernaryMAC'
    # REQUIRED: Give the percent accuracy of the Model.
    priority = 0.8

    def __init__(self, accum_datawidth: int, tech_node: int):
        # Provide an area and leakage power for the component. All units are in 
        # standard units without any prefixes (Joules, Watts, meters, etc.).
        super().__init__(
            area=5e-12 * accum_datawidth, 
            leak_power=1e-3 * accum_datawidth
        )

        # The following scales the tech_node to the given tech_node node from 40nm. 
        # The scaling functions for area, energy, and leakage are defined in
        # hwcomponents.scaling. The energy scalingw will affect the functions decorated
        # with @actionDynamicEnergy.
        self.tech_node = self.scale(
            "tech_node",
            tech_node,
            40e-9,
            tech_node_area,
            tech_node_energy,
            tech_node_leak,
        )
        self.accum_datawidth = accum_datawidth

        # Raising an error says that this model can't estimate and other models instead
        # should be used instead. Good error messages are essential for users debugging
        # their designs.
        assert 4 <= accum_datawidth <= 8, \
            f'Accumulation datawidth {accum_datawidth} outside supported ' \
            f'range [4, 8]!'

    # The actionDynamicEnergy decorator makes this function visible as an action. The
    # function should return an energy in Joules.
    @actionDynamicEnergy
    def mac(self, clock_gated: bool = False) -> float:
        self.logger.info(f'TernaryMAC Model is estimating '
                         f'energy for mac_random.')
        if clock_gated:
            return 0.0
        return 0.002e-12 * (self.accum_datawidth + 0.25)
