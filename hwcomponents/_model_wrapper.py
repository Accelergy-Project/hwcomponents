import inspect
import logging
from numbers import Number
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Union
from .model import ComponentModel
from ._logging import (
    move_queue_from_one_logger_to_another,
    ListLoggable,
    pop_all_messages,
)


class EstimatorError(Exception):
    def __str__(self):
        return self.message

    def __repr__(self):
        return str(self)

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class PrintableCall:
    def __init__(
        self,
        name: str,
        args: List[str] = (),
        defaults: Dict[str, Any] = None,
    ):
        self.name = name
        self.args = args
        self.defaults = defaults or {}

    def __str__(self):
        n = self.name
        args = [str(a) for a in self.args] + [
            f"{k}={v}" for k, v in self.defaults.items()
        ]

        return f"{n}({', '.join(args)})"


class ModelQuery:
    """A query to an ComponentModel."""

    def __init__(
        self,
        component_name: str,
        component_attributes: Dict[str, Any],
        action_name: str = None,
        action_arguments: Dict[str, Any] = None,
        required_actions: List[str] = (),
    ):
        self.component_name = component_name
        self.action_name = action_name
        # Attributes and arguments are only included if they are not None
        action_arguments = {} if action_arguments is None else action_arguments
        self.action_arguments = {
            k: v for k, v in action_arguments.items() if v is not None
        }
        self.component_attributes = {
            k: v for k, v in component_attributes.items() if v is not None
        }
        self.required_actions = required_actions

    def __str__(self):
        attrs_stringified = ", ".join(
            [f"{k}={v}" for k, v in self.component_attributes.items()]
        )
        s = f"{self.component_name}({attrs_stringified})"
        if self.action_name:
            args_stringified = ", ".join(
                [f"{k}={v}" for k, v in self.action_arguments.items()]
            )
            s += f".{self.action_name}({args_stringified})"
        return s


class Estimation:
    value: Union[int, float, ComponentModel]
    success: bool
    messages: List[str]
    model_name: Optional[str]

    def __init__(
        self,
        value: Union[int, float, ComponentModel],
        success: bool = True,
        messages: List[str] = (),
        model_name: Optional[str] = None,
    ):
        self.value = value
        self.success = success
        self.messages = list(messages)
        self.model_name = model_name

    def add_messages(self, messages: Union[List[str], str]):
        """
        Adds messages to the internal message list. The messages are reported
        depending on model selections and verbosity level.
        """
        if isinstance(messages, str):
            self.add_messages([messages])
        else:
            self.messages += messages

    def fail(self, message: str):
        """Marks this estimation as failed and adds the message."""
        self.success = False
        self.add_messages(message)

    def lastmessage(self) -> str:
        """Returns the last message in the message list. If no messages, returns
        a default."""
        if self.messages:
            return self.messages[-1]
        else:
            return f"No messages found."


class FloatEstimation(Estimation):
    def __init__(
        self,
        value: Union[int, float, tuple[Union[int, float], ...]],
        success: bool = True,
        messages: List[str] = [],
        model_name: Optional[str] = None,
    ):
        super().__init__(value, success, messages, model_name)


class ModelEstimation(Estimation):
    def __init__(
        self,
        value: Union[int, float],
        success: bool = True,
        messages: List[str] = [],
        model_name: Optional[str] = None,
    ):
        super().__init__(value, success, messages, model_name)


