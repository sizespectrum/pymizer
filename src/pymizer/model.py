from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from rpy2 import robjects

from ._bridge import MizerREnvironment, get_environment
from ._converters import named_numeric_vector, to_dataframe_2d, to_numpy, to_r, to_xarray
from ._validation import validate_interaction_matrix, validate_species_params


def _wrap_params(obj: Any, env: MizerREnvironment | None = None) -> "MizerParams":
    return MizerParams(_r_obj=obj, _env=env or get_environment())


def _wrap_sim(obj: Any, env: MizerREnvironment | None = None) -> "MizerSim":
    return MizerSim(_r_obj=obj, _env=env or get_environment())


def _series_from_r_vector(value: Any, *, index: list[str] | None = None, name: str | None = None) -> pd.Series:
    """Convert an R vector to a pandas Series."""
    data = to_numpy(value)
    if index is None:
        names = robjects.r["names"](value)
        if names is not robjects.NULL and len(names) == len(data):
            index = [str(item) for item in names]
    return pd.Series(data, index=index, name=name)


def _frame_from_r_dataframe(value: Any, *, index_name: str | None = None) -> pd.DataFrame:
    """Convert an R data.frame to a labelled pandas DataFrame."""
    frame = pd.DataFrame({str(name): to_numpy(value.rx2(name)) for name in value.names})
    rownames = robjects.r["rownames"](value)
    if rownames is not robjects.NULL and len(rownames) == len(frame):
        frame.index = [str(item) for item in rownames]
        if index_name is not None:
            frame.index.name = index_name
    return frame


def _scalar_from_r(value: Any) -> float:
    """Convert a length-1 R numeric result to a Python float."""
    data = to_numpy(value).reshape(-1)
    return float(data[0])


