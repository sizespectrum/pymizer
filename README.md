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

## Development install

```bash
pip install -e ./python
```

## Documentation

The Python package has a MkDocs-based documentation site under `python/docs/`.

```bash
python/.venv/bin/pip install -e './python[docs]'
python/.venv/bin/mkdocs serve -f python/mkdocs.yml
```

To publish the site to GitHub Pages from your local machine:

```bash
cd python
mkdocs gh-deploy
```
