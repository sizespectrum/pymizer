from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ._bridge import MizerREnvironment, get_environment
from ._converters import named_numeric_vector, to_dataframe_2d, to_numpy, to_r, to_xarray
from ._validation import validate_interaction_matrix, validate_species_params


def _wrap_params(obj: Any, env: MizerREnvironment | None = None) -> "MizerParams":
    return MizerParams(_r_obj=obj, _env=env or get_environment())


def _wrap_sim(obj: Any, env: MizerREnvironment | None = None) -> "MizerSim":
    return MizerSim(_r_obj=obj, _env=env or get_environment())


@dataclass(frozen=True)
class MizerParams:
    """Python wrapper around an R `MizerParams` object."""

    _r_obj: Any
    _env: MizerREnvironment

    @property
    def r(self) -> Any:
        """Access the underlying R object."""
        return self._r_obj

    def copy(self) -> "MizerParams":
        """Return another wrapper for the same underlying object."""
        return _wrap_params(self._r_obj, self._env)

    def project(
        self,
        effort: float | dict[str, float] | Any | None = None,
        *,
        t_max: float = 100,
        dt: float = 0.1,
        t_save: float = 1,
        t_start: float = 0,
        progress_bar: bool = False,
        **kwargs: Any,
    ) -> "MizerSim":
        """Run `mizer::project()` and wrap the resulting `MizerSim`."""
        call_kwargs: dict[str, Any] = {
            "t_max": t_max,
            "dt": dt,
            "t_save": t_save,
            "t_start": t_start,
            "progress_bar": progress_bar,
        }
        if effort is not None:
            if isinstance(effort, dict):
                call_kwargs["effort"] = named_numeric_vector(effort)
            else:
                call_kwargs["effort"] = to_r(effort)
        for key, value in kwargs.items():
            call_kwargs[key] = to_r(value)
        sim = self._env.call("project", self._r_obj, **call_kwargs)
        return _wrap_sim(sim, self._env)

    def set_fishing(self, **kwargs: Any) -> "MizerParams":
        """Call `setFishing()` and wrap the returned params object."""
        updated = self._env.call("setFishing", self._r_obj, **{key: to_r(value) for key, value in kwargs.items()})
        return _wrap_params(updated, self._env)

    def save(self, path: str | Path) -> None:
        """Save the params object using `saveParams()`."""
        self._env.call("saveParams", self._r_obj, str(path))

    def summary(self) -> str:
        """Return the text representation of `summary(params)`."""
        summary_obj = self._env.base.summary(self._r_obj)
        return str(summary_obj)


@dataclass(frozen=True)
class MizerSim:
    """Python wrapper around an R `MizerSim` object."""

    _r_obj: Any
    _env: MizerREnvironment

    @property
    def r(self) -> Any:
        """Access the underlying R object."""
        return self._r_obj

    def params(self) -> MizerParams:
        """Return the `MizerParams` used to create the simulation."""
        params = self._env.call("getParams", self._r_obj)
        return _wrap_params(params, self._env)

    def times(self):
        """Return saved times as a numpy array."""
        return to_numpy(self._env.call("getTimes", self._r_obj))

    def biomass(self) -> pd.DataFrame:
        """Return biomass through time as a pandas DataFrame."""
        return to_dataframe_2d(self._env.call("getBiomass", self._r_obj), index_name="time", column_name="species")

    def abundance(self) -> pd.DataFrame:
        """Return total abundance through time as a pandas DataFrame."""
        return to_dataframe_2d(self._env.call("getN", self._r_obj), index_name="time", column_name="species")

    def yield_(self) -> pd.DataFrame:
        """Return fisheries yield through time as a pandas DataFrame."""
        return to_dataframe_2d(self._env.call("getYield", self._r_obj), index_name="time", column_name="species")

    def n(self, *, as_xarray: bool = True):
        """Return the species abundance array."""
        value = self._env.call("N", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "sp", "w"])
        return to_numpy(value)

    def n_resource(self, *, as_xarray: bool = True):
        """Return the resource abundance array."""
        value = self._env.call("NResource", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "w"])
        return to_numpy(value)

    def f_mort(self, *, as_xarray: bool = True):
        """Return fishing mortality through time."""
        value = self._env.call("getFMort", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "sp", "w"])
        return to_numpy(value)

    def feeding_level(self, *, as_xarray: bool = True):
        """Return feeding levels through time."""
        value = self._env.call("getFeedingLevel", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "sp", "w"])
        return to_numpy(value)


def new_multispecies_params(
    *,
    species_params: pd.DataFrame,
    interaction: Any | None = None,
    env: MizerREnvironment | None = None,
    **kwargs: Any,
) -> MizerParams:
    """Wrap `newMultispeciesParams()` with pandas-friendly inputs."""
    env = env or get_environment()
    species_params = validate_species_params(species_params)
    interaction = validate_interaction_matrix(interaction, species_params["species"].tolist())
    call_kwargs = {"species_params": to_r(species_params)}
    if interaction is not None:
        call_kwargs["interaction"] = to_r(interaction)
    for key, value in kwargs.items():
        call_kwargs[key] = to_r(value)
    params = env.call("newMultispeciesParams", **call_kwargs)
    return _wrap_params(params, env)


def new_single_species_params(
    *,
    species_params: pd.DataFrame,
    env: MizerREnvironment | None = None,
    **kwargs: Any,
) -> MizerParams:
    """Wrap `newSingleSpeciesParams()`."""
    env = env or get_environment()
    species_params = validate_species_params(species_params, single_species=True)
    call_kwargs = {"species_params": to_r(species_params)}
    for key, value in kwargs.items():
        call_kwargs[key] = to_r(value)
    params = env.call("newSingleSpeciesParams", **call_kwargs)
    return _wrap_params(params, env)


def new_community_params(env: MizerREnvironment | None = None, **kwargs: Any) -> MizerParams:
    """Wrap `newCommunityParams()`."""
    env = env or get_environment()
    params = env.call("newCommunityParams", **{key: to_r(value) for key, value in kwargs.items()})
    return _wrap_params(params, env)


def read_params(path: str | Path, env: MizerREnvironment | None = None) -> MizerParams:
    """Load a saved params object with `readParams()`."""
    env = env or get_environment()
    params = env.call("readParams", str(path))
    return _wrap_params(params, env)
