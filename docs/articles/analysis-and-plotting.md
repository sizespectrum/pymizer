# Analysis And Plotting

This article shows a notebook-style analysis workflow built around the bundled
North Sea example. The emphasis is on staying in Python-native objects for
summaries and then plotting them directly with `matplotlib`.

## Load The Example

```python
import pymizer as mz

north_sea = mz.load_north_sea()
params = north_sea.params

sim = params.project(
    t_max=2,
    dt=0.1,
    t_save=1,
    effort=0,
    progress_bar=False,
)
```

## Build Tidy Summaries

The time-by-species summaries come back as `pandas.DataFrame`, which makes them
easy to reshape for plotting libraries:

```python
biomass = sim.biomass()
yield_df = sim.yield_()

biomass_long = (
    biomass
    .reset_index()
    .melt(id_vars="time", var_name="species", value_name="biomass")
)
```

That gives a table with one row per time/species combination, ready for
plotting or grouped analysis.

## Size-Resolved Diagnostics

For size-resolved outputs, `xarray` works well directly:

```python
pred_mort = sim.pred_mort()
diet = sim.diet()

cod_pred_mort = pred_mort.sel(sp="Cod")
cod_diet = diet.sel(predator="Cod")
```

Typical use cases are:

- selecting one species with `.sel(sp="Cod")`
- slicing along time or size dimensions
- converting a smaller slice to a DataFrame with `.to_dataframe()`

## Example Plots

Because `matplotlib` is a package dependency, a simple workflow is:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 4))
biomass[["Cod", "Haddock", "Herring"]].plot(ax=ax)
ax.set_ylabel("Biomass")
ax.set_title("North Sea Biomass Through Time")
fig.tight_layout()
```

For a size-resolved plot:

```python
fig, ax = plt.subplots(figsize=(8, 4))
cod_pred_mort.plot(ax=ax)
ax.set_title("Cod Predation Mortality By Size")
fig.tight_layout()
```

## Indicators For Quick Comparison

The scalar and vector indicators are useful for concise summaries:

```python
large_fish = sim.proportion_of_large_fish()
mean_weight = sim.mean_weight()
community_slope = sim.community_slope()
```

These give:

- `large_fish`: `pandas.Series`
- `mean_weight`: `pandas.Series`
- `community_slope`: `pandas.DataFrame`

They work well for quick before/after comparisons when you edit parameters and
rerun the model.

## Runnable Example

A runnable version of this workflow is included in
[examples/north_sea_analysis.py](/home/gustav/Git/mizer/python/examples/north_sea_analysis.py).

The script:

- loads the North Sea bundle
- runs a short projection
- prints a few tidy summaries
- saves PNG plots into `examples/output`
