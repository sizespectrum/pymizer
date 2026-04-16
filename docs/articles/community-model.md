# Community Model

This example mirrors the lightest-weight path through the wrapper: create a
community model in Python, run a projection in R through `mizer`, and bring the
results back into Python objects.

## Create And Project

```python
import pymizer as mz

params = mz.new_community_params(no_w=20)
sim = params.project(
    t_max=5,
    dt=0.1,
    t_save=1,
    progress_bar=False,
)
```

## Inspect Outputs

```python
times = sim.times()
biomass = sim.biomass()
abundance = sim.abundance()
resource = sim.n_resource()
initial_n = params.initial_n()
initial_resource = params.initial_n_resource()
pred_rate = sim.pred_rate()
```

The returned objects are chosen to feel natural in Python:

- `times` is a NumPy array
- `biomass` and `abundance` are labelled `pandas.DataFrame` objects
- `resource` is an `xarray.DataArray` by default
- `initial_n` and `pred_rate` are labelled `xarray.DataArray` objects
- `initial_resource` is a `pandas.Series`

## Focus On A Size Range

The high-level summary methods can also be narrowed to a size range without
leaving Python:

```python
community_biomass = sim.biomass(min_w=1, max_w=1000)
community_abundance = sim.abundance(min_w=1, max_w=1000)
mean_weight = params.mean_weight(min_w=1, max_w=1000)
large_fish = params.proportion_of_large_fish(threshold_w=100)
```

That makes it easy to move between broad summaries and size-resolved arrays in
the same notebook.

## Edit And Reuse A Model

The wrapper preserves the `mizer` pattern where parameter edits return a new
model object:

```python
edited = params.set_metadata(
    title="Community demo",
    description="Edited from Python",
)

steady_ready = edited.set_initial_values(sim)
```

For more structural changes, inspect the current values first and then set an
updated copy:

```python
search_vol = params.search_volume(as_xarray=False).copy()
search_vol[:] = search_vol * 1.05

retuned = params.set_search_volume(search_vol)
```

This pattern also applies to `set_interaction()`, `set_reproduction()`,
`set_max_intake_rate()`, `set_metabolic_rate()`, and `set_pred_kernel()`.

## Steady-State Helpers

For steady-state-oriented workflows, `pymizer` exposes the `mizer` helpers
directly:

```python
steady_params = params.project_to_steady(
    t_per=0.5,
    t_max=0.5,
    dt=0.1,
    progress_bar=False,
    info_level=0,
)
```

For larger packaged models such as `NS_params`, you can also use:

```python
ns_params = mz.load_dataset("NS_params")
ns_steady = ns_params.steady(
    t_per=1.5,
    t_max=1.5,
    dt=0.1,
    progress_bar=False,
    info_level=0,
)
```

## Example Biomass Output

The smoke test for `pymizer` currently produces output shaped like this:

```text
species     Community
time
0        34926.721959
1        46146.578715
2        50503.969482
3        52101.198790
4        52906.953622
5        53493.609873
```

## Notes

- The model construction and projection are still performed by the R `mizer`
  package.
- The Python layer mainly handles conversion, object wrapping, and ergonomics.
- When debugging environment problems, it is worth checking both Python and R
  package availability.
