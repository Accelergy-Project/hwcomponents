from abc import ABC, abstractmethod
import inspect
from numbers import Number
from functools import wraps
from typing import Any, Callable, List, NamedTuple, Type, Union, TypeVar
from hwcomponents._logging import ListLoggable, messages_from_logger, pop_all_messages
from hwcomponents._util import parse_float

T = TypeVar("T", bound="ComponentModel")


class EnergyLatency(NamedTuple):
    energy: float
    latency: float

    def __add__(self, other: "EnergyLatency") -> "EnergyLatency":
        return EnergyLatency(self.energy + other.energy, self.latency + other.latency)


def action(
    func: Callable[..., Union[float, tuple[float, float]]] = None,
    bits_per_action: str = None,
    pipelined_subcomponents: bool = False,
) -> Callable[..., EnergyLatency]:
    """
    Decorator that adds an action to an energy/area model. If the component has no
    subcomponents, then the action is expected to return a tuple of (energy, latency)
    where energy is in Joules and latency is in seconds. If the component has
    subcomponents, then None return values are assumed to be (0, 0), and subcomponent
    actions that occur during the component's action will be added to the component's
    energy and latency. The energy and latency of the subcomponents will NOT be scaled
    by the component's energy_scale and latency_scale; to scale these, set the
    subcomponents' scaling factors directly.

    Parameters
    ----------
        func : Callable | None
            The function to decorate.
        bits_per_action : str
            The attribute of the model that contains the number of bits per action. If
            this is set and a bits_per_action is passed to the function, the energy and
            latency will be scaled by the number of bits. For example, if
            bits_per_action is set to "width", the function is called with
            bits_per_action=10, and the model has a width attribute of 5, then the
            energy and latency will be scaled by 2.
        pipelined_subcomponents : bool
            Whether the subcomponents are pipelined. If True, then the latency of is the
            max of the latency returned and all subcomponent latencies. Otherwise, it is
            the sum. Does nothing if there are no subcomponents.
    Returns
    -------
        The decorated function.
    """
    if func is None:
        return lambda func: action(func, bits_per_action)

    additional_kwargs = set()
    if bits_per_action is not None:
        additional_kwargs.add("bits_per_action")

    @wraps(func)
    def wrapper(self: "ComponentModel", *args, **kwargs):
        was_already_calling_action = getattr(self, "_currently_calling_action", False)
        self._currently_calling_action = True
        try:
            self.logger.info("")
            self.logger.info(
                f"Calling action {self.__class__.__name__}.{func.__name__} with arguments {args} and {kwargs}"
            )
            for subcomponent in self.subcomponents:
                subcomponent._energy_used = 0
                subcomponent._latency_used = 0
            scale = 1
            scalestr = None
            if bits_per_action is not None and "bits_per_action" in kwargs:
                nominal_bits = None
                try:
                    nominal_bits = getattr(self, bits_per_action)
                except:
                    pass
                if nominal_bits is None:
                    raise ValueError(
                        f"{self.__name__} has no attribute {bits_per_action}. "
                        f"Ensure that the attributes referenced in @action "
                        f"are defined in the class."
                    )
                scale = kwargs["bits_per_action"] / nominal_bits
                scalestr = f"Scaling by {kwargs['bits_per_action']=} / {nominal_bits=}"
            kwargs = {k: v for k, v in kwargs.items() if k not in additional_kwargs}
            returned_value = func(self, *args, **kwargs)
            # Normalize return to (energy, latency)
            if returned_value is None:
                if not self._subcomponents_set and not self.subcomponents:
                    raise ValueError(
                        f"@action function {func.__name__} did not return a value. "
                        f"This is permitted if and only if the component has no "
                        f"subcomponents. Please either initialize subcomponents or ensure "
                        f"that the @action function returns a tuple of (energy, latency)."
                    )
                energy_val, latency_val = 0.0, 0.0
            elif isinstance(returned_value, (tuple, list)) and len(returned_value) == 2:
                energy_val, latency_val = returned_value
            else:
                raise ValueError(
                    f"@action function {func.__name__} returned an invalid value. "
                    f"Expected a tuple of (energy, latency), got {returned_value}."
                )

            self.logger.info(
                f"Function {func.__name__} returned energy {energy_val} and latency {latency_val}"
            )
            if scalestr is not None:
                self.logger.info(scalestr)

            if not was_already_calling_action:
                energy_val *= self.energy_scale
                if self.energy_scale != 1:
                    self.logger.info(f"Scaling energy by {self.energy_scale=}")
                for subcomponent in self.subcomponents:
                    self.logger.info(
                        f"Adding subcomponent {subcomponent.__class__.__name__} energy {subcomponent._energy_used}"
                    )
                    energy_val += subcomponent._energy_used
                    subcomponent._energy_used = 0
                energy_val *= scale
                self._energy_used += energy_val

                latency_val *= self.latency_scale
                if self.latency_scale != 1:
                    self.logger.info(f"Scaling latency by {self.latency_scale=}")
                target_func = max if pipelined_subcomponents else sum
                x = "Max" if pipelined_subcomponents else "Summ"
                for subcomponent in self.subcomponents:
                    self.logger.info(
                        f"{x}ing subcomponent {subcomponent.__class__.__name__} latency {subcomponent._latency_used}"
                    )
                    latency_val = target_func((latency_val, subcomponent._latency_used))
                    subcomponent._latency_used = 0
                latency_val *= scale
                self._latency_used += latency_val

                for subcomponent in self.subcomponents:
                    self.logger.info(f"Log for subcomponent {subcomponent.__class__.__name__}:")
                    for message in pop_all_messages(subcomponent.logger):
                        if message:
                            self.logger.info(f"\t{message}")

                self.logger.info(
                    f"** Final return value for {self.__class__.__name__}.{func.__name__}: energy {energy_val} and latency {latency_val}"
                )

            return EnergyLatency(energy_val, latency_val)
        except:
            raise
        finally:
            self._currently_calling_action = False

    wrapper._is_component_action = True
    wrapper._original_function = func
    wrapper._additional_kwargs = additional_kwargs
    return wrapper