def _growth_curves_to_frame(value: Any) -> pd.DataFrame:
    """Convert an R species x age matrix to a labelled pandas DataFrame."""
    frame = to_dataframe_2d(value, index_name="species", column_name="age")
    frame.columns = [float(col) for col in frame.columns]
    return frame


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

    def biomass(self) -> pd.Series:
        """Return species biomass in the initial state as a pandas Series."""
        return _series_from_r_vector(self._env.call("getBiomass", self._r_obj), name="biomass")

    def abundance(self) -> pd.Series:
        """Return species abundance in the initial state as a pandas Series."""
        return _series_from_r_vector(self._env.call("getN", self._r_obj), name="abundance")

    def ssb(self) -> pd.Series:
        """Return spawning stock biomass in the initial state as a pandas Series."""
        return _series_from_r_vector(self._env.call("getSSB", self._r_obj), name="ssb")

    def pred_mort(self, *, as_xarray: bool = True):
        """Return predation mortality in the initial state."""
        value = self._env.call("getPredMort", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["sp", "w"])
        return to_numpy(value)

    def feeding_level(self, *, as_xarray: bool = True):
        """Return feeding level in the initial state."""
        value = self._env.call("getFeedingLevel", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["sp", "w"])
        return to_numpy(value)

    def growth_curves(self) -> pd.DataFrame:
        """Return species growth curves as a pandas DataFrame."""
        value = self._env.call("getGrowthCurves", self._r_obj)
        return _growth_curves_to_frame(value)

    def diet(self, *, proportion: bool = True, as_xarray: bool = True):
        """Return diet composition in the initial state."""
        value = self._env.call("getDiet", self._r_obj, proportion=proportion)
        if as_xarray:
            return to_xarray(value, ["predator", "w", "prey"])
        return to_numpy(value)

    def trophic_level(self, *, as_xarray: bool = True):
        """Return trophic level at size in the initial state."""
        value = self._env.call("getTrophicLevel", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["sp", "w"])
        return to_numpy(value)

    def trophic_level_by_species(self) -> pd.Series:
        """Return the species-level trophic level in the initial state."""
        value = self._env.call("getTrophicLevelBySpecies", self._r_obj)
        return _series_from_r_vector(value, name="trophic_level_by_species")

    def mean_weight(self, **kwargs: Any) -> float:
        """Return the mean community weight in the initial state."""
        value = self._env.call("getMeanWeight", self._r_obj, **{key: to_r(val) for key, val in kwargs.items()})
        return _scalar_from_r(value)

    def proportion_of_large_fish(self, **kwargs: Any) -> float:
        """Return the proportion of large fish in the initial state."""
        value = self._env.call(
            "getProportionOfLargeFish",
            self._r_obj,
            **{key: to_r(val) for key, val in kwargs.items()},
        )
        return _scalar_from_r(value)

    def community_slope(self, **kwargs: Any) -> pd.DataFrame:
        """Return the fitted community size-spectrum slope in the initial state."""
        return _frame_from_r_dataframe(
            self._env.call("getCommunitySlope", self._r_obj, **{key: to_r(val) for key, val in kwargs.items()})
        )

    def mean_max_weight(self, measure: str = "both", **kwargs: Any):
        """Return the mean maximum weight in the initial state."""
        value = self._env.call(
            "getMeanMaxWeight",
            self._r_obj,
            measure=measure,
            **{key: to_r(val) for key, val in kwargs.items()},
        )
        if measure == "both":
            return _series_from_r_vector(value, name="mean_max_weight")
        return _scalar_from_r(value)


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

    def _final_params(self) -> MizerParams:
        """Return params updated to the final state of the simulation."""
        params = self._env.call("getParams", self._r_obj)
        updated = self._env.call("setInitialValues", params, self._r_obj)
        return _wrap_params(updated, self._env)

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

    def ssb(self) -> pd.DataFrame:
        """Return spawning stock biomass through time as a pandas DataFrame."""
        return to_dataframe_2d(self._env.call("getSSB", self._r_obj), index_name="time", column_name="species")

    def yield_gear(self, *, as_xarray: bool = True):
        """Return gear-resolved fisheries yield through time."""
        value = self._env.call("getYieldGear", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "gear", "sp"])
        return to_numpy(value)

    def f_mort_gear(self, *, as_xarray: bool = True):
        """Return gear-resolved fishing mortality through time."""
        value = self._env.call("getFMortGear", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "gear", "sp", "w"])
        return to_numpy(value)

    def pred_mort(self, *, as_xarray: bool = True):
        """Return predation mortality through time."""
        value = self._env.call("getPredMort", self._r_obj, drop=False)
        if as_xarray:
            return to_xarray(value, ["time", "sp", "w"])
        return to_numpy(value)

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

    def growth_curves(self) -> pd.DataFrame:
        """Return growth curves evaluated from the final simulation state."""
        value = self._env.call("getGrowthCurves", self._r_obj)
        return _growth_curves_to_frame(value)

    def diet(self, *, proportion: bool = True, as_xarray: bool = True):
        """Return diet composition at the final simulated state."""
        value = self._env.call("getDiet", self._final_params().r, proportion=proportion)
        if as_xarray:
            return to_xarray(value, ["predator", "w", "prey"])
        return to_numpy(value)

    def trophic_level(self, *, as_xarray: bool = True):
        """Return trophic level at size at the final simulated state."""
        value = self._env.call("getTrophicLevel", self._final_params().r)
        if as_xarray:
            return to_xarray(value, ["sp", "w"])
        return to_numpy(value)

    def trophic_level_by_species(self) -> pd.Series:
        """Return the species-level trophic level at the final simulated state."""
        value = self._env.call("getTrophicLevelBySpecies", self._final_params().r)
        return _series_from_r_vector(value, name="trophic_level_by_species")

    def mean_weight(self, **kwargs: Any) -> pd.Series:
        """Return mean community weight through time."""
        value = self._env.call("getMeanWeight", self._r_obj, **{key: to_r(val) for key, val in kwargs.items()})
        time_index = [str(item) for item in self.times()]
        series = _series_from_r_vector(value, index=time_index, name="mean_weight")
        series.index.name = "time"
        return series

    def proportion_of_large_fish(self, **kwargs: Any) -> pd.Series:
        """Return the proportion of large fish through time."""
        value = self._env.call(
            "getProportionOfLargeFish",
            self._r_obj,
            **{key: to_r(val) for key, val in kwargs.items()},
        )
        time_index = [str(item) for item in self.times()]
        series = _series_from_r_vector(value, index=time_index, name="proportion_of_large_fish")
        series.index.name = "time"
        return series

    def community_slope(self, **kwargs: Any) -> pd.DataFrame:
        """Return the fitted community size-spectrum slope through time."""
        return _frame_from_r_dataframe(
            self._env.call("getCommunitySlope", self._r_obj, **{key: to_r(val) for key, val in kwargs.items()}),
            index_name="time",
        )

    def mean_max_weight(self, measure: str = "both", **kwargs: Any):
        """Return the mean maximum weight through time."""
        value = self._env.call(
            "getMeanMaxWeight",
            self._r_obj,
            measure=measure,
            **{key: to_r(val) for key, val in kwargs.items()},
        )
        if measure == "both":
            frame = to_dataframe_2d(value, index_name="time")
            return frame
        time_index = [str(item) for item in self.times()]
        series = _series_from_r_vector(value, index=time_index, name=f"mean_max_weight_{measure}")
        series.index.name = "time"
        return series


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
