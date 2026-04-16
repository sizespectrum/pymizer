# North Sea Model

This article shows the recommended first workflow for a realistic built-in
example model in `pymizer`: load the bundled North Sea datasets, inspect the
inputs, run a short projection, and explore the results in Python-native data
structures.

## Load The Bundle

```python
import pymizer as mz

north_sea = mz.load_north_sea()

species = north_sea.species_params
interaction = north_sea.interaction
params = north_sea.params
sim = north_sea.sim
```

The bundle keeps the matching example pieces together:

- `species`: `pandas.DataFrame`
- `interaction`: `pandas.DataFrame`
- `params`: `pymizer.MizerParams`
- `sim`: `pymizer.MizerSim`

If available in the installed `mizer` version, the bundle also includes
`north_sea.species_params_gears`.

## Inspect The Inputs

The bundled North Sea inputs are immediately usable from Python:

```python
print(species.head(2))
print(interaction.iloc[:2, :2])
```

Typical output looks like:

```text
   species  w_max  w_mat    beta  sigma   k_vb         R_max  w_inf
1    Sprat   33.0     13   51076    0.8  0.681  7.380000e+11   33.0
2  Sandeel   36.0      4  398849    1.9  1.000  4.100000e+11   36.0

            Sprat   Sandeel
Sprat    0.729129  0.034084
Sandeel  0.034084  0.681199
```

## Inspect The Built-In Model

The bundled `params` object is already a wrapped `MizerParams`, so you can
inspect the current state immediately:

```python
print(params.biomass().head())
```

Example:

```text
Sprat      4.054293e+11
Sandeel    5.589441e+12
N.pout     4.762654e+11
Herring    1.467576e+12
Dab        1.056360e+10
```

## Run A Short Projection

You can project the bundled model forward from Python:

```python
short_sim = params.project(
    t_max=1,
    dt=0.1,
    t_save=1,
    effort=0,
    progress_bar=False,
)

print(short_sim.biomass().iloc[:2, :3])
```

Example output:

```text
species         Sprat       Sandeel        N.pout
time
1967     5.083638e+10  3.652370e+12  3.698381e+11
1968     5.569864e+10  3.737535e+12  3.929766e+11
```

## Explore The Results

The North Sea model is large enough to make the richer analysis methods useful:

```python
diet = short_sim.diet()
pred_mort = short_sim.pred_mort()
large_fish = short_sim.proportion_of_large_fish()
```

Typical return types are:

- `short_sim.biomass()`: `pandas.DataFrame`
- `short_sim.diet()`: `xarray.DataArray`
- `short_sim.pred_mort()`: `xarray.DataArray`
- `short_sim.proportion_of_large_fish()`: `pandas.Series`

## Edit And Rerun

Because the bundled object is a normal `MizerParams`, it works with the Phase 3
editing surface as well:

```python
edited = params.set_metadata(
    title="North Sea example",
    description="Edited from Python",
)

edited_sim = edited.project(t_max=1, dt=0.1, t_save=1, effort=0, progress_bar=False)
```

This makes the bundled North Sea model a good starting point for notebooks,
tests, and examples.

For a notebook-style follow-up that reshapes outputs and adds plotting,
see [Analysis And Plotting](analysis-and-plotting.md).
