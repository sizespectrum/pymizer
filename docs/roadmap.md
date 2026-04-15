# Roadmap

This page tracks the planned development of `pymizer`, the Python wrapper for
the R `mizer` package.

The current package already supports:

- creating `MizerParams` wrappers from Python
- running `project()` through the R `mizer` package
- extracting common results as `pandas`, `numpy`, and `xarray`
- loading built-in `mizer` datasets from Python
- building a dedicated documentation website

The next stages should focus on turning the current proof of concept into a
more robust and maintainable bridge for real analysis workflows.

## Guiding Principles

- Keep the Python API close to the mental model of `mizer`, but make return
  types feel natural in Python.
- Prefer thin, reliable wrapping of stable R functionality over partial
  reimplementation in Python.
- Expand the public API in layers, starting with the most common scientific
  workflows.
- Treat packaging, testing, and documentation as product features, not polish.

## Phase 1: Stabilise The Core Wrapper

### Goals

- Make the existing wrapper reliable for day-to-day use.
- Reduce avoidable environment friction.
- Tighten the boundaries of the supported API.

### Work Items

- Add explicit version checks for compatible R, `mizer`, and `rpy2` versions.
- Improve startup diagnostics when R or the `mizer` package is unavailable.
- Standardise conversion helpers so all wrapped functions follow the same rules
  for `pandas`, `numpy`, and `xarray` outputs.
- Add lightweight validation helpers for constructor inputs such as
  `species_params` and interaction matrices.
- Improve object summaries so `MizerParams.summary()` and `MizerSim` reporting
  are more useful in notebooks.
- Add convenience methods for common save/load workflows on `MizerSim` as well
  as `MizerParams`.

## Phase 2: Expand High-Value Analysis Surface

### Goals

- Cover the most commonly used read-only `mizer` analysis functions.
- Make Python notebooks viable without frequent escapes into raw R objects.

### Priority Additions

- `MizerSim` accessors:
  - `ssb()`
  - `yield_gear()`
  - `f_mort_gear()`
  - `pred_mort()`
  - `diet()`
  - `growth_curves()`
- `MizerParams` accessors:
  - `initial_n()`
  - `initial_n_resource()`
  - `biomass()`
  - `feeding_level()`
  - `pred_rate()`
- indicator functions:
  - community slope
  - mean weight
  - proportion of large fish
  - trophic level outputs

## Phase 3: Parameter Editing And Model Manipulation

### Goals

- Support the common “load, tweak, rerun” workflow from Python.
- Preserve the immutability pattern used by `mizer`.

### Priority Additions

- `set_interaction()`
- `set_resource()`
- `set_reproduction()`
- `set_initial_values()`
- `set_metadata()`
- `set_pred_kernel()`
- `set_search_volume()`
- `set_max_intake_rate()`
- `set_metabolic_rate()`
- `project_to_steady()` if feasible through the current bridge design

## Phase 4: Better Dataset And Example Support

### Goals

- Make the wrapper easy to learn through real models and reproducible examples.

### Work Items

- Add richer helpers around built-in datasets, such as loading matching North
  Sea inputs together.
- Add example notebooks for:
  - community model
  - North Sea model
  - basic plotting and analysis in Python
- Add a helper to expose package example file paths if needed.
- Add a documented “recommended first workflow” that uses built-in example
  data only.

## Phase 5: Packaging And Distribution

### Goals

- Make installation predictable outside this repository.
- Clarify how Python and R dependencies should be managed together.

### Work Items

- Decide on the intended release model:
  - publish `pymizer` as a Python package only
  - or keep it as a repo-local companion package for now
- Add wheel and source distribution checks.
- Document installation strategies for:
  - local developer setup
  - virtualenv/venv
  - Conda or Mamba
  - CI environments
- Decide whether installation should attempt any automatic R package checks or
  remain fully manual.
- Add a minimal support matrix covering OS, Python version, and R version.

## Phase 6: Testing And Continuous Integration

### Goals

- Move from smoke tests to confidence-building coverage.

### Test Layers

- unit tests for conversion helpers and shape handling
- integration tests for live R bridge behaviour
- regression tests for built-in examples
- documentation build tests

## Phase 7: Plotting And Python-Native Ergonomics

### Goals

- Make output exploration feel more natural in the Python ecosystem.

### Possible Additions

- convenience plotting methods backed by `matplotlib`, `seaborn`, or `plotly`
- helper methods for converting outputs to tidy long-form `pandas`
- utility functions for common notebook display patterns
- optional integration with Jupyter-rich summaries for wrapped objects

## Phase 8: Advanced And Experimental Features

### Goals

- Explore whether more of `mizer`’s extension surface can be exposed from
  Python without creating fragile abstractions.

### Candidates

- support for more extension hooks and metadata
- controlled access to custom rate-function registration
- pass-through helpers for advanced users who need raw R evaluation
- helpers for serialising wrapper state in mixed Python/R workflows

## Recommended Near-Term Priorities

If development time is limited, the best next sequence is:

1. Stabilise the bridge and input validation.
2. Add the highest-value summary and indicator accessors.
3. Expand tests and CI coverage.
4. Publish example notebooks using the built-in datasets.
5. Add selected parameter-setting methods for iterative modelling workflows.

## Milestones

### Milestone A: Usable Beta

- clean install process documented
- constructor and projection workflows stable
- built-in dataset loading stable
- core result accessors covered by tests
- docs site published

### Milestone B: Analysis-Ready

- common summary and indicator functions wrapped
- North Sea example notebook available
- CI runs bridge tests automatically
- version compatibility policy documented

### Milestone C: Modelling-Ready

- important setter methods wrapped
- save/load workflow broadened
- more realistic end-to-end examples added
- error handling improved for model editing workflows

## Source

The canonical repository version of this plan also lives in the repository as
`python/ROADMAP.md`.
