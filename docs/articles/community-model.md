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
