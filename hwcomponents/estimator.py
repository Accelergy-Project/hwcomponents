from abc import ABC, abstractmethod
from numbers import Number
from typing import Callable, List, Union
import warnings
from hwcomponents.logging import ListLoggable


def actionDynamicEnergy(func: Callable) -> Callable:
    """
    Decorator that adds an action to an energy/area estimator. Actions are
    expected to return an energy value in Juoles or an Estimation object with
    the energy and units.
    """
    func._is_component_energy_action = True
    return func


class EnergyAreaEstimator(ListLoggable, ABC):
    """
    EnergyAreaEstimator base class. EnergyAreaEstimator class must have "name"
    attribute, "percent_accuracy_0_to_100" attribute, and "get_area" method.
    EnergyAreaEstimators may have any number of methods that are decorated with
    @.
    """

    component_name: Union[str, List[str]] = None
    percent_accuracy_0_to_100: Number = None

    def __init__(self, name: str = None):
        cls = self.__class__
        if cls.component_name is None and getattr(cls, "name", None) is not None:
            cls.component_name = cls.name
            warnings.warn(
                "EnergyAreaEstimator.name is deprecated and will be removed in a future version. "
                "Use EnergyAreaEstimator.component_name instead.",
                DeprecationWarning,
                stacklevel=2
            )
        super().__init__(name=name)

    @abstractmethod
    def get_area(self) -> Number:
        """Returns the area in m^2 or an Estimation object with the area and
        units."""
        pass

    @abstractmethod
    def leak(self, global_cycle_seconds: float) -> Number:
        """Returns the leakage energy per global cycle or an Estimation object
        with the leakage energy and units."""
        pass
class Estimator(EnergyAreaEstimator):
    pass # An override of EnergyAreaEstimator.