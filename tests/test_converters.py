from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from rpy2 import robjects
from rpy2.robjects.vectors import FloatVector, ListVector

from pymizer._converters import dimnames, named_list, named_numeric_vector, to_dataframe_2d, to_numpy, to_r, to_xarray


def test_to_r_and_to_numpy_round_trip_dataframe():
    frame = pd.DataFrame({"species": ["Cod", "Haddock"], "w_max": [1.0, 2.0]})

    converted = to_r(frame)
    result = to_numpy(converted.rx2("w_max"))

    assert list(robjects.r["colnames"](converted)) == ["species", "w_max"]
    assert np.allclose(result, np.array([1.0, 2.0]))


def test_to_dataframe_2d_preserves_dimnames():
    matrix = robjects.r(
        """
        x <- matrix(c(1, 2, 3, 4), nrow = 2, ncol = 2)
        dimnames(x) <- list(c("Cod", "Haddock"), c("Cod", "Haddock"))
        x
        """
    )

    frame = to_dataframe_2d(matrix, index_name="predator", column_name="prey")

    assert frame.index.tolist() == ["Cod", "Haddock"]
    assert frame.columns.tolist() == ["Cod", "Haddock"]
    assert frame.index.name == "predator"
    assert frame.columns.name == "prey"
    assert frame.loc["Cod", "Cod"] == pytest.approx(1.0)


def test_dimnames_extracts_null_entries():
    array = robjects.r.array(FloatVector([1.0, 2.0]), dim=robjects.IntVector([2]))

    names = dimnames(array)

    assert names == [None]


def test_named_numeric_vector_sets_names():
    vec = named_numeric_vector({"Cod": 1.0, "Haddock": 0.5})

    assert list(vec.names) == ["Cod", "Haddock"]
    assert list(vec) == [1.0, 0.5]


def test_named_list_converts_nested_python_values():
    result = named_list({"species": ["Cod", "Haddock"], "effort": np.array([1.0, 0.5])})

    assert isinstance(result, ListVector)
    assert list(result.names) == ["species", "effort"]
    assert list(robjects.r["unlist"](result.rx2("species"))) == ["Cod", "Haddock"]
    assert list(result.rx2("effort")) == [1.0, 0.5]


def test_to_xarray_uses_dimnames_as_coordinates():
    matrix = robjects.r(
        """
        x <- matrix(c(1, 2, 3, 4), nrow = 2, ncol = 2)
        dimnames(x) <- list(c("Cod", "Haddock"), c("small", "large"))
        x
        """
    )

    result = to_xarray(matrix, ["sp", "w"])

    assert result.dims == ("sp", "w")
    assert result.coords["sp"].to_numpy().tolist() == ["Cod", "Haddock"]
    assert result.coords["w"].to_numpy().tolist() == ["small", "large"]
    assert result.sel(sp="Haddock", w="large").item() == pytest.approx(4.0)
