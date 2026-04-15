# Reference

The `pymizer` reference is organised into a few small modules.

## Main API

- [Model API](model.md): model constructors and wrapper classes
- [Dataset API](datasets.md): list and load packaged example datasets
- [R Bridge API](bridge.md): lower-level access to the embedded R environment

## Design Notes

The public API deliberately stays narrower than the full R package:

- constructor functions are exposed at top level
- `MizerParams` and `MizerSim` provide the most common workflows
- raw R objects remain accessible through the `.r` property when needed
