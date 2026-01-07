import logging
import copy
from typing import Any, Callable, Dict, List, Tuple
from hwcomponents.model import ComponentModel
from hwcomponents._logging import (
    get_logger,
    pop_all_messages,
    log_all_lines,
    clear_logs,
)
from hwcomponents._model_wrapper import (
    ComponentModelWrapper,
    ModelQuery,
    Estimation,
    EstimatorError,
    ModelEstimation,
    FloatEstimation,
)
from hwcomponents.find_models import installed_models


def _indent_list_text_block(prefix: str, list_to_print: List[str]):
    if not list_to_print:
        return ""
    return "\n| ".join(
        [f"{prefix}"] + [str(l).replace("\n", "\n|  ") for l in list_to_print]
    )


def _call_model(
    model: ComponentModelWrapper,
    query: ModelQuery,
    target_func: Callable,
) -> Estimation:
    # Clear the logger
    pop_all_messages(model.logger)
    try:
        estimation = target_func(query)
    except Exception as e:
        estimation = FloatEstimation(0, success=False, model_name=model.get_name())
        model.logger.error(f"{type(e).__name__}: {e}")
        # Add the full traceback
        import traceback

        estimation.add_messages(traceback.format_exc().split("\n"))
        return estimation

    # Add message logs
    estimation.add_messages(pop_all_messages(model.logger))
    estimation.model_name = model.get_name()

    # See if this estimation matches user requested model and min priority
    attrs = query.component_attributes
    prefix = f"Model {estimation.model_name} did not"
    if attrs.get("model", estimation.model_name) != estimation.model_name:
        estimation.fail(f"{prefix} match requested model {attrs['model']}")
    if attrs.get("min_priority", -float("inf")) > model.model_cls.priority:
        estimation.fail(f"{prefix} meet min_priority {attrs['min_priority']}")
    return estimation


def _get_energy_estimation(
    model: ComponentModelWrapper, query: ModelQuery
) -> FloatEstimation:
    e = _call_model(model, query, model.get_action_energy_latency)
    if e.success:
        e.value = e.value[0]
    return e


def _get_latency_estimation(
    model: ComponentModelWrapper, query: ModelQuery
) -> FloatEstimation:
    e = _call_model(model, query, model.get_action_energy_latency)
    if e.success:
        e.value = e.value[1]
    return e


def _get_area_estimation(
    model: ComponentModelWrapper, query: ModelQuery
) -> FloatEstimation:
    e = _call_model(model, query, model.get_area)
    return e


def _get_leak_power_estimation(
    model: ComponentModelWrapper, query: ModelQuery
) -> FloatEstimation:
    e = _call_model(model, query, model.get_leak_power)
    return e


def _select_model(
    model: ComponentModelWrapper,
    query: ModelQuery,
) -> ModelEstimation:
    for required_action in query.required_actions:
        if required_action not in model.get_action_names():
            e = ModelEstimation(0, success=False, model_name=model.get_name())
            e.fail(
                f"Model {model.get_name()} does not support action {required_action}"
            )
            return e
    callfunc = lambda x: ModelEstimation(
        model.get_initialized_subclass(x),
        success=True,
        model_name=model.get_name(),
    )
    return _call_model(model, query, callfunc)


def _wrap_model(
    model: ComponentModel | ComponentModelWrapper,
) -> ComponentModelWrapper:
    if isinstance(model, ComponentModelWrapper):
        return model
    return ComponentModelWrapper(model, model.__name__)


