import logging
import copy
from typing import Any, Callable, Dict, List
from hwcomponents.logging import get_logger, pop_all_messages, log_all_lines, clear_logs
from hwcomponents.estimator_wrapper import (
    EnergyAreaEstimatorWrapper,
    EnergyAreaQuery,
    Estimation,
)


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
        estimation = Estimation(0, success=False)
        estimator.logger.error(f"{type(e).__name__}: {e}")

    # Add message logs
    estimation.add_messages(pop_all_messages(estimator.logger))
    estimation.estimator_name = estimator.get_name()

    # See if this estimation matches user requested estimator and min accuracy
    attrs = query.component_attributes
    if (
        attrs.get("estimator", None) is not None
        and attrs["estimator"] != estimation.estimator_name
    ) or (
        attrs.get("min_accuracy", None) is not None
        and attrs["min_accuracy"] > estimation.percent_accuracy_0_to_100
    ):
        estimation.fail(
            f"Estimator {estimation.estimator_name} was not selected for query."
        )
    return estimation


def get_energy_estimation(estimator: Any, query: EnergyAreaQuery) -> Estimation:
    e = call_estimator(estimator, query, estimator.estimate_energy)
    if e and e.success and query.action_name == "leak":
        n_instances = query.component_attributes.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e.value *= n_instances
    return e


def get_area_estimation(estimator: Any, query: EnergyAreaQuery) -> Estimation:
    e = call_estimator(estimator, query, estimator.estimate_area)
    if e and e.success:
        n_instances = query.component_attributes.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e.value *= n_instances
    return e


def _get_best_estimate(
    estimators: List[EnergyAreaEstimatorWrapper],
    query: EnergyAreaQuery,
    is_energy_estimation: bool,
) -> Estimation:
    est_func = get_energy_estimation if is_energy_estimation else get_area_estimation

    target = "ENERGY" if is_energy_estimation else "AREA"
    if logging.getLogger("").isEnabledFor(logging.INFO):
        logging.getLogger("").info("")
    logging.getLogger("").info(f"{target} ESTIMATION for {query}")

    for to_drop in ["area", "energy", "area_scale", "energy_scale"]:
        for drop_from in [query.component_attributes, query.action_arguments]:
            if to_drop in drop_from:
                del drop_from[to_drop]

    estimations = []
    supported_estimators = sorted(
        estimators, key=lambda x: x.percent_accuracy, reverse=True
    )
    supported_estimators = [
        p for p in supported_estimators if p.is_class_supported(query)
    ]

    if not supported_estimators:
        if not estimators:
            raise KeyError(f"No estimators found. Please check your configuration.")
        supported_classes = set.union(
            *[set(p.get_component_names()) for p in estimators]
        )
        raise KeyError(
            f"Component {query.component_name} is not supported by any estimators. "
            f"Supported components: " + ", ".join(supported_classes)
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
                f"EnergyArea",
                "info",
                f"{estimation.estimator_name} estimated "
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
            "EnergyArea", "debug", indent_list_text_block("Estimator logs:", full_logs)
        )
    if fail_reasons:
        log_all_lines(
            "EnergyArea",
            "debug",
            indent_list_text_block("Why estimators did not estimate:", fail_reasons),
        )
    if fail_reasons:
        log_all_lines(
            "EnergyArea",
            "info",
            indent_list_text_block(
                "Estimators provided accuracy but failed to estimate:",
                fail_reasons,
            ),
        )

    if estimation and estimation.success:
        return estimation

    clear_logs()

    estimation_target = "energy" if is_energy_estimation else "area"
    raise RuntimeError(
        f"Can not find an {estimation_target} estimator for {query}\n"
        f'{indent_list_text_block("Logs for estimators that could estimate query:", full_logs)}\n'
        f'{indent_list_text_block("Why estimators did not estimate:", fail_reasons)}\n'
        f'\n.\n.\nTo see a list of available component models, run "<command you used> -h" and '
        f"find the option to list components. Alternatively, run accelergy verbose and "
        f"check the log file."
    )


def get_energy(
    estimators: List[EnergyAreaEstimatorWrapper],
    component_name: str,
    component_attributes: Dict[str, Any],
    action_name: str,
    action_arguments: Dict[str, Any],
) -> Estimation:
    query = EnergyAreaQuery(
        component_name, component_attributes, action_name, action_arguments
    )
    return _get_best_estimate(estimators, query, True)


def get_area(
    estimators: List[EnergyAreaEstimatorWrapper],
    component_name: str,
    component_attributes: Dict[str, Any],
) -> Estimation:
    query = EnergyAreaQuery(component_name, component_attributes, None, None)
    return _get_best_estimate(estimators, query, False)
