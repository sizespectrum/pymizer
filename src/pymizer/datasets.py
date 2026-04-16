from __future__ import annotations

from typing import Any

import pandas as pd
from rpy2 import robjects

from ._bridge import MizerError, MizerREnvironment, get_environment
from ._converters import to_dataframe_2d, to_pandas
from .model import MizerParams, MizerSim, _wrap_params, _wrap_sim


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