def _get_best_estimate(
    query: ModelQuery,
    target: str,
    models: List[ComponentModelWrapper] | List[ComponentModel] = None,
    _return_estimation_object: bool = False,
    _relaxed_component_name_selection: bool = False,
) -> FloatEstimation | ComponentModel:
    if models is None:
        models = installed_models(_return_wrappers=True)

    models = [_wrap_model(m) for m in models]

    if target == "energy":
        est_func = _get_energy_estimation
    elif target == "latency":
        est_func = _get_latency_estimation
    elif target == "area":
        est_func = _get_area_estimation
    elif target == "model":
        est_func = _select_model
    elif target == "leak_power":
        est_func = _get_leak_power_estimation
    else:
        raise ValueError(f"Invalid target: {target}")

    logging.getLogger("").info(f"{target} estimation for {query}")

    estimations = []

    def _get_supported_models(relaxed_component_name_selection: bool):
        supported_models = []
        init_errors = []
        for model in models:
            try:
                if not model.is_component_supported(
                    query, relaxed_component_name_selection
                ):
                    continue
                supported_models.append(model)
            except Exception as e:
                init_errors.append((model, e))
        return supported_models, init_errors

    supported_models, init_errors = _get_supported_models(
        _relaxed_component_name_selection
    )

    if not supported_models:
        if not models:
            raise EstimatorError(
                f"No models found. Please install hwcomponents models."
            )
        supported_classes = set.union(*[set(p.get_component_names()) for p in models])

        err_str = []
        if not _relaxed_component_name_selection:
            near_supported, _ = _get_supported_models(True)
            if near_supported:
                err_str.append(
                    f"Some component models have similar names to the given component "
                    f"name. Did you mean any of the following?\n\t"
                )
                for model in near_supported:
                    err_str.append(f"\t{model.get_name()}")

        if init_errors:
            err_str.append(
                f"Component {query.component_name} is supported by models, but the "
                f"following models could could not be initialized."
            )
            for model, err in init_errors:
                err_str.append(f"\t{model.get_name()}")
                err_str.append(f"\t{str(err).replace("\n", "\n\t")}")
            raise EstimatorError("\n".join(err_str))

        e = (
            f"Component {query.component_name} is not supported by any models. "
            f"Supported components: " + ", ".join(sorted(supported_classes))
        )
        if err_str:
            e += "\n" + "\n".join(err_str)
        raise EstimatorError(e)

    estimation = None
    for model in supported_models:
        estimation = est_func(model, copy.deepcopy(query))
        logger = get_logger(model.get_name())
        if not estimation.success:
            estimation.add_messages(pop_all_messages(logger))
            estimations.append((model.priority, estimation))
        else:
            log_all_lines(
                f"HWComponents",
                "info",
                f"{estimation.model_name} returned "
                f"{estimation} with priority {model.priority}. "
                + _indent_list_text_block("Messages:", estimation.messages),
            )
            break
    else:
        estimation = None

    full_logs = [
        _indent_list_text_block(
            f"{e.model_name} with priority {a} estimating value: ", e.messages
        )
        for a, e in estimations
    ]
    fail_reasons = [
        f"{e.model_name} with priority {a} estimating value: " f"{e.lastmessage()}"
        for a, e in estimations
    ]

    if full_logs:
        log_all_lines(
            "HWComponents",
            "debug",
            _indent_list_text_block("Model logs:", full_logs),
        )
    if fail_reasons:
        log_all_lines(
            "HWComponents",
            "debug",
            _indent_list_text_block("Why models did not estimate:", fail_reasons),
        )
    if fail_reasons:
        log_all_lines(
            "HWComponents",
            "info",
            _indent_list_text_block(
                "Models provided accuracy but failed to estimate:",
                fail_reasons,
            ),
        )

    clear_logs()

    if estimation is not None and estimation.success:
        if _return_estimation_object:
            return estimation
        return estimation.value

    clear_logs()

    raise RuntimeError(
        f"Can not find an {target} model for {query}\n"
        f'{_indent_list_text_block("Logs for models that could estimate query:", full_logs)}\n'
        f'{_indent_list_text_block("Why models did not estimate:", fail_reasons)}\n'
        f'\n.\n.\nTo see a list of available component models, run "hwc --list".'
    )


def get_energy(
    component_name: str,
    component_attributes: Dict[str, Any],
    action_name: str,
    action_arguments: Dict[str, Any],
    models: List[ComponentModelWrapper] = None,
    _return_estimation_object: bool = False,
    _relaxed_component_name_selection: bool = False,
) -> float | Estimation:
    """
    Finds the energy using the best-matching model. "Best" is defined as the
    highest-priority model that has all required attributes specified in
    component_attributes and a matching action with all required arguments specified
    in action_arguments.

    Parameters
    ----------
        component_name: The name of the component.
        component_attributes: The attributes of the component.
        action_name: The name of the action.
        action_arguments: The arguments of the action.
        models: The models to use.
        _return_estimation_object: Whether to return the estimation object instead of
            the energy value.
        _relaxed_component_name_selection: Whether to relax the component name
            selection. Relaxed selection ignores underscores in the component name.

    Returns
    -------
        The energy in Joules.
    """
    query = ModelQuery(
        component_name.lower(), component_attributes, action_name, action_arguments
    )
    return _get_best_estimate(
        query,
        "energy",
        models,
        _return_estimation_object,
        _relaxed_component_name_selection,
    )


