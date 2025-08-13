import glob
import importlib
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType
from typing import List, Set, Union
from hwcomponents.model_wrapper import EnergyAreaModelWrapper
import inspect
import logging
import copy
import sys
import os
from pkgutil import iter_modules

_ALL_ESTIMATORS = None


def installed_models() -> List[EnergyAreaModelWrapper]:
    # List all Python packages installed that are prefixed with "hwcomponents_"
    global _ALL_ESTIMATORS
    if _ALL_ESTIMATORS is not None:
        return _ALL_ESTIMATORS

    modules = [p.name for p in iter_modules() if p.name.startswith("hwcomponents_")]
    for m in modules:
        logging.info(f"Importing from module: {m}")

    models = []
    model_ids = set()

    # Handle the packages
    for module in modules:
        models.extend(
            get_models_in_module(importlib.import_module(module), model_ids)
        )

    _ALL_ESTIMATORS = models

    return models


def get_models_in_module(
    module: ModuleType, model_ids: Set
) -> List[EnergyAreaModelWrapper]:
    logging.info(f"Getting models in module: {module.__name__}")
    classes = [
        (x, name) for name in dir(module) if inspect.isclass(x := getattr(module, name))
    ]
    # classes = [(x, name) for x, name in classes if x.__module__ == module.__name__]
    found = []
    for x, name in classes:
        superclasses = [c.__name__ for c in inspect.getmro(x)]

        if (
            any(base in superclasses for base in ["EnergyAreaModel", "Model"])
            and not inspect.isabstract(x)
            and id(x) not in model_ids
        ):
            model_ids.add(id(x))
            found.append(EnergyAreaModelWrapper(x, name))
    return found


def get_models(
    *paths_or_packages: Union[str, List[str], List[List[str]]], 
    include_installed: bool = True
) -> List[EnergyAreaModelWrapper]:
    """
    Instantiate a list of model model objects for later queries.
    """
    model_ids = set()
    n_models = 0

    packages = []
    paths = []

    flattened = []
    for path_or_package in paths_or_packages:
        if not isinstance(path_or_package, list):
            path_or_package = [path_or_package]
        for p in path_or_package:
            if isinstance(p, (str, Path)):
                globbed = glob.glob(p, recursive=True)
                flattened.extend(globbed)
            else:
                flattened.append(p)

    models = installed_models() if include_installed else []

    for path_or_package in flattened:
        # Check if it's a package first
        try:
            importlib.import_module(path_or_package)
            packages.append(path_or_package)
        except (ImportError, TypeError):
            # If not, check if it's a file
            if os.path.isfile(path_or_package):
                assert path_or_package.endswith(
                    ".py"
                ), f"Path {path_or_package} is not a Python file"
                paths.append(path_or_package)
            else:
                raise ValueError(
                    f"Path {path_or_package} is not a valid file or package"
                )

    for package in packages:
        models.extend(
            get_models_in_module(importlib.import_module(package), model_ids)
        )

    # Handle the paths
    paths_globbed = []
    allpaths = []
    for p in paths:
        if isinstance(p, list):
            allpaths.extend(p)
        else:
            allpaths.append(p)

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

        new_models = []
        for path in newpaths:
            logging.info(
                f"Loading models from {path}. Errors below are likely due to the model."
            )
            prev_sys_path = copy.deepcopy(sys.path)
            sys.path.append(os.path.dirname(os.path.abspath(path)))
            python_module = SourceFileLoader(
                f"model{n_models}", path
            ).load_module()
            new_models += get_models_in_module(python_module, model_ids)
            sys.path = prev_sys_path
            n_models += 1

        if not new_models:
            raise ValueError(f"No models found in {p}")

        models.extend(new_models)

    return models
