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
def test_params_read_only_analysis_methods():
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)

    biomass = params.biomass()
    abundance = params.abundance()
    ssb = params.ssb()
    feeding = params.feeding_level()
    pred_mort = params.pred_mort()
    growth = params.growth_curves()
    diet = params.diet()
    trophic = params.trophic_level()
    trophic_by_species = params.trophic_level_by_species()
    mean_max_weight = params.mean_max_weight()
    mean_weight = params.mean_weight()
    large_fish = params.proportion_of_large_fish()
    slope = params.community_slope()

    assert biomass.index.tolist() == ["Community"]
    assert abundance.index.tolist() == ["Community"]
    assert ssb.index.tolist() == ["Community"]
    assert feeding.dims == ("sp", "w")
    assert pred_mort.dims == ("sp", "w")
    assert growth.index.tolist() == ["Community"]
    assert growth.columns[0] == 0.0
    assert diet.dims == ("predator", "w", "prey")
    assert trophic.dims == ("sp", "w")
    assert trophic_by_species.index.tolist() == ["Community"]
    assert set(mean_max_weight.index.tolist()) == {"mmw_numbers", "mmw_biomass"}
    assert isinstance(mean_weight, float)
    assert isinstance(large_fish, float)
    assert {"slope", "intercept", "r2"} == set(slope.columns)


@pytest.mark.integration
def test_sim_extended_analysis_methods():
    pymizer = importlib.import_module("pymizer")
    species = pymizer.load_dataset("NS_species_params")
    interaction = pymizer.load_dataset("NS_interaction")
    params = pymizer.new_multispecies_params(species_params=species, interaction=interaction)
    sim = params.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)

    ssb = sim.ssb()
    yield_gear = sim.yield_gear()
    f_mort_gear = sim.f_mort_gear()
    pred_mort = sim.pred_mort()
    growth = sim.growth_curves()
    diet = sim.diet()
    trophic = sim.trophic_level()
    trophic_by_species = sim.trophic_level_by_species()
    mean_max_weight = sim.mean_max_weight()
    mean_weight = sim.mean_weight()
    large_fish = sim.proportion_of_large_fish()
    slope = sim.community_slope()

    assert ssb.index.tolist() == ["0", "1"]
    assert "Cod" in ssb.columns
    assert yield_gear.dims == ("time", "gear", "sp")
    assert f_mort_gear.dims == ("time", "gear", "sp", "w")
    assert pred_mort.dims == ("time", "sp", "w")
    assert "Cod" in growth.index
    assert growth.columns[0] == 0.0
    assert diet.dims == ("predator", "w", "prey")
    assert trophic.dims == ("sp", "w")
    assert "Cod" in trophic_by_species.index
    assert {"mmw_numbers", "mmw_biomass"} == set(mean_max_weight.columns)
    assert mean_weight.index.tolist() == ["0.0", "1.0"]
    assert large_fish.index.tolist() == ["0.0", "1.0"]
    assert {"slope", "intercept", "r2"} == set(slope.columns)


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
