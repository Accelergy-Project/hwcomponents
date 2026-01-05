from abc import ABC, abstractmethod
import inspect
from numbers import Number
from functools import wraps
from typing import Callable, List, Type, Union, TypeVar
from hwcomponents._logging import ListLoggable
from hwcomponents._util import parse_float

T = TypeVar("T", bound="EnergyAreaModel")

def actionDynamicEnergy(
    func: Callable[[], float] = None, bits_per_action: str = None
) -> Callable[[], float]:
    """
    Decorator that adds an action to an energy/area model. If the component has no
    subcomponents, then the action is expected to return an energy value in Joules. If
    the component has subcomponents, then None return values are assumed to be 0, and
    subcomponent actions that occur during the component's action will be added to the
    component's energy. The energy of the subcomponents will NOT be scaled by the
    component's energy_scale.

    Parameters
    ----------
        func : Callable[[], float] | None
            The function to decorate.
        bits_per_action : str
            The attribute of the model that contains the number of bits per action. If
            this is set and a bits_per_action is passed to the function, the energy will
            be scaled by the number of bits. For example, if bits_per_action is set to
            "width", the function is called with bits_per_action=10, and the model has a
            width attribute of 5, then the energy will be scaled by 2.

    Returns
    -------
        The decorated function.
    """
    if func is None:
        return lambda func: actionDynamicEnergy(func, bits_per_action)

    additional_kwargs = set()
    if bits_per_action is not None:
        additional_kwargs.add("bits_per_action")

    @wraps(func)
    def wrapper(self: "EnergyAreaModel", *args, **kwargs):
        for subcomponent in self.subcomponents:
            subcomponent._energy_used = 0
        scale = 1
        if bits_per_action is not None and "bits_per_action" in kwargs:
            nominal_bits = None
            try:
                nominal_bits = getattr(self, bits_per_action)
            except:
                pass
            if nominal_bits is None:
                raise ValueError(
                    f"{self.__name__} has no attribute {bits_per_action}. "
                    f"Ensure that the attributes referenced in actionDynamicEnergy "
                    f"are defined in the class."
                )
            scale = kwargs["bits_per_action"] / nominal_bits
        kwargs = {k: v for k, v in kwargs.items() if k not in additional_kwargs}
        value = func(self, *args, **kwargs)
        if value is None:
            if not self._subcomponents_set and not self.subcomponents:
                raise ValueError(
                    f"actionDynamicEnergy function {func.__name__} did not return a "
                    f"value. This is permitted if and only if the component has no "
                    f"subcomponents. Please either initialize subcomponents or ensure "
                    f"that the actionDynamicEnergy function returns a value."
                )
            value = 0
        value *= self.energy_scale * scale
        for subcomponent in self.subcomponents:
            value += subcomponent._energy_used
        self._energy_used += value
        return value

    wrapper._is_component_energy_action = True
    wrapper._original_function = func
    wrapper._additional_kwargs = additional_kwargs
    return wrapper


