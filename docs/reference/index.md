# Reference Overview

The `pymizer` reference now has two layers:

- high-level guide pages in this `reference/` section
- generated API pages under [API Reference](../api/index.qmd), built from the
  package source with `quartodoc`

## Guide Pages

- [Model API](model.md): model constructors and wrapper classes
- [Dataset API](datasets.md): list and load packaged example datasets
- [R Bridge API](bridge.md): lower-level access to the embedded R environment
- [API Reference](../api/index.qmd): generated signatures and docstrings for the
  public Python surface

## Key Wrapper Surfaces

The current `pymizer` API is centred around three parts of the workflow:

- model construction with `new_community_params()`, `new_multispecies_params()`,
  `new_single_species_params()`, and `read_params()`
- simulation with `MizerParams.project()`
- inspection through `MizerParams` and `MizerSim` methods that return
  `pandas`, `numpy`, or `xarray` objects

## Common Return Types

- tabular summaries such as `sim.biomass()` and `sim.abundance()` return
  `pandas.DataFrame`
- state spectra such as `params.initial_n()` and `sim.pred_rate()` return
  `xarray.DataArray` by default
- one-dimensional indicator outputs such as `params.mean_weight()` or
  `params.initial_n_resource()` return Python scalars or `pandas.Series`

## Common Analysis Patterns

- use `params.initial_n()` and `params.initial_n_resource()` to inspect the
  starting state before a projection
- use `sim.biomass()`, `sim.abundance()`, and `sim.ssb()` for time-by-species
  summaries
- use `sim.pred_rate()`, `sim.pred_mort()`, `sim.feeding_level()`, and
  `sim.diet()` for size-resolved diagnostics
- use filter arguments such as `species=`, `min_w=`, `max_w=`, `min_l=`, and
  `max_l=` on supported summary methods to stay within Python for common
  exploratory analysis

## Design Notes

The public API deliberately stays narrower than the full R package:

- constructor functions are exposed at top level
- `MizerParams` and `MizerSim` provide the most common workflows
- raw R objects remain accessible through the `.r` property when needed
- advanced workflows can use `read_rds()`, `MizerREnvironment.eval()`, and
  `MizerParams.set_rate_functions()` when the core wrapper surface is not
  quite enough

For full signatures and class pages, use the generated
[API Reference](../api/index.qmd).
