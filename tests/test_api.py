from __future__ import annotations

import importlib

import pytest


def test_public_api_imports():
    module = importlib.import_module("pymizer")
    assert hasattr(module, "CompatibilityReport")
    assert hasattr(module, "MizerParams")
    assert hasattr(module, "MizerSim")
    assert hasattr(module, "evaluate_versions")
    assert hasattr(module, "list_datasets")
    assert hasattr(module, "load_dataset")
    assert hasattr(module, "new_multispecies_params")
    assert hasattr(module, "runtime_diagnostics")
    assert hasattr(module, "validate_species_params")


@pytest.mark.integration
def test_community_model_projection():
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)
    sim = params.project(t_max=1, dt=0.1, t_save=1, progress_bar=False)
    biomass = sim.biomass()

    assert list(sim.times()) == [0.0, 1.0]
    assert biomass.shape == (2, 1)
    assert biomass.columns.tolist() == ["Community"]


@pytest.mark.integration
def test_load_builtin_datasets():
    pymizer = importlib.import_module("pymizer")

    datasets = pymizer.list_datasets()
    species = pymizer.load_dataset("NS_species_params")
    params = pymizer.load_dataset("NS_params")

    assert "NS_species_params" in datasets["name"].tolist()
    assert "species" in species.columns
    assert isinstance(params, pymizer.MizerParams)


@pytest.mark.integration
def test_environment_versions():
    pymizer = importlib.import_module("pymizer")
    versions = pymizer.get_environment().versions()

    assert "pymizer" in versions
    assert "rpy2" in versions
    assert "R" in versions
    assert "mizer" in versions


@pytest.mark.integration
def test_runtime_diagnostics_success():
    pymizer = importlib.import_module("pymizer")
    diagnostics = pymizer.runtime_diagnostics()

    assert diagnostics["rpy2_import_ok"] is True
    assert diagnostics["compatibility"] is True
    assert "versions" in diagnostics
    assert "issues" in diagnostics
