from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from rpy2 import robjects

from ._bridge import MizerError, MizerREnvironment, get_environment
from ._converters import to_dataframe_2d, to_pandas
from .model import MizerParams, MizerSim, _wrap_params, _wrap_sim


@dataclass(frozen=True)
class NorthSeaExample:
    """Convenience bundle for the built-in North Sea example datasets.

    Attributes:
        species_params: Species parameter table.
        interaction: Species interaction matrix.
        params: Wrapped ``MizerParams`` object for the built-in North Sea model.
        sim: Wrapped ``MizerSim`` object for the built-in North Sea simulation.
        species_params_gears: Optional gear-specific species parameter table
            when available in the installed `mizer` version.

    Examples:
        ```python
        import pymizer as mz

        north_sea = mz.load_north_sea()
        sim = north_sea.params.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)
        ```
    """

    species_params: pd.DataFrame
    interaction: pd.DataFrame
    params: MizerParams
    sim: MizerSim
    species_params_gears: pd.DataFrame | None = None


def list_datasets(env: MizerREnvironment | None = None) -> pd.DataFrame:
    """List datasets shipped with the R `mizer` package.

    Args:
        env: Optional shared R environment wrapper.

    Returns:
        A ``pandas.DataFrame`` with ``name`` and ``title`` columns.

    Examples:
        ```python
        import pymizer as mz

        datasets = mz.list_datasets()
        print(datasets.head())
        ```
    """
    env = env or get_environment()
    info = env.utils.data(package=env.package_name)
    results = info.rx2("results")
    frame = to_dataframe_2d(results)
    frame.columns = [str(col) for col in frame.columns]
    return frame[["Item", "Title"]].rename(columns={"Item": "name", "Title": "title"})


def load_dataset(name: str, env: MizerREnvironment | None = None) -> Any:
    """Load a built-in `mizer` dataset and convert it to a Python-friendly type.

    Args:
        name: Dataset name as reported by :func:`list_datasets`.
        env: Optional shared R environment wrapper.

    Returns:
        One of:

        - ``pandas.DataFrame`` for tabular datasets
        - :class:`pymizer.MizerParams` for ``MizerParams`` objects
        - :class:`pymizer.MizerSim` for ``MizerSim`` objects
        - a raw R-backed object for unsupported dataset classes

    Raises:
        MizerError: If the dataset name is unknown.

    Examples:
        ```python
        import pymizer as mz

        species = mz.load_dataset("NS_species_params")
        params = mz.load_dataset("NS_params")
        sim = mz.load_dataset("NS_sim")
        ```
    """
    env = env or get_environment()
    available = list_datasets(env)["name"].tolist()
    if name not in available:
        raise MizerError(
            f"Unknown mizer dataset '{name}'. Available datasets: {', '.join(available)}."
        )

    package_env = robjects.r["as.environment"](f"package:{env.package_name}")
    obj = robjects.r["get"](name, envir=package_env)
    cls = env.class_name(obj)

    if cls == "data.frame":
        return to_pandas(obj)
    if cls == "matrix":
        return to_dataframe_2d(obj)
    if cls == "MizerParams":
        return _wrap_params(obj, env)
    if cls == "MizerSim":
        return _wrap_sim(obj, env)
    return obj


def load_north_sea(env: MizerREnvironment | None = None) -> NorthSeaExample:
    """Load the matching built-in North Sea example datasets together.

    Args:
        env: Optional shared R environment wrapper.

    Returns:
        A :class:`NorthSeaExample` bundle containing the most commonly used
        North Sea inputs and example model objects.

    Examples:
        ```python
        import pymizer as mz

        north_sea = mz.load_north_sea()
        print(north_sea.species_params.head())
        print(north_sea.params.biomass())
        ```
    """
    env = env or get_environment()
    species_params = load_dataset("NS_species_params", env=env)
    interaction = load_dataset("NS_interaction", env=env)
    params = load_dataset("NS_params", env=env)
    sim = load_dataset("NS_sim", env=env)

    species_params_gears = None
    available = list_datasets(env)["name"].tolist()
    if "NS_species_params_gears" in available:
        species_params_gears = load_dataset("NS_species_params_gears", env=env)

    return NorthSeaExample(
        species_params=species_params,
        interaction=interaction,
        params=params,
        sim=sim,
        species_params_gears=species_params_gears,
    )
