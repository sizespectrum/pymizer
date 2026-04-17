# Model API

The model API combines constructor functions with two wrapper classes:
`MizerParams` for configured models and `MizerSim` for projection results.

## Constructors

- `new_community_params()`
- `new_multispecies_params()`
- `new_single_species_params()`
- `read_params()`

## Common `MizerParams` Methods

- state inspection: `initial_n()`, `initial_n_resource()`, `biomass()`,
  `abundance()`, `ssb()`
- size-resolved rates: `pred_rate()`, `pred_mort()`, `feeding_level()`,
  `diet()`, `trophic_level()`, `pred_kernel()`
- indicators: `mean_weight()`, `mean_max_weight()`,
  `proportion_of_large_fish()`, `community_slope()`
- parameter editing: `set_interaction()`, `set_resource()`,
  `set_initial_values()`, `set_metadata()`, `set_reproduction()`,
  `set_search_volume()`, `set_max_intake_rate()`, `set_metabolic_rate()`,
  `set_pred_kernel()`
- steady-state workflows: `project_to_steady()`, `steady()`,
  `steady_single_species()`
- simulation: `project()`

## Common `MizerSim` Methods

- projection summaries: `times()`, `biomass()`, `abundance()`, `yield_()`,
  `ssb()`
- state and rate diagnostics: `initial_n()`, `initial_n_resource()`,
  `pred_rate()`, `pred_mort()`, `feeding_level()`, `f_mort()`, `f_mort_gear()`
- ecological summaries: `diet()`, `growth_curves()`, `trophic_level()`,
  `trophic_level_by_species()`

## Editing Workflow

The editing methods mirror the `mizer` design: they do not mutate the current
object in place. Instead they return a new `MizerParams` wrapper with the
updated R object inside it.

Typical usage looks like:

```python
interaction = params.interaction_matrix()
interaction.iloc[0, 1] = 0.0

updated = params.set_interaction(interaction)
sim = updated.project(t_max=2, dt=0.1, t_save=1, effort=0, progress_bar=False)
```

## Steady-State Workflow

The wrapper exposes both lower-level and higher-level steady-state helpers:

- `project_to_steady()` searches for convergence under the current dynamics
- `steady()` applies the more opinionated `mizer::steady()` workflow
- `steady_single_species()` solves selected species against the current rates

## Filtering And Return Types

Many summary methods accept arguments such as `species=`, `min_w=`, `max_w=`,
`min_l=`, and `max_l=`. In general:

- time-by-species summaries return `pandas.DataFrame`
- spectra and size-resolved arrays return `xarray.DataArray`
- one-dimensional indicators return `float` or `pandas.Series`

## Generated API Pages

For full signatures, docstrings, and class reference pages, see:

- [MizerParams](../api/MizerParams.qmd)
- [MizerSim](../api/MizerSim.qmd)
- [new_community_params](../api/new_community_params.qmd)
- [new_multispecies_params](../api/new_multispecies_params.qmd)
- [new_single_species_params](../api/new_single_species_params.qmd)
- [read_params](../api/read_params.qmd)
