# Get Started

## Requirements

To use `pymizer`, you need:

- Python 3.10 or later
- R installed and available on your path
- the `mizer` R package installed in your R library
- `rpy2` able to initialise against that R installation

## Packaging model

`pymizer` is published as a Python package, but it deliberately leaves R
dependency management to the user or environment manager. Installing `pymizer`
does not attempt to install the R package `mizer` automatically.

The recommended sequence is:

1. install R
2. install the R package `mizer`
3. install `pymizer` into the Python environment that should talk to that R
   runtime

## Install

For development from this repository:

```bash
python3 -m venv python/.venv
python/.venv/bin/python -m pip install --upgrade pip
python/.venv/bin/python -m pip install -e './python[dev]'
```

Install the R package separately:

```r
install.packages("mizer")
```

For a regular virtualenv or venv install:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pymizer
```

For Conda or Mamba environments:

```bash
mamba create -n pymizer python=3.11 r-base r-essentials
mamba activate pymizer
python -m pip install pymizer
R -q -e 'install.packages("mizer", repos="https://cloud.r-project.org")'
```

For CI environments, install Python and R first, then install `mizer`, and
only after that install `pymizer` with `pip`.

## Support Matrix

The current support target is:

- Linux with Python 3.10 to 3.12 and a current CRAN R release
- macOS with Python 3.10 to 3.12 is expected to work with the same setup
- Windows is not currently in the supported matrix
- `mizer` 2.5.0 or later

Use `runtime_diagnostics()` if you need to confirm what stack `pymizer`
detected on your machine.

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
python3 -m pip install -e '.[dev]'
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

## Build And Check Distributions

Before publishing, build both package formats and run the metadata checks:

```bash
python -m build
python -m twine check dist/*
```

## Publish To GitHub Pages

For the `pymizer` site, the simplest publish path is to let Quarto render the
site and push the output to the `gh-pages` branch for you.

First, make sure the GitHub repository is configured to serve Pages from the
`gh-pages` branch:

1. Open the repository on GitHub.
2. Go to `Settings` -> `Pages`.
3. Set the source to `Deploy from a branch`.
4. Choose the `gh-pages` branch and the `/ (root)` folder.

Then publish from your local checkout:

```bash
source .venv/bin/activate
quartodoc build --config docs/_quarto.yml
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto publish gh-pages docs
```

Quarto will:

- render the site from `docs/`
- create or update the `gh-pages` branch
- push the rendered `_site/` output to GitHub Pages

If you prefer to inspect the rendered site before publishing, render first and
then publish:

```bash
source .venv/bin/activate
quartodoc build --config docs/_quarto.yml
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto render docs
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto publish gh-pages docs
```

After the push completes, GitHub Pages will usually update the public site
within a minute or two.
