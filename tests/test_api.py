from __future__ import annotations

import importlib

import pytest


def test_public_api_imports():
    module = importlib.import_module("pymizer")
    assert hasattr(module, "CompatibilityReport")
    assert hasattr(module, "MizerParams")
    assert hasattr(module, "MizerSim")
    assert hasattr(module, "NorthSeaExample")
    assert hasattr(module, "evaluate_versions")
    assert hasattr(module, "list_datasets")
    assert hasattr(module, "load_dataset")
    assert hasattr(module, "load_north_sea")
    assert hasattr(module, "new_multispecies_params")
    assert hasattr(module, "read_rds")
    assert hasattr(module, "runtime_diagnostics")
    assert hasattr(module, "validate_species_params")


@pytest.mark.integration
def test_runtime_diagnostics_reports_ready_bridge():
    pymizer = importlib.import_module("pymizer")

    diagnostics = pymizer.runtime_diagnostics()

    assert diagnostics["rpy2_import_ok"] is True
    assert diagnostics["compatibility"] is True
    assert diagnostics["versions"]["mizer"]


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
    north_sea = pymizer.load_north_sea()

    assert "NS_species_params" in datasets["name"].tolist()
    assert "species" in species.columns
    assert isinstance(params, pymizer.MizerParams)
    assert isinstance(north_sea, pymizer.NorthSeaExample)
    assert "species" in north_sea.species_params.columns
    assert "Cod" in north_sea.interaction.columns
    assert isinstance(north_sea.params, pymizer.MizerParams)
    assert isinstance(north_sea.sim, pymizer.MizerSim)


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
def test_rate_functions_can_be_inspected_and_updated():
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)

    original = params.rate_functions()
    updated = params.set_rate_functions(RDD="BevertonHoltRDD")

    assert original["RDD"] == "constantRDD"
    assert updated.rate_functions()["RDD"] == "BevertonHoltRDD"
    assert params.rate_functions()["RDD"] == "constantRDD"


@pytest.mark.integration
def test_rds_round_trip_and_raw_r_evaluation(tmp_path):
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)
    sim = params.project(t_max=1, dt=0.1, t_save=1, progress_bar=False)
    params_path = tmp_path / "params.rds"
    sim_path = tmp_path / "sim.rds"

    params.save_rds(params_path)
    sim.save_rds(sim_path)

    loaded_params = pymizer.read_rds(params_path)
    loaded_sim = pymizer.read_rds(sim_path)
    evaluated = pymizer.get_environment().eval(
        """
        list(
          params_class = class(params)[1],
          sim_class = class(sim)[1],
          final_time = max(getTimes(sim))
        )
        """,
        params=loaded_params,
        sim=loaded_sim,
    )

    assert isinstance(loaded_params, pymizer.MizerParams)
    assert isinstance(loaded_sim, pymizer.MizerSim)
    assert loaded_sim.times().tolist() == [0.0, 1.0]
    assert evaluated.rx2("params_class")[0] == "MizerParams"
    assert evaluated.rx2("sim_class")[0] == "MizerSim"
    assert float(evaluated.rx2("final_time")[0]) == pytest.approx(1.0)


@pytest.mark.integration
def test_reproduction_and_rate_setters():
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)

    original_maturity = params.maturity(as_xarray=False)
    maturity = original_maturity.copy()
    maturity[:, -1] = 0.0
    search_vol = params.search_volume(as_xarray=False).copy()
    search_vol[:] = search_vol * 1.1
    intake_max = params.max_intake_rate(as_xarray=False).copy()
    intake_max[:] = intake_max * 0.9
    metab = params.metabolic_rate(as_xarray=False).copy()
    metab[:] = metab * 1.05
    pred_kernel = params.pred_kernel(as_xarray=False).copy()
    pred_kernel[:, -1, 0] = 0.0

    updated_reproduction = params.set_reproduction(maturity=maturity)
    updated_search = params.set_search_volume(search_vol)
    updated_intake = params.set_max_intake_rate(intake_max)
    updated_kernel = params.set_pred_kernel(pred_kernel)
    updated_metab = params.set_metabolic_rate(metab)

    assert isinstance(updated_reproduction, pymizer.MizerParams)
    assert isinstance(updated_search, pymizer.MizerParams)
    assert isinstance(updated_intake, pymizer.MizerParams)
    assert isinstance(updated_kernel, pymizer.MizerParams)
    assert isinstance(updated_metab, pymizer.MizerParams)
    assert updated_reproduction.maturity(as_xarray=False)[0, -1] == 0.0
    assert updated_search.search_volume(as_xarray=False)[0, 0] == pytest.approx(search_vol[0, 0])
    assert updated_intake.max_intake_rate(as_xarray=False)[0, 0] == pytest.approx(intake_max[0, 0])
    assert updated_kernel.pred_kernel(as_xarray=False)[0, -1, 0] == 0.0
    assert updated_metab.metabolic_rate(as_xarray=False)[0, 0] == pytest.approx(metab[0, 0])
    assert params.maturity(as_xarray=False)[0, -1] == pytest.approx(original_maturity[0, -1])


@pytest.mark.integration
def test_steady_state_workflows():
    pymizer = importlib.import_module("pymizer")
    params = pymizer.new_community_params(no_w=20)
    ns_params = pymizer.load_dataset("NS_params")

    projected = params.project_to_steady(t_per=0.5, t_max=0.5, dt=0.1, progress_bar=False, info_level=0)
    projected_sim = params.project_to_steady(
        t_per=0.5,
        t_max=0.5,
        dt=0.1,
        return_sim=True,
        progress_bar=False,
        info_level=0,
    )
    steady_params = ns_params.steady(t_per=1.5, t_max=1.5, dt=0.1, progress_bar=False, info_level=0)
    single_species = params.steady_single_species()

    assert isinstance(projected, pymizer.MizerParams)
    assert isinstance(projected_sim, pymizer.MizerSim)
    assert isinstance(steady_params, pymizer.MizerParams)
    assert isinstance(single_species, pymizer.MizerParams)
    assert projected.initial_n().dims == ("sp", "w")
    assert projected_sim.biomass().shape[0] >= 1
    assert steady_params.initial_n().dims == ("sp", "w")
    assert single_species.initial_n().dims == ("sp", "w")


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
