# Get Started

## Requirements

To use `pymizer`, you need:

- Python 3.10 or later
- R installed and available on your path
- the `mizer` R package installed in your R library

## Install

For development from this repository:

```bash
python3 -m venv python/.venv
python/.venv/bin/pip install -e ./python
```

To install documentation tooling as well:

```bash
python/.venv/bin/pip install -e './python[docs]'
```

## First Simulation

The simplest way to confirm the bridge is working is to build a small community
model and run a short projection:

```python
import pymizer as mz

params = mz.new_community_params(no_w=20)
sim = params.project(
    t_max=5,
    dt=0.1,
    t_save=1,
    progress_bar=False,
)

print(sim.times())
print(sim.biomass())
```

Expected result:

- `sim.times()` returns a NumPy array of saved years
- `sim.biomass()` returns a labelled `pandas.DataFrame`

## Inspect The Model State

Once a model is loaded or created, you can inspect both the initial state and
the projected state without dropping into raw R objects:

```python
import pymizer as mz

params = mz.new_community_params(no_w=20)
sim = params.project(t_max=5, dt=0.1, t_save=1, progress_bar=False)

initial_n = params.initial_n()
initial_resource = params.initial_n_resource()
pred_rate = sim.pred_rate()
pred_mort = sim.pred_mort()
```

Typical return types are:

- `initial_n`: `xarray.DataArray` with dimensions `("sp", "w")`
- `initial_resource`: `pandas.Series` indexed by resource size
- `pred_rate`: `xarray.DataArray` with dimensions `("sp", "w_prey")`
- `pred_mort`: `xarray.DataArray` with dimensions `("time", "sp", "w")`

## Filter Common Summaries

Many summary methods accept the same species and size-range filters used by the
R package:

```python
import pymizer as mz

species = mz.load_dataset("NS_species_params")
interaction = mz.load_dataset("NS_interaction")
params = mz.new_multispecies_params(species_params=species, interaction=interaction)
sim = params.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)

cod_haddock_growth = params.growth_curves(species=["Cod", "Haddock"], max_age=5)
medium_biomass = sim.biomass(min_w=10, max_w=1000)
cod_haddock_weight = params.mean_weight(species=["Cod", "Haddock"], min_w=10, max_w=1000)
```

Supported filter arguments vary by method, but the common ones are:

- `species=`
- `min_w=` and `max_w=`
- `min_l=` and `max_l=`
- method-specific options such as `use_cutoff=`, `threshold_w=`, and `biomass=`

## Edit And Rerun Models

`pymizer` now supports the common “load, tweak, rerun” workflow directly from
Python. The editing methods follow the `mizer` pattern and return a new
`MizerParams` object rather than mutating the existing one.

```python
import pymizer as mz

params = mz.load_dataset("NS_params")

interaction = params.interaction_matrix()
interaction.iloc[0, 1] = 0.0

updated = (
    params
    .set_interaction(interaction)
    .set_metadata(title="North Sea example", description="Edited from Python")
)

sim = updated.project(t_max=2, dt=0.1, t_save=1, effort=0, progress_bar=False)
```

Useful editing methods include:

- `set_interaction()`
- `set_resource()`
- `set_initial_values()`
- `set_metadata()`
- `set_reproduction()`
- `set_search_volume()`
- `set_max_intake_rate()`
- `set_metabolic_rate()`
- `set_pred_kernel()`

## Steady-State Workflows

The wrapper also exposes the steady-state search helpers from `mizer`:

```python
import pymizer as mz

params = mz.load_dataset("NS_params")

steady_params = params.project_to_steady(
    t_per=1.0,
    t_max=5.0,
    dt=0.1,
    progress_bar=False,
    info_level=0,
)

single_species_params = params.steady_single_species(keep="biomass")
```

Available helpers are:

- `project_to_steady()` for the lower-level convergence search
- `steady()` for the higher-level workflow that holds reproduction and
  resource dynamics constant during the search
- `steady_single_species()` for solving selected species against the current
  rates

## Built-in Datasets

The wrapper can also load datasets shipped with the R package:

```python
import pymizer as mz

print(mz.list_datasets())

north_sea = mz.load_north_sea()
species = mz.load_dataset("NS_species_params")
interaction = mz.load_dataset("NS_interaction")
params = mz.load_dataset("NS_params")
sim = mz.load_dataset("NS_sim")
```

Returned types depend on the dataset:

- tabular datasets become `pandas.DataFrame`
- `NS_params` becomes `pymizer.MizerParams`
- `NS_sim` becomes `pymizer.MizerSim`

For most users, the easiest way to start with a realistic model is the bundled
North Sea helper:

```python
import pymizer as mz

north_sea = mz.load_north_sea()

params = north_sea.params
sim = north_sea.params.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)
```

This returns the matching built-in pieces together:

- `north_sea.species_params`
- `north_sea.interaction`
- `north_sea.params`
- `north_sea.sim`
- optionally `north_sea.species_params_gears` when available in the installed
  `mizer` version

## Build The Docs

This website is built with Quarto, and the API reference pages are generated by
`quartodoc` from the Python package source:

```bash
python3 -m pip install -e '.[docs]'
source .venv/bin/activate
quartodoc build --config docs/_quarto.yml
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto render docs
```

For live preview during editing:

```bash
source .venv/bin/activate
quartodoc build --config docs/_quarto.yml --watch
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto preview docs
```

`quartodoc build` reads [docs/_quarto.yml](/home/gustav/Git/pymizer/docs/_quarto.yml)
and writes the generated API pages into `docs/api/`. Quarto then renders the
hand-written `.md` and `.qmd` pages alongside that generated reference.

Those generated `docs/api/` files are local build artifacts, so rerun
`quartodoc build` whenever you need to preview, render, or publish the site.

Set `QUARTO_PYTHON` to the repository virtualenv so executable articles run
against the same Python, `rpy2`, and R-backed `pymizer` environment as the
library itself.

## Publish To GitHub Pages

Once the site has been rendered into `docs/_site/`, publish it using your preferred
Quarto or GitHub Pages workflow.
