# pymizer

`pymizer` brings core `mizer` workflows into Python while continuing to rely on
the mature R implementation for the actual model logic and numerical solvers.

The current wrapper focuses on the common interactive workflow:

1. load or construct a `MizerParams` model
2. run a projection with `project()`
3. pull results back into Python as `pandas`, `numpy`, or `xarray`

```python
import pymizer as mz

params = mz.new_community_params(no_w=20)
sim = params.project(t_max=5, dt=0.1, t_save=1, progress_bar=False)

biomass = sim.biomass()
times = sim.times()
```

## Why a Python wrapper?

`mizer` already has a rich R API and excellent package documentation. The goal
of `pymizer` is not to replace that ecosystem, but to make it easier to:

- use `mizer` from Python notebooks and analysis scripts
- move simulation outputs directly into the Python data stack
- access packaged example datasets from Python
- keep the Python interface close to the mental model of the R package

## Current scope

The wrapper currently supports:

- constructing models with `new_multispecies_params()`,
  `new_single_species_params()`, and `new_community_params()`
- loading saved models with `read_params()`
- round-tripping generic `.rds` files with `read_rds()`
- running simulations through `MizerParams.project()`
- accessing common outputs from `MizerSim`
- quick notebook helpers such as `MizerSim.biomass_tidy()` and
  `MizerSim.plot_biomass()`
- listing and loading built-in `mizer` datasets

Advanced features are still intentionally narrow, but `pymizer` now includes
controlled access to the `rates_funcs` slot, generic RDS helpers, and a
temporary-environment `eval()` helper on the bridge for mixed Python/R work.

## Site Guide

- [Get Started](get-started.md) shows installation and the first simulation.
- [Articles](articles/community-model.qmd) provides worked examples.
- [Reference Overview](reference/index.md) summarises the public Python API.
- [API Reference](api/index.qmd) is generated from the package source with `quartodoc`.
- [News](news.md) summarises recent changes to the wrapper.
