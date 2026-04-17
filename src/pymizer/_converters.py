from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from rpy2 import robjects
from rpy2.robjects import conversion, default_converter, numpy2ri, pandas2ri
from rpy2.robjects.vectors import FloatVector, ListVector, StrVector


def _active_conversion():
    """Return the currently active rpy2 conversion object."""
    return conversion.get_conversion()


def to_r(value: Any) -> Any:
    """Convert a Python value to an R object using rpy2 converters."""
    with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
        return _active_conversion().py2rpy(value)


def to_numpy(value: Any) -> np.ndarray:
    """Convert an R vector or array to a numpy array."""
    with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
        converted = _active_conversion().rpy2py(value)
    return np.asarray(converted)


def to_pandas(value: Any) -> pd.DataFrame:
    """Convert an R data frame-like object to pandas."""
    with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
        converted = _active_conversion().rpy2py(value)
    if isinstance(converted, pd.DataFrame):
        return converted
    return pd.DataFrame(converted)


def to_dataframe_2d(value: Any, index_name: str | None = None, column_name: str | None = None) -> pd.DataFrame:
    """Convert an R matrix-like object with dimnames to a labelled pandas DataFrame."""
    data = np.array(value)
    if data.ndim != 2:
        dims = robjects.r["dim"](value)
        if len(dims) == 2:
            data = data.reshape(tuple(int(dim) for dim in dims), order="F")
        else:
            raise ValueError("Expected a two-dimensional R object.")
    dn = dimnames(value)
    index = dn[0] if len(dn) > 0 else None
    columns = dn[1] if len(dn) > 1 else None
    frame = pd.DataFrame(data, index=index, columns=columns)
    if index_name is not None:
        frame.index.name = index_name
    if column_name is not None:
        frame.columns.name = column_name
    return frame


def dimnames(value: Any) -> list[list[str] | None]:
    """Extract dimnames from an R array."""
    names = robjects.r["dimnames"](value)
    if names is robjects.NULL:
        dims = robjects.r["dim"](value)
        return [None] * len(dims)
    result: list[list[str] | None] = []
    for item in names:
        if item is robjects.NULL:
            result.append(None)
        else:
            result.append([str(v) for v in item])
    return result


def named_numeric_vector(data: dict[str, float]) -> FloatVector:
    """Create a named R numeric vector."""
    vec = FloatVector(list(data.values()))
    vec.names = StrVector(list(data.keys()))
    return vec


def named_list(data: dict[str, Any]) -> ListVector:
    """Create a named R list from a Python dict."""
    return ListVector({key: to_r(value) for key, value in data.items()})


def to_xarray(value: Any, dim_names: list[str] | None = None) -> Any:
    """Convert an R array to xarray if xarray is installed."""
    try:
        import xarray as xr
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "xarray support is optional. Install pymizer with the 'xarray' extra "
            "to use this method."
        ) from exc

    data = to_numpy(value)
    dims = dim_names or []
    coords: dict[str, Any] = {}
    dn = dimnames(value)
    if not dims:
        dims = [f"dim_{idx}" for idx in range(data.ndim)]
    for idx, dim in enumerate(dims):
        labels = dn[idx] if idx < len(dn) else None
        if labels is not None:
            coords[dim] = labels
    return xr.DataArray(data, dims=dims, coords=coords)
