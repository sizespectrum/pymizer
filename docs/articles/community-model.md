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
```

The returned objects are chosen to feel natural in Python:

- `times` is a NumPy array
- `biomass` and `abundance` are labelled `pandas.DataFrame` objects
- `resource` is an `xarray.DataArray` by default

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
