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

## Built-in Datasets

The wrapper can also load datasets shipped with the R package:

```python
import pymizer as mz

print(mz.list_datasets())

species = mz.load_dataset("NS_species_params")
interaction = mz.load_dataset("NS_interaction")
params = mz.load_dataset("NS_params")
sim = mz.load_dataset("NS_sim")
```

Returned types depend on the dataset:

- tabular datasets become `pandas.DataFrame`
- `NS_params` becomes `pymizer.MizerParams`
- `NS_sim` becomes `pymizer.MizerSim`

## Build The Docs

This website is built with MkDocs:

```bash
python/.venv/bin/mkdocs build -f python/mkdocs.yml
```

For live preview during editing:

```bash
python/.venv/bin/mkdocs serve -f python/mkdocs.yml
```

## Publish To GitHub Pages

`pymizer` is intended to publish its static documentation by pushing the built
site to the repository's `gh-pages` branch from a local environment.

From the `python/` directory:

```bash
mkdocs gh-deploy
```

This command builds the site and updates the `gh-pages` branch used by GitHub
Pages.
