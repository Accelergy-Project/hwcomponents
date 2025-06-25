import logging
import copy
from typing import Any, Callable, Dict, List
from hwcomponents.estimator import EnergyAreaEstimator
from hwcomponents.logging import get_logger, pop_all_messages, log_all_lines, clear_logs
from hwcomponents.estimator_wrapper import (
    EnergyAreaEstimatorWrapper,
    EnergyAreaQuery,
    Estimation,
    EstimatorError,
    EstimatorEstimation,
    FloatEstimation,
)
from hwcomponents.find_estimators import installed_estimators


def indent_list_text_block(prefix: str, list_to_print: List[str]):
    if not list_to_print:
        return ""
    return "\n| ".join(
        [f"{prefix}"] + [str(l).replace("\n", "\n|  ") for l in list_to_print]
    )


def call_estimator(
    estimator: EnergyAreaEstimatorWrapper,
    query: EnergyAreaQuery,
    target_func: Callable,
) -> Estimation:
    # Clear the logger
    pop_all_messages(estimator.logger)
    try:
        estimation = target_func(query)
    except Exception as e:
        estimation = FloatEstimation.get_estimation(
            0, success=False, estimator_name=estimator.get_name()
        )
        estimator.logger.error(f"{type(e).__name__}: {e}")
        # Add the full traceback
        import traceback

        estimation.add_messages(traceback.format_exc().split("\n"))
        return estimation

    # Add message logs
    estimation.add_messages(pop_all_messages(estimator.logger))
    estimation.estimator_name = estimator.get_name()

    # See if this estimation matches user requested estimator and min accuracy
    attrs = query.component_attributes
    prefix = f"Estimator {estimation.estimator_name} did not"
    if attrs.get("estimator", estimation.estimator_name) != estimation.estimator_name:
        estimation.fail(f"{prefix} match requested estimator {attrs['estimator']}")
    if (
        attrs.get("min_accuracy", -float("inf"))
        > estimator.estimator_cls.percent_accuracy_0_to_100
    ):
        estimation.fail(f"{prefix} meet min_accuracy {attrs['min_accuracy']}")
    return estimation


def _get_energy_estimation(
    estimator: EnergyAreaEstimatorWrapper, query: EnergyAreaQuery
) -> FloatEstimation:
    e = call_estimator(estimator, query, estimator.estimate_energy)
    if e and e.success and query.action_name == "leak":
        n_instances = query.component_attributes.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e *= n_instances
    return e


def _get_area_estimation(
    estimator: EnergyAreaEstimatorWrapper, query: EnergyAreaQuery
) -> FloatEstimation:
    e = call_estimator(estimator, query, estimator.estimate_area)
    if e and e.success:
        n_instances = query.component_attributes.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e *= n_instances
    return e


def _get_leak_power_estimation(
    estimator: EnergyAreaEstimatorWrapper, query: EnergyAreaQuery
) -> FloatEstimation:
    e = call_estimator(estimator, query, estimator.estimate_leak_power)
    if e and e.success:
        n_instances = query.component_attributes.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e *= n_instances
    return e


def _select_estimator(
    estimator: EnergyAreaEstimatorWrapper,
    query: EnergyAreaQuery,
) -> EstimatorEstimation:
    for required_action in query.required_actions:
        if required_action not in estimator.get_action_names():
            e = EstimatorEstimation.get_estimation(
                0, success=False, estimator_name=estimator.get_name()
            )
            e.fail(
                f"Estimator {estimator.get_name()} does not support action {required_action}"
            )
            return e
    callfunc = lambda x: EstimatorEstimation.get_estimation(
        estimator.get_initialized_subclass(x),
        success=True,
        estimator_name=estimator.get_name(),
    )
    return call_estimator(estimator, query, callfunc)


