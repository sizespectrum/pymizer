# pymizer

`pymizer` is a small Python wrapper around the `mizer` R package.

The initial API focuses on the common workflow:

```python
import pymizer as mz

params = mz.new_multispecies_params(species_params=species_df, interaction=interaction_df)
sim = params.project(t_max=10, effort=0.0)
biomass = sim.biomass()

datasets = mz.list_datasets()
ns_species = mz.load_dataset("NS_species_params")
ns_params = mz.load_dataset("NS_params")
```

## Status

This is an early proof of concept. It currently aims to:

- create `MizerParams` objects from Python
- run simulations with `project()`
- extract common outputs as `pandas`, `numpy`, and `xarray`

Advanced `mizer` extension features such as custom rate functions are not yet
wrapped in a Python-native way.

## Requirements

- Python 3.10+
- R installed
- the `mizer` R package installed and loadable by R

## Diagnostics

If the bridge cannot start cleanly, you can inspect the detected runtime stack:

```python
import pymizer as mz

print(mz.runtime_diagnostics())
```

This reports:

- whether `rpy2` imported successfully
- detected versions of Python, `rpy2`, R, and `mizer`
- whether the environment passes the wrapper's compatibility checks
- any compatibility or startup issues found

## Development install

```bash
python -m pip install -e '.[docs]'
```

## Documentation

The documentation site is built with Quarto and `quartodoc`.

```bash
source .venv/bin/activate
quartodoc build --config docs/_quarto.yml
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto preview docs
```

The generated `docs/api/` reference pages are build artifacts and are not meant
to be committed. Regenerate them locally with `quartodoc build` before preview,
render, or publish.

To render the static site into `docs/_site/` from your local machine:

```bash
source .venv/bin/activate
quartodoc build --config docs/_quarto.yml
QUARTO_PYTHON="$(pwd)/.venv/bin/python" quarto render docs
```
