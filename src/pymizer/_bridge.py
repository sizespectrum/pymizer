from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

import pandas as pd

from rpy2 import robjects
from rpy2.robjects import conversion, default_converter, numpy2ri, pandas2ri
from rpy2.robjects.packages import importr


class MizerError(RuntimeError):
    """Raised when the R bridge cannot complete an operation."""


@dataclass
class MizerREnvironment:
    """Thin wrapper around the embedded R session used by pymizer."""

    package_name: str = "mizer"

    def __post_init__(self) -> None:
        try:
            self.methods = importr("methods")
            self.base = importr("base")
            self.utils = importr("utils")
            self.mizer = importr(self.package_name)
        except Exception as exc:  # pragma: no cover - depends on local R setup
            raise MizerError(
                "Could not load the R bridge for pymizer. Make sure R is installed, "
                "that the 'mizer' R package is available in your R library, and "
                "that the Python package 'rpy2' can talk to your local R installation."
            ) from exc

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Call an exported R function from the mizer package."""
        try:
            fun = getattr(self.mizer, name)
        except AttributeError as exc:
            raise MizerError(f"The R package does not export '{name}'.") from exc

        try:
            return fun(*args, **kwargs)
        except Exception as exc:
            raise MizerError(f"Calling mizer::{name} failed.") from exc

    def save_rds(self, obj: Any, path: str | Path) -> None:
        """Save an R object to an RDS file."""
        with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
            self.base.saveRDS(obj, file=str(path))

    def read_rds(self, path: str | Path) -> Any:
        """Read an RDS file."""
        return self.base.readRDS(str(path))

    def class_name(self, obj: Any) -> str:
        """Return the first class name for an R object."""
        cls = robjects.r["class"](obj)
        return str(cls[0]) if len(cls) > 0 else ""

    def is_s4(self, obj: Any) -> bool:
        """Return whether an object is an S4 object."""
        return bool(self.methods.isS4(obj)[0])

    def slot_names(self, obj: Any) -> list[str]:
        """Return slot names for an S4 object."""
        slots = self.methods.slotNames(obj)
        return [str(name) for name in slots]

    def dataframe_from_r(self, obj: Any) -> pd.DataFrame:
        """Convert an R object to a pandas DataFrame via as.data.frame()."""
        with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
            frame = robjects.r["as.data.frame"](obj)
            if isinstance(frame, pd.DataFrame):
                return frame
            return pd.DataFrame(frame)

    def versions(self) -> dict[str, str]:
        """Return version information for the active Python and R bridge stack."""
        r_version = str(robjects.r["as.character"](robjects.r["getRversion"]())[0])
        mizer_version = str(robjects.r["as.character"](self.utils.packageVersion(self.package_name))[0])
        return {
            "pymizer": metadata.version("pymizer"),
            "rpy2": metadata.version("rpy2"),
            "R": r_version,
            self.package_name: mizer_version,
        }


_ENV: MizerREnvironment | None = None


def get_environment() -> MizerREnvironment:
    """Return the singleton R environment used by pymizer."""
    global _ENV
    if _ENV is None:
        _ENV = MizerREnvironment()
    return _ENV