def _get_best_estimate(
    query: EnergyAreaQuery,
    target: str,
    estimators: List[EnergyAreaEstimatorWrapper] = None,
) -> FloatEstimation | EnergyAreaEstimator:
    if estimators is None:
        estimators = installed_estimators()

    if target == "energy":
        est_func = _get_energy_estimation
    elif target == "area":
        est_func = _get_area_estimation
    elif target == "estimator":
        est_func = _select_estimator
    elif target == "leak_power":
        est_func = _get_leak_power_estimation
    else:
        raise ValueError(f"Invalid target: {target}")

    logging.getLogger("").info(f"{target} estimation for {query}")

    for to_drop in ["area", "energy", "area_scale", "energy_scale"]:
        for drop_from in [query.component_attributes, query.action_arguments]:
            if to_drop in drop_from:
                del drop_from[to_drop]

    estimations = []
    supported_estimators = sorted(
        estimators, key=lambda x: x.percent_accuracy, reverse=True
    )
    supported_estimators = []
    init_errors = []
    for estimator in estimators:
        try:
            if not estimator.is_component_supported(query):
                continue
            supported_estimators.append(estimator)
        except Exception as e:
            init_errors.append((estimator, e))

    if not supported_estimators:
        if not estimators:
            raise EstimatorError(
                f"No estimators found. Please install hwcomponents estimators."
            )
        supported_classes = set.union(
            *[set(p.get_component_names()) for p in estimators]
        )
        if init_errors:
            err_str = [
                f"Component {query.component_name} is supported by estimators, but the "
                f"following estimators could could not be initialized."
            ]
            for estimator, err in init_errors:
                err_str.append(f"\t{estimator.get_name()}")
                err_str.append(f"\t" + str(err).replace("\n", "\n\t"))
            raise EstimatorError("\n".join(err_str))
        raise EstimatorError(
            f"Component {query.component_name} is not supported by any estimators. "
            f"Supported components: " + ", ".join(sorted(supported_classes))
        )

    estimation = None
    for estimator in supported_estimators:
        estimation = est_func(estimator, copy.deepcopy(query))
        logger = get_logger(estimator.get_name())
        if not estimation.success:
            estimation.add_messages(pop_all_messages(logger))
            estimations.append((estimator.percent_accuracy, estimation))
        else:
            log_all_lines(
                f"HWComponents",
                "info",
                f"{estimation.estimator_name} returned "
                f"{estimation} with accuracy {estimator.percent_accuracy}. "
                + indent_list_text_block("Messages:", estimation.messages),
            )
            break

    full_logs = [
        indent_list_text_block(
            f"{e.estimator_name} with accuracy {a} estimating value: ", e.messages
        )
        for a, e in estimations
    ]
    fail_reasons = [
        f"{e.estimator_name} with accuracy {a} estimating value: " f"{e.lastmessage()}"
        for a, e in estimations
    ]

    if full_logs:
        log_all_lines(
            "HWComponents",
            "debug",
            indent_list_text_block("Estimator logs:", full_logs),
        )
    if fail_reasons:
        log_all_lines(
            "HWComponents",
            "debug",
            indent_list_text_block("Why estimators did not estimate:", fail_reasons),
        )
    if fail_reasons:
        log_all_lines(
            "HWComponents",
            "info",
            indent_list_text_block(
                "Estimators provided accuracy but failed to estimate:",
                fail_reasons,
            ),
        )

    if estimation is not None and estimation.success:
        return estimation.value if target == "estimator" else estimation

    clear_logs()

    raise RuntimeError(
        f"Can not find an {target} estimator for {query}\n"
        f'{indent_list_text_block("Logs for estimators that could estimate query:", full_logs)}\n'
        f'{indent_list_text_block("Why estimators did not estimate:", fail_reasons)}\n'
        f'\n.\n.\nTo see a list of available component models, run "hwc --list".'
    )

def get_energy(
    component_name: str,
    component_attributes: Dict[str, Any],
    action_name: str,
    action_arguments: Dict[str, Any],
    estimators: List[EnergyAreaEstimatorWrapper] = None,
) -> Estimation:
    query = EnergyAreaQuery(
        component_name.lower(), component_attributes, action_name, action_arguments
    )
    return _get_best_estimate(query, "energy", estimators)


def get_area(
    component_name: str,
    component_attributes: Dict[str, Any],
    estimators: List[EnergyAreaEstimatorWrapper] = None,
) -> Estimation:
    query = EnergyAreaQuery(component_name.lower(), component_attributes, None, None)
    return _get_best_estimate(query, "area", estimators)


def get_leak_power(
    component_name: str,
    component_attributes: Dict[str, Any],
    estimators: List[EnergyAreaEstimatorWrapper] = None,
) -> Estimation:
    query = EnergyAreaQuery(component_name.lower(), component_attributes, None, None)
    return _get_best_estimate(query, "leak_power", estimators)


def get_estimator(
    component_name: str,
    component_attributes: Dict[str, Any],
    required_actions: List[str] = (),
    estimators: List[EnergyAreaEstimatorWrapper] = None,
) -> EnergyAreaEstimatorWrapper:
    query = EnergyAreaQuery(
        component_name.lower(), component_attributes, None, None, required_actions
    )
    return _get_best_estimate(query, "estimator", estimators)