class CallableFunction:
    """Wrapper for a function to provide error checking and argument
    matching."""

    def __init__(
        self,
        function: Callable,
        logger: logging.Logger,
        force_name_override: str = None,
        is_init: bool = False,
    ):
        if not isinstance(function, Callable):
            raise TypeError(
                f"Function {function.__name__} must be an instance of Callable, not {type(function)}"
            )

        self.function = function
        self.additional_kwargs = getattr(function, "_additional_kwargs", set())
        if is_init:
            function = function.__init__
        elif getattr(function, "_is_component_action", False):
            function = function._original_function

        args = function.__code__.co_varnames[1 : function.__code__.co_argcount]
        default_length = (
            len(function.__defaults__) if function.__defaults__ is not None else 0
        )

        self.function_name = function.__name__
        if force_name_override is not None:
            self.function_name = force_name_override
        self.non_default_args = args[: len(args) - default_length]
        self.default_args = args[len(args) - default_length :]
        self.default_arg_values = (
            function.__defaults__ if function.__defaults__ is not None else []
        )
        self.logger = logger

    def get_error_message_for_name_match(self, name: str, component_name: str = ""):
        if self.function_name != name:
            return f"Function name {self.function_name} does not match my name {component_name}.{name}"
        return None

    def get_error_message_for_non_default_arg_match(
        self, kwags: dict, component_name: str = ""
    ) -> Optional[str]:
        for arg in self.non_default_args:
            if kwags.get(arg) is None:
                return (
                    f"Argument for {component_name}.{self.function_name} is missing: {arg}. "
                    f'Arguments provided: {", ".join(kwags.keys())}'
                )
        return None

    def get_call_error_message(
        self, name: str, kwargs: dict, component_name: str = ""
    ) -> Optional[str]:
        name_error = self.get_error_message_for_name_match(name, component_name)
        if name_error is not None:
            return name_error
        arg_error = self.get_error_message_for_non_default_arg_match(
            kwargs, component_name
        )
        if arg_error is not None:
            return arg_error
        return None

    def call(
        self,
        kwargs: dict,
        component_name: str = "",
        call_function_on_object: object = None,
    ) -> Any:
        kwags_included = {
            k: v
            for k, v in kwargs.items()
            if k in self.non_default_args
            or k in self.default_args
            or k in self.additional_kwargs
        }
        self.logger.info(
            f"Calling {self.function_name} with arguments {kwags_included}"
        )
        unneeded_args = [k for k in kwargs.keys() if k not in kwags_included]
        if unneeded_args:
            self.logger.warn(
                f"Unused arguments for {component_name}.{self.function_name}: "
                f'({", ".join(unneeded_args)}) '
                f'Arguments used: ({", ".join(kwags_included.keys())})'
            )

        if call_function_on_object is not None:
            return self.function(call_function_on_object, **kwags_included)
        return self.function(**kwags_included)

    def __str__(self):
        return str(
            PrintableCall(
                self.function_name if self.function_name != "__init__" else "",
                self.non_default_args,
                {a: b for a, b in zip(self.default_args, self.default_arg_values)},
            )
        )