def get_latency(
    component_name: str,
    component_attributes: Dict[str, Any],
    action_name: str,
    action_arguments: Dict[str, Any],
    models: List[ComponentModelWrapper] = None,
    _return_estimation_object: bool = False,
    _relaxed_component_name_selection: bool = False,
) -> float | Estimation:
    """
    Finds the latency using the best-matching model. "Best" is defined as the
    highest-priority model that has all required attributes specified in
    component_attributes and a matching action with all required arguments specified
    in action_arguments.

    Parameters
    ----------
        component_name: The name of the component.
        component_attributes: The attributes of the component.
        action_name: The name of the action.
        action_arguments: The arguments of the action.
        models: The models to use.
        _return_estimation_object: Whether to return the estimation object instead of
            the latency value.
        _relaxed_component_name_selection: Whether to relax the component name
            selection. Relaxed selection ignores underscores in the component name.

    Returns
    -------
        The latency in seconds.
    """
    query = ModelQuery(
        component_name.lower(), component_attributes, action_name, action_arguments
    )
    return _get_best_estimate(
        query,
        "latency",
        models,
        _return_estimation_object,
        _relaxed_component_name_selection,
    )


def get_area(
    component_name: str,
    component_attributes: Dict[str, Any],
    models: List[ComponentModelWrapper] = None,
    _return_estimation_object: bool = False,
    _relaxed_component_name_selection: bool = False,
) -> float | Estimation:
    """
    Finds the area using the best-matching model. "Best" is defined as the
    highest-priority model that has all required attributes specified in
    component_attributes.

    Parameters
    ----------
        component_name: The name of the component.
        component_attributes: The attributes of the component.
        models: The models to use.
        _return_estimation_object: Whether to return the estimation object instead of
            the area value.
        _relaxed_component_name_selection: Whether to relax the component name
            selection. Relaxed selection ignores underscores in the component name.

    Returns
    -------
        The area in m^2.
    """
    query = ModelQuery(component_name.lower(), component_attributes, None, None)
    return _get_best_estimate(
        query,
        "area",
        models,
        _return_estimation_object,
        _relaxed_component_name_selection,
    )


def get_leak_power(
    component_name: str,
    component_attributes: Dict[str, Any],
    models: List[ComponentModelWrapper] = None,
    _return_estimation_object: bool = False,
    _relaxed_component_name_selection: bool = False,
) -> float | Estimation:
    """
    Finds the leak power using the best-matching model. "Best" is defined as the
    highest-priority model that has all required attributes specified in
    component_attributes.

    Parameters
    ----------
        component_name: The name of the component.
        component_attributes: The attributes of the component.
        models: The models to use.
        _relaxed_component_name_selection: Whether to relax the component name
            selection. Relaxed selection ignores underscores in the component name.

    Returns
    -------
        The leak power in Watts.
    """
    query = ModelQuery(component_name.lower(), component_attributes, None, None)
    return _get_best_estimate(
        query,
        "leak_power",
        models,
        _return_estimation_object,
        _relaxed_component_name_selection,
    )


def get_model(
    component_name: str,
    component_attributes: Dict[str, Any],
    required_actions: List[str] = (),
    models: List[ComponentModelWrapper] = None,
    _return_estimation_object: bool = False,
    _relaxed_component_name_selection: bool = False,
) -> ComponentModelWrapper:
    """
    Finds the best model for the given component. "Best" is defined as the
    highest-priority model that has all required attributes specified in
    component_attributes, and has actions for all of required_actions.

    Parameters
    ----------
        component_name: The name of the component.
        component_attributes: The attributes of the component.
        required_actions: The actions that are required for the component.
        models: The models to use.
        _return_estimation_object: Whether to return the estimation object instead of
            the model wrapper.
        _relaxed_component_name_selection: Whether to relax the component name
            selection. Relaxed selection ignores underscores in the component name.

    Returns
    -------
        The best model wrapper.
    """
    query = ModelQuery(
        component_name.lower(), component_attributes, None, None, required_actions
    )
    return _get_best_estimate(
        query,
        "model",
        models,
        _return_estimation_object,
        _relaxed_component_name_selection,
    )
