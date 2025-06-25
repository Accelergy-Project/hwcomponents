from abc import ABC, abstractmethod
from numbers import Number
from typing import Callable, List, Union
import warnings
from hwcomponents.logging import ListLoggable
from hwcomponents.util import parse_float


def actionDynamicEnergy(func: Callable) -> Callable:
    """
    Decorator that adds an action to an energy/area estimator. Actions are
    expected to return an energy value in Juoles or an Estimation object with
    the energy and units.
    """

    def wrapper(self: "EnergyAreaEstimator", *args, **kwargs):
        return func(self, *args, **kwargs) * self.energy_scale

    wrapper._is_component_energy_action = True
    wrapper._original_function = func
    return wrapper


class EnergyAreaEstimator(ListLoggable, ABC):
    """
    EnergyAreaEstimator base class. EnergyAreaEstimator class must have "name"
    attribute, "percent_accuracy_0_to_100" attribute, and "get_area" method.
    EnergyAreaEstimators may have any number of methods that are decorated with
    @actionDynamicEnergy.
    """

    component_name: Union[str, List[str]] = None
    percent_accuracy_0_to_100: Number = None

    @abstractmethod
    def __init__(self, leak_power: float, area: float):
        super().__init__()
        self.energy_scale = 1
        self.area_scale = 1
        self.leak_scale = 1
        self._leak_power = leak_power
        self._area = area

    @property
    def leak_power(self) -> Number:
        """Returns the leakage power of the component in Watts."""
        return self._leak_power * self.leak_scale

    @property
    def area(self) -> Number:
        """Returns the area in m^2 of the component."""
        return self._area * self.area_scale

    @actionDynamicEnergy
    def leak(self, time_period: float) -> Number:
        """Returns the energy leakage of the component over a given time period in Joules."""
        return self.leak_power * time_period

    def scale(
        self,
        key: str,
        target: float,
        default: float,
        energy_scale_function: Callable[[float, float], float],
        area_scale_function: Callable[[float, float], float],
        leak_scale_function: Callable[[float, float], float],
    ) -> float:
        super()._init_logger(f"{self.__class__.component_name}")
        if target == default:
            return target

        for attr, callfunc in [
            ("energy_scale", energy_scale_function),
            ("area_scale", area_scale_function),
            ("leak_scale", leak_scale_function),
        ]:
            try:
                prev_val = getattr(self, attr)
                scale = callfunc(target, default)
                setattr(self, attr, prev_val * scale)
                self.logger.info(
                    f"Scaled {key} from {default} to {target}: {attr} multiplied by {scale}"
                )
            except:
                target_float = parse_float(
                    target, f"{self.__class__.component_name}.{key}"
                )
                default_float = parse_float(
                    default, f"{self.__class__.component_name}.{key}"
                )
                scale = callfunc(target_float, default_float)
                setattr(self, attr, prev_val * scale)
                self.log.append(
                    f"Scaled {key} from {default} to {target}: {attr} multiplied by {scale}"
                )

        return target