class EnergyAreaModel(ListLoggable, ABC):
    """
    EnergyAreaModel base class. EnergyAreaModel class must have "name" attribute,
    "priority" attribute, and "get_area" method. EnergyAreaModels may have any number of
    methods that are decorated with @actionDynamicEnergy.

    Parameters
    ----------
        component_name: str | list[str] | None
            The name of the component. Must be a string or list/tuple of strings. Can be
            omitted if the component name is the same as the class name.
        priority: float
            The priority of the model. Higher priority models are used first. Must be a
            number between 0 and 1.
        leak_power: float | None
            The leakage power of the component in Watts. Must be set if subcomponents is
            not set.
        area: float | None
            The area of the component in m^2. Must be set if subcomponents is not set.
        energy_scale: float
            A scale factor for the energy. All calls to @actionDynamicEnergy will be
            scaled by this factor.
        area_scale: float
            A scale factor for the area. All calls to area will be scaled by this
            factor.
        leak_scale: float
            A scale factor for the leakage power. All calls to leak_power will be scaled
            by this factor.
        subcomponents: list[EnergyAreaModel] | None
            A list of subcomponents. If set, the area and leak power of the
            subcomponents will be added to the area and leak power of the component. All
            calls to @actionDynamicEnergy functions will be added to the energy of the
            component if they occur during one of the component's actions. The area,
            energy, and leak power of subcomponents WILL NOT BE scaled by the
            component's energy_scale, area_scale, or leak_scale; if you want to scale
            the subcomponents, multiply their energy_scale, area_scale, or leak_scale by
            the desired scale factor.

    Attributes
    ----------
        component_name: The name of the component. Must be a string or list/tuple of
            strings. Can be omitted if the component name is the same as the class name.
        priority: The priority of the model. Higher priority models are used first.
            Must be a number between 0 and 1.
        energy_scale: A scale factor for the energy. All calls to actionDynamicEnergy
            will be scaled by this factor.
        area_scale: A scale factor for the area. All calls to area
            will be scaled by this factor.
        leak_scale: A scale factor for the leakage power. All calls to leak_power
            will be scaled by this factor.
        subcomponents: A list of subcomponents. If set, the area and leak power of the
            subcomponents will be added to the area and leak power of the component. All
            calls to @actionDynamicEnergy functions will be added to the energy of the
            component if they occur during one of the component's actions, and will be
            scaled by the component's energy_scale.
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
    def __init__(
            self,
            leak_power: float | None = None,
            area: float | None = None,
            subcomponents: list["EnergyAreaModel"] | None = None,
        ):
        if subcomponents is None:
            if leak_power is None or area is None:
                raise ValueError(
                    f"Either subcomponents must be set, or BOTH leak_power and area"
                    f"must be set."
                )
        super().__init__()
        self.energy_scale: float = 1
        self.area_scale: float = 1
        self.leak_scale: float = 1
        self._leak_power: float = leak_power if leak_power is not None else 0
        self._area: float = area if area is not None else 0
        self.subcomponents: list["EnergyAreaModel"] = [] if subcomponents is None else subcomponents
        self._subcomponents_set = subcomponents is not None
        self._energy_used: float = 0

    @property
    def leak_power(self) -> Number:
        """
        Returns the leakage power of the component in Watts.

        Returns
        -------
            The leakage power in Watts.
        """
        return self._leak_power * self.leak_scale + sum(
            s.leak_power for s in self.subcomponents
        )

    @property
    def area(self) -> Number:
        """
        Returns the area in m^2 of the component.

        Returns
        -------
            The area in m^2 of the component.
        """
        return self._area * self.area_scale + sum(
            s.area for s in self.subcomponents
        )

    @classmethod
    def _component_name(cls) -> str:
        if cls.component_name is None:
            return cls.__name__
        return cls.component_name

    def leak(self, time_period: float) -> float:
        """
        Returns the leakage energy for a given time period.

        Parameters
        ----------
            time_period : float
                The time period in seconds.

        Returns
        -------
            The leakage energy in Joules.
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

    @classmethod
    def get_action_names(cls) -> List[str]:
        """
        Returns the names of the actions supported by the model.

        Returns
        -------
        List[str]
            The names of the actions supported by the model.
        """
        names = set()
        for base in cls.__mro__:
            for name, func in base.__dict__.items():
                if getattr(func, "_is_component_energy_action", False):
                    names.add(name)
        return sorted(names)

    def required_arguments(self, action_name: str | None = None) -> List[str]:
        """
        Returns the required arguments for the given action. If no action is given,
        returns the required arguments for the __init__ method.

        Parameters
        ----------
            action_name : str | None
                The name of the action to get the required arguments for.
                If None, returns the required arguments for the __init__ method.

        Returns
        -------
            list[str]
                The required arguments for the given action.
        """
        action_name = "__init__" if action_name is None else action_name
        try:
            action_func = getattr(self, action_name)
        except:
            raise ValueError(
                f"{self.__class__.__name__} has no action {action_name}. "
                f"Supported actions are: {self.get_action_names()}"
            )
        return inspect.signature(action_func).parameters.keys()

    @classmethod
    def try_init_arbitrary_args(cls: Type[T], **kwargs) -> T:
        """
        Tries to initialize the model with the given arguments.

        Parameters
        ----------
            **kwargs : dict
                The arguments with which to initialize the model.

        Returns
        -------
            The initialized model. If the model cannot be initialized with the given
            arguments, an exception is raised.
        """
        from hwcomponents._model_wrapper import EnergyAreaQuery, EnergyAreaModelWrapper
        wrapper = EnergyAreaModelWrapper(cls, cls.component_name)
        cname = cls.component_name
        query = EnergyAreaQuery(
            component_name=cname if isinstance(cname, str) else cname[0],
            component_attributes=kwargs,
        )
        return wrapper.get_initialized_subclass(query)


    def try_call_arbitrary_action(self: T, action_name: str, **kwargs) -> T:
        """
        Tries to call the given action with the given arguments.

        Parameters
        ----------
            action_name : str
                The name of the action to call.
            **kwargs : dict
                The arguments with which to call the action.
        """
        from hwcomponents._model_wrapper import EnergyAreaQuery, EnergyAreaModelWrapper
        wrapper = EnergyAreaModelWrapper(type(self), self.component_name)
        query = EnergyAreaQuery(
            component_name=self.component_name,
            component_attributes={},
            action_name=action_name,
            action_arguments=kwargs,
        )
        return wrapper.estimate_energy(query, initialized_obj=self)