class ComponentModelWrapper(ListLoggable):
    def __init__(self, model_cls: type, component_name: str):
        check_for_valid_model_attrs(model_cls)
        self.model_cls = model_cls
        self.model_name = component_name
        cls_component_name = model_cls._component_name()
        if isinstance(cls_component_name, str):
            cls_component_name = [cls_component_name]
        if not isinstance(cls_component_name, list):
            raise ValueError(
                f"component_name must be a string or list of strings, not {type(cls_component_name)}"
            )
        self.component_name = [c.lower() for c in cls_component_name]
        super().__init__(name=self.get_name())

        self.priority = model_cls.priority
        if self.priority < 0 or self.priority > 1:
            raise ValueError(f"Priority must be between 0 and 1, not {self.priority}")
        self.init_function = CallableFunction(model_cls, self.logger, is_init=True)

        self.actions = [
            CallableFunction(getattr(model_cls, a), self.logger)
            for a in dir(model_cls)
            if getattr(
                getattr(model_cls, a),
                "_is_component_action",
                False,
            )
        ]
        # self.actions.append(CallableFunction(model_cls.leak, self.logger))
        logging.debug(
            f"Added model {self.model_name} that for component {self.component_name}"
        )

    def get_action_names(self) -> List[str]:
        return [a.function_name for a in self.actions]

    def fail_missing(self, missing: str):
        raise AttributeError(
            f"Primitive component {self.component_name} " f"must have {missing}"
        )

    def is_component_supported(
        self, query: ModelQuery, relaxed_component_name_selection: bool = False
    ) -> bool:
        if query.component_name.lower() in self.component_name:
            pass
        elif query.component_name.lower().replace("_", "") in self.component_name:
            if relaxed_component_name_selection:
                pass
            else:
                self.logger.error(
                    f"Component name is similar to supported component names, but not "
                    f"supported. Did you mean {self.component_name}?"
                )
                return False
        else:
            self.logger.error(
                f"Component name {query.component_name} is not supported. "
                f"Supported component names: {self.component_name}"
            )
            return False

        init_error = self.init_function.get_call_error_message(
            "__init__", query.component_attributes, self.component_name
        )
        if init_error is not None:
            self.logger.error(init_error)
            raise EstimatorError(init_error)
        return True

    def get_initialized_subclass(self, query: ModelQuery) -> ComponentModel:
        self.logger.info(
            f"Initializing {self.model_cls.__name__} from {self.model_cls.__module__}"
        )
        subclass = self.init_function.call(
            query.component_attributes, self.component_name
        )
        subclass._init_logger()
        return subclass

    def get_matching_actions(self, query: ModelQuery) -> List[CallableFunction]:
        # Find actions that match the name
        name_matches = [a for a in self.actions if a.function_name == query.action_name]
        if len(name_matches) == 0:
            raise AttributeError(
                f"No action with name {query.action_name} found in {self.component_name}. "
                f'Actions supported: {", ".join(self.get_action_names())}'
            )

        # Find actions that match the arguments
        matching_name_and_arg_actions = [
            a
            for a in name_matches
            if a.get_call_error_message(query.action_name, query.action_arguments)
            is None
        ]
        if len(matching_name_and_arg_actions) == 0:
            matching_func_strings = [
                (
                    f"{a.function_name}("
                    + ", ".join(
                        list(a.non_default_args)
                        + ["OPTIONAL " + b for b in a.default_args]
                    )
                )
                + ")"
                for a in name_matches
            ]
            args_provided = (
                query.action_arguments.keys() if query.action_arguments else ["<none>"]
            )
            raise AttributeError(
                f"Action with name {query.action_name} found in {self.component_name}, "
                f"but provided arguments do not match.\n\t"
                f'Arguments provided: {", ".join(args_provided)}\n\t'
                f"Possible actions:\n\t\t" + "\n\t\t".join(matching_func_strings)
            )
        return matching_name_and_arg_actions

    def get_action_energy_latency(
        self, query: ModelQuery, initialized_obj: ComponentModel = None
    ) -> Estimation:
        """Returns the energy and latency estimation for the given action."""
        if initialized_obj is None:
            initialized_obj = self.get_initialized_subclass(query)
            move_queue_from_one_logger_to_another(initialized_obj.logger, self.logger)
        supported_actions = self.get_matching_actions(query)
        if len(supported_actions) == 0:
            raise AttributeError(
                f"No action with name {query.action_name} found in "
                f"{self.component_name}. Actions supported: "
                f"{', '.join(self.get_action_names())}"
            )
        try:
            result = supported_actions[0].call(
                query.action_arguments, self.component_name, initialized_obj
            )
            energy_value, latency_value = result
            estimation = FloatEstimation(
                value=(energy_value, latency_value),
            )
        except Exception as e:
            move_queue_from_one_logger_to_another(initialized_obj.logger, self.logger)
            raise e
        estimation.add_messages(pop_all_messages(initialized_obj.logger))
        estimation.model_name = self.model_name
        return estimation

    def get_area(self, query: ModelQuery) -> Estimation:
        """Returns the area estimation for the given action."""
        subclass = self.get_initialized_subclass(query)
        return FloatEstimation(
            value=subclass.area,
            success=True,
            model_name=self.model_name,
            messages=pop_all_messages(subclass.logger),
        )

    def get_leak_power(self, query: ModelQuery) -> Estimation:
        """Returns the leak power estimation for the given action."""
        subclass = self.get_initialized_subclass(query)
        return FloatEstimation(
            value=subclass.leak_power,
            success=True,
            model_name=self.model_name,
            messages=pop_all_messages(subclass.logger),
        )

    def get_name(self) -> str:
        return self.model_name

    def get_component_names(self) -> List[str]:
        return (
            [self.component_name]
            if isinstance(self.component_name, str)
            else self.component_name
        )

    @staticmethod
    def print_action(action: CallableFunction) -> str:
        return action.function_name


def check_for_valid_model_attrs(model: ComponentModel):
    # Check for valid component_name. Must be a string or list of strings
    component_name = model._component_name()
    if not isinstance(component_name, str) and not (
        isinstance(component_name, (list, tuple))
        and all(isinstance(n, str) for n in component_name)
    ):
        raise AttributeError(
            f"ComponentModel {model} component_name must be a string or list/tuple of strings"
        )

    # Check for valid priority. Must be a number between 0 and 100
    if getattr(model, "priority", None) is None:
        raise AttributeError(
            f'ComponentModel for {component_name} must have a "priority" ' f"attribute."
        )
    priority = model.priority
    if not isinstance(priority, Number):
        raise AttributeError(
            f"ComponentModel for {component_name} priority must be a "
            f"number. It is currently a {type(priority)}"
        )
    if priority < 0 or priority > 1:
        raise AttributeError(
            f"ComponentModel for {component_name} priority must be "
            f"between 0 and 1 inclusive."
        )