class ComponentModel(ListLoggable, ABC):
    """
    ComponentModel base class. ComponentModel class must have "name" attribute,
    "priority" attribute, and "get_area" method. ComponentModels may have any number of
    methods that are decorated with @action.

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
            A scale factor for the energy. All calls to @action will be scaled by this
            factor.
        area_scale: float
            A scale factor for the area. All calls to area will be scaled by this
            factor.
        latency_scale: float
            A scale factor for the latency. All calls to @action will be scaled by this
            factor.
        leak_power_scale: float
            A scale factor for the leakage power. All calls to leak_power will be scaled
            by this factor.
        subcomponents: list[ComponentModel] | None
            A list of subcomponents. If set, the area and leak power of the
            subcomponents will be added to the area and leak power of the component. All
            calls to @action functions will be added to the energy and latency of the
            component if they occur during one of the component's actions. The area,
            energy, latency, and leak power of subcomponents WILL NOT BE scaled by the
            component's energy_scale, area_scale, or leak_power_scale; if you want to
            scale the subcomponents, multiply their energy_scale, area_scale,
            latency_scale, or leak_power_scale by the desired scale factor.

    Attributes
    ----------
        component_name: The name of the component. Must be a string or list/tuple of
            strings. Can be omitted if the component name is the same as the class name.
        priority: The priority of the model. Higher priority models are used first.
            Must be a number between 0 and 1.
        energy_scale: A scale factor for the energy. All calls to action
            will be scaled by this factor.
        area_scale: A scale factor for the area. All calls to area
            will be scaled by this factor.
        latency_scale: A scale factor for the latency. All calls to @action
            will be scaled by this factor.
        leak_power_scale: A scale factor for the leakage power. All calls to leak_power
            will be scaled by this factor.
        subcomponents: A list of subcomponents. If set, the area and leak power of the
            subcomponents will be added to the area and leak power of the component. All
            calls to @action functions will be added to the energy and latency of the
            component if they occur during one of the component's actions. The area,
            energy, latency, and leak power of subcomponents WILL NOT BE scaled by the
            component's energy_scale, area_scale, or leak_power_scale; if you want to
            scale the subcomponents, multiply their energy_scale, area_scale,
            latency_scale, or leak_power_scale by the desired scale factor.
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
        subcomponents: list["ComponentModel"] | None = None,
    ):
        if subcomponents is None:
            if leak_power is None or area is None:
                raise ValueError(
                    f"Either subcomponents must be set, or BOTH leak_power and area"
                    f"must be set."
                )
        super().__init__()
        self.area_scale: float = 1
        self.energy_scale: float = 1
        self.latency_scale: float = 1
        self.leak_power_scale: float = 1
        self._leak_power: float = leak_power if leak_power is not None else 0
        self._area: float = area if area is not None else 0
        self.subcomponents: list["ComponentModel"] = (
            [] if subcomponents is None else subcomponents
        )
        self._subcomponents_set = subcomponents is not None
        self._energy_used: float = 0
        self._latency_used: float = 0

    @property
    def leak_power(self) -> Number:
        """
        Returns the leakage power of the component in Watts.

        Returns
        -------
            The leakage power in Watts.
        """
        return self._leak_power * self.leak_power_scale + sum(
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
        return self._area * self.area_scale + sum(s.area for s in self.subcomponents)

    @classmethod
    def _component_name(cls) -> str:
        if cls.component_name is None:
            return cls.__name__
        return cls.component_name

    def scale(
        self,
        key: str,
        target: float,
        default: float,
        area_scale_function: Callable[[float, float], float] | None = None,
        energy_scale_function: Callable[[float, float], float] | None = None,
        latency_scale_function: Callable[[float, float], float] | None = None,
        leak_power_scale_function: Callable[[float, float], float] | None = None,
    ) -> float:
        """
        Scales this model's area, energy, latency, and leak power to the given target.

        Parameters
        ----------
            key: str
                The name of the parameter to scale. Used for logging.
            target: float
                The target value of the parameter. The value is scaled to this from the
                default.
            default: float
                The default value of the parameter. The value is scaled to the target
                from this.
            area_scale_function: Callable[[float, float], float]
                The function to use to scale the area. None if no scaling should be
                done.
            energy_scale_function: Callable[[float, float], float]
                The function to use to scale the energy. None if no scaling should be
                done.
            latency_scale_function: Callable[[float, float], float]
                The function to use to scale the latency. None if no scaling should be
                done.
            leak_power_scale_function: Callable[[float, float], float]
                The function to use to scale the leak power. None if no scaling should
                be done.
        """
        super()._init_logger(f"{self._component_name()}")
        if target == default:
            return target

        for attr, callfunc in [
            ("area_scale", area_scale_function),
            ("energy_scale", energy_scale_function),
            ("latency_scale", latency_scale_function),
            ("leak_power_scale", leak_power_scale_function),
        ]:
            try:
                if callfunc is None:
                    continue
                prev_val = getattr(self, attr)
                scale = callfunc(target, default)
                setattr(self, attr, prev_val * scale)
                self.logger.info(
                    f"Scaled {key} from {default} to {target}: {attr} multiplied by {scale}"
                )
            except:
                target_float = parse_float(target, f"{self._component_name()}.{key}")
                default_float = parse_float(default, f"{self._component_name()}.{key}")
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
                if getattr(func, "_is_component_action", False):
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
    def try_init_arbitrary_args(
        cls: Type[T], _return_estimation_object: bool = False, **kwargs
    ) -> T:
        """
        Tries to initialize the model with the given arguments.

        Parameters
        ----------
            **kwargs : dict
                The arguments with which to initialize the model.
            _return_estimation_object : bool
                Whether to return the Estimation object instead of the model.
        Returns
        -------
            The initialized model. If the model cannot be initialized with the given
            arguments, an exception is raised.
        """
        from hwcomponents._model_wrapper import ModelQuery, ComponentModelWrapper

        wrapper = ComponentModelWrapper(cls, cls.component_name)
        cname = cls.component_name
        query = ModelQuery(
            component_name=cname if isinstance(cname, str) else cname[0],
            component_attributes=kwargs,
        )
        value = wrapper.get_initialized_subclass(query)
        if _return_estimation_object:
            return value
        return value.value

    def try_call_arbitrary_action(
        self: T, action_name: str, _return_estimation_object: bool = False, **kwargs
    ) -> T:
        """
        Tries to call the given action with the given arguments.

        Parameters
        ----------
            action_name : str
                The name of the action to call.
            **kwargs : dict
                The arguments with which to call the action.
        """
        from hwcomponents._model_wrapper import ModelQuery, ComponentModelWrapper

        wrapper = ComponentModelWrapper(type(self), self.component_name)
        query = ModelQuery(
            component_name=self.component_name,
            component_attributes={},
            action_name=action_name,
            action_arguments=kwargs,
        )
        value = wrapper.get_action_energy_latency(query, initialized_obj=self)
        if _return_estimation_object:
            return value
        return value.value

    def assert_int(self, name: str, value: int | float | Any) -> int:
        """
        Checks that the value is an integer, and if so, returns it as an integer.
        Otherwise, raises a ValueError.

        Parameters
        ----------
            name: str
                The name of the attribute to check. Used for error messages.
            value: int | float | Any
                The value to check.
        Returns
        -------
            int
                The value as an integer.
        """

        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                value = int(value)
            except:
                pass
        raise ValueError(f"{name} must be an integer. Got {value}.")

    def assert_match(
        self,
        value_a: int | float | Any | None,
        value_b: int | float | Any | None,
        name_a: str,
        name_b: str,
    ) -> int:
        """
        Checks that the two values are equal, and if so, returns the matched value. If
        one value is None, returns the other value. Raise an error if the two values are
        not equal, or if both are None.

        Parameters
        ----------
            value_a: int | float | Any
                The first value to check.
            value_b: int | float | Any
                The second value to check.
            name_a: str
                The name of the first value. Used for error messages.
            name_b: str
                The name of the second value. Used for error messages.

        Returns
        -------
            int
                The matched value.
        """
        if value_a is None and value_b is None:
            raise ValueError(
                f"Both {name_a} and {name_b} are None. At least one must be provided."
            )
        if value_a is None:
            return value_b
        if value_b is None:
            return value_a

        if value_a != value_b:
            raise ValueError(
                f"Mismatch between {name_a} and {name_b}. Got {value_a} and {value_b}."
            )

        return value_a

    def resolve_multiple_ways_to_calculate_value(
        self, name: str, *args: tuple[str, Callable[[Any], Any], dict[str, Any]]
    ) -> Any:
        """
        Parses multiple possible ways to set an attribute, raising errors if the values
        are not consistent.

        Each possible argument is a tuple containing a function and a dictionary of
        keyword arguments. A function fails if any keyword arguments are None, if the
        function raises an error, or if the function returns None.

        The outputs of all non-failing functions are compared, and an error is raised if
        they are not equal.

        Parameters
        ----------
            name: str
                The name of the attribute to set.
            *args: tuple[str, Callable[[Any], Any], dict[str, Any]]
                The possible ways to set the attribute. Each tuple contains a name, a
                function that takes the current value and returns the new value, and a
                dictionary of keyword arguments to pass to the function.
        Returns
        -------
            The value of the attribute.
        """

        error_messages = []

        success_values = []

        for fname, func, kwargs in args:
            for key, value in kwargs.items():
                fname = f"{fname}({', '.join(f'{k}={v}' for k, v in kwargs.items())})"
                if value is None:
                    error_messages.append(f"{fname}: {key} is None.")
            try:
                new_value = func(**kwargs)
            except Exception as e:
                error_messages.append(f"{fname} raised {e}")
            if new_value is None:
                error_messages.append(f"{fname} returned None.")
            else:
                success_values.append((fname, new_value))

        values = set(v[-1] for v in success_values)

        if len(values) == 0:
            raise ValueError(
                f"Could not set {name} with any of the following options:\n\t"
                + "\n\t".join(error_messages)
            )

        if len(values) > 1:
            raise ValueError(
                f"Different ways to set {name} returned conflicting values:\n\t"
                + "\n\t".join(f"{fname}: {value}" for fname, value in success_values)
            )

        return next(iter(values))

    def get_log_messages(self) -> List[str]:
        """
        Returns the log messages for the component.

        Returns
        -------
            List[str]
                The log messages for the component.
        """
        return messages_from_logger(self.logger)

    def pop_log_messages(self) -> List[str]:
        """
        Pops the log messages for the component.

        Returns
        -------
            List[str]
                The log messages for the component.
        """
        return pop_all_messages(self.logger)