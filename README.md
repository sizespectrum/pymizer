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
- `rpy2` able to initialise against that R installation

## Release model

`pymizer` is intended to be published as a standalone Python package. The
Python package does not vendor R, and it does not try to install the R package
`mizer` for you. Instead, installation is split into two explicit steps:

1. install a supported R runtime and the R package `mizer`
2. install `pymizer` into your Python environment with `pip`

This keeps Python packaging predictable on PyPI while leaving R dependency
management with the tools that already handle it well.

## Installation

### Local developer setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Install the R dependency separately:

```r
install.packages("mizer")
```

### Virtualenv or venv

For a normal user install, create and activate an environment, then install
from PyPI or from a local checkout:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pymizer
```

### Conda or Mamba

If you manage R and Python together through Conda-style environments, install R
first, then install the R package and `pymizer` inside the same environment:

```bash
mamba create -n pymizer python=3.11 r-base r-essentials
mamba activate pymizer
python -m pip install pymizer
R -q -e 'install.packages("mizer", repos="https://cloud.r-project.org")'
```

### CI environments

In CI, set up R before installing Python dependencies so `rpy2` can discover
the correct runtime. A typical order is:

1. install Python
2. install R
3. install the R package `mizer`
4. install `pymizer` with `pip`
5. run tests or smoke checks

## Support matrix

The current packaging target is:

- Linux on Python 3.10 to 3.12 with a current CRAN R release
- macOS on Python 3.10 to 3.12 is expected to work with the same R setup
- Windows is not part of the supported matrix yet
- `mizer` 2.5.0 or later is required

The bridge performs runtime checks and reports the detected Python, `rpy2`, R,
and `mizer` versions to help diagnose unsupported combinations.

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
python -m pip install -e '.[dev]'
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

## Build distributions

Build both the source distribution and wheel locally before publishing:

```bash
python -m build
python -m twine check dist/*
```
