from __future__ import annotations

import pandas as pd
import pytest

import pymizer._bridge as bridge
from pymizer import load_dataset, new_multispecies_params, new_single_species_params, runtime_diagnostics
from pymizer._bridge import MizerError, MizerREnvironment


class _UnusedEnv:
    def call(self, *args, **kwargs):  # pragma: no cover - should never be reached
        raise AssertionError("validation should fail before any R call")


def test_runtime_diagnostics_reports_rpy2_initialisation_failure(monkeypatch):
    monkeypatch.setattr(bridge, "_ENV", None)
    monkeypatch.setattr(bridge, "_RPY2_IMPORT_ERROR", RuntimeError("simulated import failure"))

    diagnostics = runtime_diagnostics()

    assert diagnostics["rpy2_import_ok"] is False
    assert diagnostics["compatibility"] is False
    assert diagnostics["issues"] == ["rpy2 could not be imported or initialised."]
    assert diagnostics["rpy2_import_error"] == "simulated import failure"


def test_mizer_environment_raises_when_package_is_unavailable(monkeypatch):
    def fake_importr(package_name: str):
        if package_name == "mizer":
            raise RuntimeError("package not installed")
        return object()

    monkeypatch.setattr(bridge, "_RPY2_IMPORT_ERROR", None)
    monkeypatch.setattr(bridge, "importr", fake_importr)

    with pytest.raises(MizerError, match="Could not load the R bridge for pymizer"):
        MizerREnvironment()


def test_load_dataset_rejects_unknown_dataset_name():
    with pytest.raises(MizerError, match="Unknown mizer dataset 'definitely_not_a_dataset'"):
        load_dataset("definitely_not_a_dataset")


def test_new_multispecies_params_rejects_non_dataframe_species_params():
    with pytest.raises(TypeError, match="species_params must be a pandas.DataFrame"):
        new_multispecies_params(species_params=[{"species": "Cod"}], env=_UnusedEnv())


def test_new_multispecies_params_rejects_wrong_interaction_type():
    species = pd.DataFrame({"species": ["Cod", "Haddock"], "w_max": [1.0, 2.0]})

    with pytest.raises(TypeError, match="interaction must be a pandas.DataFrame, a numpy.ndarray, or None"):
        new_multispecies_params(species_params=species, interaction=[[1.0, 0.0], [0.0, 1.0]], env=_UnusedEnv())


def test_new_single_species_params_rejects_multiple_rows():
    species = pd.DataFrame({"species": ["Cod", "Haddock"], "w_max": [1.0, 2.0]})

    with pytest.raises(ValueError, match="requires exactly one row"):
        new_single_species_params(species_params=species, env=_UnusedEnv())


def test_set_rate_functions_rejects_unknown_entries():
    import pymizer as mz

    params = mz.new_community_params(no_w=20)

    with pytest.raises(ValueError, match="Unknown rate-function entries"):
        params.set_rate_functions(NotARealEntry="constantRDD")


def test_set_rate_functions_rejects_missing_r_function():
    import pymizer as mz

    params = mz.new_community_params(no_w=20)

    with pytest.raises(ValueError, match="was not found in the active R session"):
        params.set_rate_functions(RDD="definitely_not_an_r_function")
