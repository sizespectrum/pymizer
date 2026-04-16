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
  `diet()`, `trophic_level()`
- indicators: `mean_weight()`, `mean_max_weight()`,
  `proportion_of_large_fish()`, `community_slope()`
- simulation: `project()`

## Common `MizerSim` Methods

- projection summaries: `times()`, `biomass()`, `abundance()`, `yield_()`,
  `ssb()`
- state and rate diagnostics: `initial_n()`, `initial_n_resource()`,
  `pred_rate()`, `pred_mort()`, `feeding_level()`, `f_mort()`, `f_mort_gear()`
- ecological summaries: `diet()`, `growth_curves()`, `trophic_level()`,
  `trophic_level_by_species()`

## Filtering And Return Types

Many summary methods accept arguments such as `species=`, `min_w=`, `max_w=`,
`min_l=`, and `max_l=`. In general:

- time-by-species summaries return `pandas.DataFrame`
- spectra and size-resolved arrays return `xarray.DataArray`
- one-dimensional indicators return `float` or `pandas.Series`

::: pymizer.model
