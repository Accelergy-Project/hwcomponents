from abc import ABC, abstractmethod
from numbers import Number
from typing import Callable, List, Union
import warnings
from hwcomponents._logging import ListLoggable
from hwcomponents._util import parse_float


def actionDynamicEnergy(
    func: Callable[[], float] = None, bits_per_action: str = None
) -> Callable[[], float]:
    """
    Decorator that adds an action to an energy/area model. Actions are
    expected to return an energy value in Joules.

    Args:
        func: The function to decorate.
        bits_per_action: The attribute of the model that contains the number of bits per
            action. If this is set and a bits_per_action is passed to the function, the
            energy will be scaled by the number of bits. For example, if bits_per_action
            is set to "width", the function is called with bits_per_action=10, and the
            model has a width attribute of 5, then the energy will be scaled by 2.
    Returns:
        The decorated function.
    """
    if func is None:
        return lambda func: actionDynamicEnergy(func, bits_per_action)

    additional_kwargs = set()
    if bits_per_action is not None:
        additional_kwargs.add("bits_per_action")

    def wrapper(self: "EnergyAreaModel", *args, **kwargs):
        scale = 1
        if bits_per_action is not None and "bits_per_action" in kwargs:
            nominal_bits = None
            try:
                nominal_bits = getattr(self, bits_per_action)
            except:
                pass
            if nominal_bits is None:
                raise ValueError(
                    f"{self.__class__.__name__} has no attribute {bits_per_action}. "
                    f"Ensure that the attributes referenced in actionDynamicEnergy "
                    f"are defined in the class."
                )
            scale = kwargs["bits_per_action"] / nominal_bits
        kwargs = {k: v for k, v in kwargs.items() if k not in additional_kwargs}
        return func(self, *args, **kwargs) * self.energy_scale * scale

    wrapper._is_component_energy_action = True
    wrapper._original_function = func
    wrapper._additional_kwargs = additional_kwargs
    return wrapper


class EnergyAreaModel(ListLoggable, ABC):
    """
    EnergyAreaModel base class. EnergyAreaModel class must have "name"
    attribute, "priority" attribute, and "get_area" method.
    EnergyAreaModels may have any number of methods that are decorated with
    @actionDynamicEnergy.

    Args:
        component_name: The name of the component. Must be a string or list/tuple of
            strings. Can be omitted if the component name is the same as the class name.
        priority: The priority of the model. Higher priority models are used first.
            Must be a number between 0 and 1.
        leak_power: The leakage power of the component in Watts.
        area: The area of the component in m^2.
        energy_scale: A scale factor for the energy.
        area_scale: A scale factor for the area.
        leak_scale: A scale factor for the leakage power.
    """

    component_name: Union[str, List[str], None] = None
    """
    Name of the component. Must be a string or list/tuple of strings. Can be omitted if
    the component name is the same as the class name.
    """

    priority: Number = None
    """
    Priority determines which model is used when multiple models are available for a
    given component. Higher priority models are used first. Must be a number between 0
    and 1.
    """

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

    @classmethod
    def _component_name(cls) -> str:
        if cls.component_name is None:
            return cls.__name__
        return cls.component_name

    def leak(self, time_period: float) -> float:
        """
        Returns the leakage energy for a given time period.
        """
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
        super()._init_logger(f"{self._component_name()}")
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
                    target, f"{self._component_name()}.{key}"
                )
                default_float = parse_float(
                    default, f"{self._component_name()}.{key}"
                )
                scale = callfunc(target_float, default_float)
                setattr(self, attr, prev_val * scale)
                self.logger.info(
                    f"Scaled {key} from {default} to {target}: {attr} multiplied by {scale}"
                )

        return target
