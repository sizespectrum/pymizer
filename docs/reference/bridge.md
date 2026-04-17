# R Bridge API

The bridge API covers the lower-level runtime layer that connects Python to the
embedded R session.

Most users only need:

- `get_environment()` to inspect the shared bridge instance
- `runtime_diagnostics()` to troubleshoot setup problems
- `evaluate_versions()` and `CompatibilityReport` to reason about supported
  runtime combinations

You can also use `MizerREnvironment` directly when you need to inspect raw R
objects or call additional exported `mizer` functions.

## Generated API Pages

For signatures, runtime compatibility details, and lower-level class reference
pages, see:

- [CompatibilityReport](../api/CompatibilityReport.qmd)
- [MizerREnvironment](../api/MizerREnvironment.qmd)
- [evaluate_versions](../api/evaluate_versions.qmd)
- [get_environment](../api/get_environment.qmd)
- [runtime_diagnostics](../api/runtime_diagnostics.qmd)
