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
    initial_n = params.initial_n()
    initial_n_resource = params.initial_n_resource()
    feeding = params.feeding_level()
    pred_rate = params.pred_rate()
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
    assert initial_n.dims == ("sp", "w")
    assert initial_n_resource.index.name == "w"
    assert feeding.dims == ("sp", "w")
    assert pred_rate.dims == ("sp", "w_prey")
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
def test_indicator_methods_accept_species_and_size_filters():
    pymizer = importlib.import_module("pymizer")
    species = pymizer.load_dataset("NS_species_params")
    interaction = pymizer.load_dataset("NS_interaction")
    params = pymizer.new_multispecies_params(species_params=species, interaction=interaction)
    sim = params.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)

    growth = params.growth_curves(species=["Cod", "Haddock"], max_age=5, percentage=True)
    biomass = params.biomass(min_w=10, max_w=1000)
    abundance = sim.abundance(min_w=10, max_w=1000)
    mean_weight = params.mean_weight(species=["Cod", "Haddock"], min_w=10, max_w=1000)
    large_fish = params.proportion_of_large_fish(
        species=["Cod", "Haddock"],
        threshold_w=1000,
        biomass_proportion=False,
        min_w=10,
        max_w=5000,
    )
    slope = params.community_slope(species=["Cod", "Haddock"], biomass=False, min_w=10, max_w=1000)
    mean_max_weight = sim.mean_max_weight(measure="numbers", species=["Cod", "Haddock"], min_w=10, max_w=1000)

    assert growth.index.tolist() == ["Cod", "Haddock"]
    assert "Cod" in biomass.index
    assert "Cod" in abundance.columns
    assert growth.columns[0] == 0.0
    assert growth.to_numpy().max() <= 100.0
    assert isinstance(mean_weight, float)
    assert isinstance(large_fish, float)
    assert {"slope", "intercept", "r2"} == set(slope.columns)
    assert mean_max_weight.index.tolist() == ["0.0", "1.0"]


@pytest.mark.integration
def test_sim_extended_analysis_methods():
    pymizer = importlib.import_module("pymizer")
    species = pymizer.load_dataset("NS_species_params")
    interaction = pymizer.load_dataset("NS_interaction")
    params = pymizer.new_multispecies_params(species_params=species, interaction=interaction)
    sim = params.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)

    ssb = sim.ssb()
    initial_n = sim.initial_n()
    initial_n_resource = sim.initial_n_resource()
    yield_gear = sim.yield_gear()
    f_mort_gear = sim.f_mort_gear()
    pred_rate = sim.pred_rate()
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
    assert initial_n.dims == ("sp", "w")
    assert initial_n_resource.index.name == "w"
    assert yield_gear.dims == ("time", "gear", "sp")
    assert f_mort_gear.dims == ("time", "gear", "sp", "w")
    assert pred_rate.dims == ("sp", "w_prey")
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
def test_parameter_editing_methods_return_new_params():
    pymizer = importlib.import_module("pymizer")
    species = pymizer.load_dataset("NS_species_params")
    interaction = pymizer.load_dataset("NS_interaction")
    params = pymizer.new_multispecies_params(species_params=species, interaction=interaction)

    original_interaction = params.interaction_matrix()
    modified_interaction = original_interaction.copy()
    modified_interaction.iloc[0, 1] = 0.0

    updated = params.set_interaction(modified_interaction)

    assert isinstance(updated, pymizer.MizerParams)
    assert params.interaction_matrix().iloc[0, 1] == original_interaction.iloc[0, 1]
    assert updated.interaction_matrix().iloc[0, 1] == 0.0


@pytest.mark.integration
def test_set_initial_values_metadata_and_resource():
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)
    sim = params.project(t_max=1, dt=0.1, t_save=1, progress_bar=False)

    updated_initial = params.set_initial_values(sim)
    updated_metadata = params.set_metadata(title="Community example", description="Test model")
    updated_resource = params.set_resource(resource_dynamics="resource_constant", balance=False)

    assert isinstance(updated_initial, pymizer.MizerParams)
    assert isinstance(updated_metadata, pymizer.MizerParams)
    assert isinstance(updated_resource, pymizer.MizerParams)
    assert not updated_initial.initial_n().equals(params.initial_n())
    assert updated_metadata.metadata()["title"] == "Community example"
    assert updated_metadata.metadata()["description"] == "Test model"
    assert updated_resource.project(t_max=0.5, dt=0.1, t_save=0.5, progress_bar=False).biomass().shape[0] == 2


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
