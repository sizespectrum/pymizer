# Datasets

The R package ships with several example datasets that are useful both for
testing the wrapper and for learning the `mizer` workflow from Python.

## List Available Datasets

```python
import pymizer as mz

datasets = mz.list_datasets()
print(datasets)
```

Typical entries include:

- `NS_species_params`
- `NS_species_params_gears`
- `NS_interaction`
- `NS_params`
- `NS_sim`

## Load A Dataset

```python
species = mz.load_dataset("NS_species_params")
interaction = mz.load_dataset("NS_interaction")
params = mz.load_dataset("NS_params")
sim = mz.load_dataset("NS_sim")
```

## Returned Python Types

`load_dataset()` maps dataset types to the closest Python representation:

- R `data.frame` -> `pandas.DataFrame`
- R matrix -> `pandas.DataFrame` with row and column labels
- `MizerParams` -> `pymizer.MizerParams`
- `MizerSim` -> `pymizer.MizerSim`

## North Sea Example

You can rebuild the North Sea parameter object from Python inputs:

```python
species = mz.load_dataset("NS_species_params")
interaction = mz.load_dataset("NS_interaction")

params = mz.new_multispecies_params(
    species_params=species,
    interaction=interaction,
)
```

This is often the most convenient starting point for notebooks because the
inputs are already in `pandas`.
