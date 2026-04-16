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

::: pymizer._bridge
