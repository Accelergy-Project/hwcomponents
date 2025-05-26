import glob
from importlib.machinery import SourceFileLoader
from types import ModuleType
from typing import List, Set, Union
from hwcomponents.estimator_wrapper import (
    EnergyAreaEstimator,
    EnergyAreaEstimatorWrapper,
)
import inspect
import logging
import copy
import sys
import os


def get_estimators_in_module(
    module: ModuleType, estimator_ids: Set
) -> List[EnergyAreaEstimatorWrapper]:
    classes = [
        (x, name) for name in dir(module) if inspect.isclass(x := getattr(module, name))
    ]
    classes = [(x, name) for x, name in classes if x.__module__ == module.__name__]
    found = []
    for x, name in classes:
        superclasses = [c.__name__ for c in inspect.getmro(x)]
        if (
            any(base in superclasses for base in ["EnergyAreaEstimator", "Estimator"])
            and not inspect.isabstract(x)
            and id(x) not in estimator_ids
        ):
            estimator_ids.add(id(x))
            found.append(EnergyAreaEstimatorWrapper(x, name))
    return found


def get_estimators(*paths: Union[str, List[str]]) -> List[EnergyAreaEstimatorWrapper]:
    """
    Instantiate a list of estimator estimator objects for later queries.
    """
    paths_globbed = []
    allpaths = []
    for p in paths:
        if isinstance(p, list):
            allpaths.extend(p)
        else:
            allpaths.append(p)

    # Load Estimators
    estimators = []
    estimator_ids = set()
    n_estimators = 0

    for p in allpaths:
        logging.info(f"Checking path: {p}")
        newpaths = []
        if os.path.isfile(p):
            assert p.endswith(".py"), f"Path {p} is not a Python file"
            newpaths.append(p)
        else:
            newpaths += list(glob.glob(p, recursive=True))
            newpaths += list(glob.glob(os.path.join(p, "**"), recursive=True))
        paths_globbed.extend(newpaths)
        if not newpaths:
            raise ValueError(
                f"Path {p} does not have any Python files. Please check the path and try again."
            )

        newpaths = [p.rstrip("/") for p in newpaths]
        newpaths = [p.replace("\\", "/") for p in newpaths]
        newpaths = [p.replace("//", "/") for p in newpaths]
        newpaths = [p for p in newpaths if p.endswith(".py")]
        newpaths = [p for p in newpaths if not p.endswith("setup.py")]
        newpaths = [p for p in newpaths if not p.endswith("__init__.py")]

        new_estimators = []
        for path in newpaths:
            logging.info(
                f"Loading estimators from {path}. Errors below are likely due to the estimator."
            )
            prev_sys_path = copy.deepcopy(sys.path)
            sys.path.append(os.path.dirname(os.path.abspath(path)))
            python_module = SourceFileLoader(
                f"estimator{n_estimators}", path
            ).load_module()
            new_estimators += get_estimators_in_module(python_module, estimator_ids)
            sys.path = prev_sys_path
            n_estimators += 1

        if not new_estimators:
            raise ValueError(f"No estimators found in {p}")

        estimators.extend(new_estimators)

    return estimators
