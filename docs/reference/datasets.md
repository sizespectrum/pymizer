# Dataset API

The dataset helpers expose the example data that ships with the R `mizer`
package.

Use them to:

- discover available built-in datasets with `list_datasets()`
- load tabular inputs such as `NS_species_params` and `NS_interaction`
- load wrapped model objects such as `NS_params` and `NS_sim`
- load the commonly used North Sea example bundle with `load_north_sea()`

These helpers are a convenient way to try `pymizer` without preparing your own
input files first.

::: pymizer.datasets
