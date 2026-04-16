from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

import pandas as pd
from packaging.version import InvalidVersion, Version

try:  # pragma: no cover - exercised indirectly in runtime diagnostics
    from rpy2 import robjects
    from rpy2.robjects import conversion, default_converter, numpy2ri, pandas2ri
    from rpy2.robjects.packages import importr
    _RPY2_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - depends on local Python/R setup
    robjects = None
    conversion = default_converter = numpy2ri = pandas2ri = None
    importr = None
    _RPY2_IMPORT_ERROR = exc


MINIMUM_VERSIONS = {
    "python": "3.10",
    "rpy2": "3.5",
    "R": "3.5",
    "mizer": "2.5.0",
}


class MizerError(RuntimeError):
    """Raised when the R bridge cannot complete an operation.

    This usually indicates one of three problems:

    - `rpy2` could not be imported or initialised against the local R install
    - the R package `mizer` is unavailable
    - an R-side function call failed
    """


@dataclass(frozen=True)
class CompatibilityReport:
    """Compatibility report for the active Python and R runtime stack.

    Attributes:
        versions: Detected versions for the current Python, R, `rpy2`, and
            `mizer` runtime stack.
        minimum_versions: Minimum versions expected by `pymizer`.
        issues: Human-readable compatibility problems, if any.
    """

    versions: dict[str, str]
    minimum_versions: dict[str, str]
    issues: list[str]

    @property
    def ok(self) -> bool:
        """Return whether the runtime environment passes compatibility checks."""
        return len(self.issues) == 0


def _safe_version(text: str) -> Version | None:
    """Parse a version string into a packaging Version if possible."""
    try:
        return Version(text)
    except InvalidVersion:
        return None


def evaluate_versions(versions: dict[str, str], minimum_versions: dict[str, str] | None = None) -> CompatibilityReport:
    """Evaluate detected versions against the supported minimum versions.

    Args:
        versions: Mapping of component name to version string.
        minimum_versions: Optional override for the default minimum versions.

    Returns:
        A :class:`CompatibilityReport`.

    Examples:
        ```python
        import pymizer as mz

        report = mz.evaluate_versions(
            {"python": "3.12.0", "rpy2": "3.6.7", "R": "4.5.3", "mizer": "2.5.4", "pymizer": "0.1.0"}
        )
        print(report.ok)
        ```
    """
    minimum_versions = minimum_versions or MINIMUM_VERSIONS
    issues: list[str] = []

    for name, minimum in minimum_versions.items():
        actual = versions.get(name)
        if actual is None:
            issues.append(f"Missing version information for {name}.")
            continue
        actual_version = _safe_version(actual)
        minimum_version = _safe_version(minimum)
        if actual_version is None or minimum_version is None:
            issues.append(f"Could not compare version for {name}: actual='{actual}', minimum='{minimum}'.")
            continue
        if actual_version < minimum_version:
            issues.append(f"{name} {actual} is below the supported minimum version {minimum}.")

    return CompatibilityReport(
        versions=versions,
        minimum_versions=minimum_versions,
        issues=issues,
    )


@dataclass
class MizerREnvironment:
    """Thin wrapper around the embedded R session used by `pymizer`.

    Most users should access the shared singleton via :func:`get_environment`
    rather than instantiating this class directly.

    Examples:
        ```python
        import pymizer as mz

        env = mz.get_environment()
        print(env.versions())
        ```
    """

    package_name: str = "mizer"

    def __post_init__(self) -> None:
        if _RPY2_IMPORT_ERROR is not None:
            raise MizerError(
                "Could not import the Python package 'rpy2', or rpy2 could not "
                "initialise against the local R installation. Make sure rpy2 is "
                "installed and that R is available to Python."
            ) from _RPY2_IMPORT_ERROR
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
        """Call an exported R function from the `mizer` package.

        Args:
            name: Exported function name in the R package.
            *args: Positional arguments passed to the R function.
            **kwargs: Keyword arguments passed to the R function.

        Returns:
            The raw R object returned by the function call.

        Raises:
            MizerError: If the function is missing or the R call fails.
        """
        try:
            fun = getattr(self.mizer, name)
        except AttributeError as exc:
            raise MizerError(f"The R package does not export '{name}'.") from exc

        try:
            return fun(*args, **kwargs)
        except Exception as exc:
            raise MizerError(f"Calling mizer::{name} failed.") from exc

    def save_rds(self, obj: Any, path: str | Path) -> None:
        """Save an R object to an `.rds` file."""
        with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
            self.base.saveRDS(obj, file=str(path))

    def read_rds(self, path: str | Path) -> Any:
        """Read an `.rds` file and return the raw R object."""
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
        """Convert an R object to a pandas DataFrame via `as.data.frame()`."""
        with conversion.localconverter(default_converter + numpy2ri.converter + pandas2ri.converter):
            frame = robjects.r["as.data.frame"](obj)
            if isinstance(frame, pd.DataFrame):
                return frame
            return pd.DataFrame(frame)

    def versions(self) -> dict[str, str]:
        """Return version information for the active Python and R bridge stack.

        Returns:
            A mapping with entries for `pymizer`, Python, `rpy2`, R, and
            `mizer`.
        """
        r_version = str(robjects.r["as.character"](robjects.r["getRversion"]())[0])
        mizer_version = str(robjects.r["as.character"](self.utils.packageVersion(self.package_name))[0])
        return {
            "pymizer": metadata.version("pymizer"),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "rpy2": metadata.version("rpy2"),
            "R": r_version,
            self.package_name: mizer_version,
        }

    def compatibility_report(self) -> CompatibilityReport:
        """Return a compatibility report for the active runtime environment."""
        return evaluate_versions(self.versions())


_ENV: MizerREnvironment | None = None


def get_environment() -> MizerREnvironment:
    """Return the singleton R environment used by `pymizer`.

    Returns:
        The shared :class:`MizerREnvironment` instance.

    Examples:
        ```python
        import pymizer as mz

        env = mz.get_environment()
        print(env.compatibility_report().ok)
        ```
    """
    global _ENV
    if _ENV is None:
        _ENV = MizerREnvironment()
    return _ENV


def runtime_diagnostics() -> dict[str, Any]:
    """Return environment diagnostics without requiring access to internals.

    The returned dictionary is designed for quick troubleshooting in notebooks,
    scripts, or issue reports.

    Returns:
        A dictionary describing:

        - whether `rpy2` imported successfully
        - minimum supported versions
        - detected runtime versions when available
        - overall compatibility status
        - any issues that were found

    Examples:
        ```python
        import pymizer as mz

        diagnostics = mz.runtime_diagnostics()
        print(diagnostics["compatibility"])
        ```
    """
    diagnostics: dict[str, Any] = {
        "rpy2_import_ok": _RPY2_IMPORT_ERROR is None,
        "rpy2_import_error": None if _RPY2_IMPORT_ERROR is None else str(_RPY2_IMPORT_ERROR),
        "minimum_versions": dict(MINIMUM_VERSIONS),
    }
    if _RPY2_IMPORT_ERROR is not None:
        diagnostics["versions"] = {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
        diagnostics["compatibility"] = False
        diagnostics["issues"] = [
            "rpy2 could not be imported or initialised.",
        ]
        return diagnostics

    try:
        env = get_environment()
        report = env.compatibility_report()
        diagnostics["versions"] = report.versions
        diagnostics["compatibility"] = report.ok
        diagnostics["issues"] = report.issues
    except Exception as exc:
        diagnostics["versions"] = {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
        diagnostics["compatibility"] = False
        diagnostics["issues"] = [str(exc)]
    return diagnostics
