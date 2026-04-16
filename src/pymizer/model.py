from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from rpy2 import robjects

from ._bridge import MizerREnvironment, get_environment
from ._converters import named_list, named_numeric_vector, to_dataframe_2d, to_numpy, to_r, to_xarray
from ._validation import validate_interaction_matrix, validate_species_params


def _species_arg(species: str | list[str] | tuple[str, ...] | None) -> Any:
    """Convert species selections to the R form expected by mizer."""
    if species is None:
        return None
    if isinstance(species, str):
        return robjects.StrVector([species])
    return robjects.StrVector([str(item) for item in species])


def _indicator_kwargs(
    *,
    species: str | list[str] | tuple[str, ...] | None = None,
    min_w: float | list[float] | None = None,
    max_w: float | list[float] | None = None,
    min_l: float | list[float] | None = None,
    max_l: float | list[float] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build keyword arguments for size-filtered summary methods."""
    call_kwargs: dict[str, Any] = {}
    if species is not None:
        call_kwargs["species"] = _species_arg(species)
    if min_w is not None:
        call_kwargs["min_w"] = to_r(min_w)
    if max_w is not None:
        call_kwargs["max_w"] = to_r(max_w)
    if min_l is not None:
        call_kwargs["min_l"] = to_r(min_l)
    if max_l is not None:
        call_kwargs["max_l"] = to_r(max_l)
    for key, value in kwargs.items():
        if value is not None:
            call_kwargs[key] = to_r(value)
    return call_kwargs


def _optional_kwargs(**kwargs: Any) -> dict[str, Any]:
    """Drop keyword arguments with None values."""
    return {key: value for key, value in kwargs.items() if value is not None}


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


def _series_with_float_index(value: Any, *, name: str | None = None, index_name: str | None = None) -> pd.Series:
    """Convert a named R vector to a pandas Series with float index."""
    series = _series_from_r_vector(value, name=name)
    series.index = [float(item) for item in series.index]
    if index_name is not None:
        series.index.name = index_name
    return series


def _growth_curves_to_frame(value: Any, species_order: str | list[str] | tuple[str, ...] | None = None) -> pd.DataFrame:
    """Convert an R species x age matrix to a labelled pandas DataFrame."""
    frame = to_dataframe_2d(value, index_name="species", column_name="age")
    frame.columns = [float(col) for col in frame.columns]
    if species_order is not None:
        requested = [species_order] if isinstance(species_order, str) else [str(item) for item in species_order]
        available = [item for item in requested if item in frame.index]
        if available:
            frame = frame.loc[available]
    return frame


def _listvector_to_python(value: Any) -> Any:
    """Convert a named R list to nested Python structures."""
    if isinstance(value, robjects.vectors.ListVector):
        if value.names is robjects.NULL:
            return [_listvector_to_python(item) for item in value]
        result: dict[str, Any] = {}
        names = [str(name) for name in value.names]
        for name, item in zip(names, value):
            result[name] = _listvector_to_python(item)
        return result
    data = to_numpy(value)
    if data.ndim == 0:
        return data.item() if hasattr(data, "item") else data
    if data.size == 1:
        scalar = data.reshape(-1)[0]
        return scalar.item() if hasattr(scalar, "item") else scalar
    return data.tolist()


@dataclass(frozen=True)
class MizerParams:
    """Python wrapper around an R ``MizerParams`` object.

    ``MizerParams`` is the main model-configuration object in `mizer`. In
    Python it acts as the starting point for running projections and inspecting
    the initial state of a model.

    Examples:
        Create a small community model and inspect its initial biomass:

        ```python
        import pymizer as mz

        params = mz.new_community_params(no_w=20)
        biomass = params.biomass()
        ```
    """

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
        """Run ``mizer::project()`` and return a wrapped simulation result.

        Args:
            effort: Fishing effort passed through to `mizer`. A Python dict is
                converted to a named R numeric vector.
            t_max: Projection length in years.
            dt: Internal integration time step.
            t_save: Interval between saved output times.
            t_start: Starting time recorded on the simulation output.
            progress_bar: Whether `mizer` should show an R-side progress bar.
            **kwargs: Additional arguments forwarded to ``mizer::project()``.

        Returns:
            A :class:`MizerSim` wrapper around the R simulation object.

        Examples:
            ```python
            import pymizer as mz

            params = mz.new_community_params(no_w=20)
            sim = params.project(t_max=5, dt=0.1, t_save=1, progress_bar=False)
            ```
        """
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

    def interaction_matrix(self) -> pd.DataFrame:
        """Return the species interaction matrix as a pandas DataFrame."""
        return to_dataframe_2d(self._env.call("interaction_matrix", self._r_obj), index_name="predator", column_name="prey")

    def metadata(self) -> dict[str, Any]:
        """Return model metadata as nested Python structures."""
        return _listvector_to_python(self._env.call("getMetadata", self._r_obj))

    def set_interaction(self, interaction: Any) -> "MizerParams":
        """Return a new params object with an updated interaction matrix.

        Args:
            interaction: Species interaction matrix as a pandas DataFrame,
                NumPy array, or other matrix-like object.
        """
        updated = self._env.call("setInteraction", self._r_obj, interaction=to_r(interaction))
        return _wrap_params(updated, self._env)

    def set_resource(
        self,
        *,
        resource_rate: Any | None = None,
        resource_capacity: Any | None = None,
        resource_level: Any | None = None,
        resource_dynamics: str | None = None,
        lambda_: float | None = None,
        n: float | None = None,
        w_pp_cutoff: float | None = None,
        balance: bool | None = None,
    ) -> "MizerParams":
        """Return a new params object with updated resource settings."""
        updated = self._env.call(
            "setResource",
            self._r_obj,
            **_optional_kwargs(
                resource_rate=to_r(resource_rate) if resource_rate is not None else None,
                resource_capacity=to_r(resource_capacity) if resource_capacity is not None else None,
                resource_level=to_r(resource_level) if resource_level is not None else None,
                resource_dynamics=resource_dynamics,
                **{"lambda": lambda_},
                n=n,
                w_pp_cutoff=w_pp_cutoff,
                balance=balance,
            ),
        )
        return _wrap_params(updated, self._env)

    def set_initial_values(
        self,
        sim: "MizerSim",
        *,
        time_range: Any | None = None,
        geometric_mean: bool = False,
    ) -> "MizerParams":
        """Return a new params object with initial values copied from a simulation."""
        updated = self._env.call(
            "setInitialValues",
            self._r_obj,
            sim.r,
            **_optional_kwargs(
                time_range=to_r(time_range) if time_range is not None else None,
                geometric_mean=geometric_mean,
            ),
        )
        return _wrap_params(updated, self._env)

    def set_metadata(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        authors: Any | None = None,
        url: str | None = None,
        doi: str | None = None,
        **extra_fields: Any,
    ) -> "MizerParams":
        """Return a new params object with updated metadata."""
        call_kwargs = _optional_kwargs(
            title=title,
            description=description,
            authors=to_r(authors) if authors is not None else None,
            url=url,
            doi=doi,
        )
        for key, value in extra_fields.items():
            call_kwargs[key] = named_list(value) if isinstance(value, dict) else to_r(value)
        updated = self._env.call("setMetadata", self._r_obj, **call_kwargs)
        return _wrap_params(updated, self._env)

    def summary(self) -> str:
        """Return the text representation of `summary(params)`."""
        summary_obj = self._env.base.summary(self._r_obj)
        return str(summary_obj)

    def biomass(
        self,
        *,
        use_cutoff: bool = False,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.Series:
        """Return species biomass in the initial state.

        Args:
            use_cutoff: Use the `biomass_cutoff` species parameter when
                available.
            min_w: Minimum weight filter.
            max_w: Maximum weight filter.
            min_l: Minimum length filter.
            max_l: Maximum length filter.

        Returns:
            A ``pandas.Series`` indexed by species name.

        Examples:
            ```python
            biomass = params.biomass(min_w=10, max_w=1000)
            ```
        """
        return _series_from_r_vector(
            self._env.call(
                "getBiomass",
                self._r_obj,
                use_cutoff=use_cutoff,
                **_indicator_kwargs(min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
            ),
            name="biomass",
        )

    def abundance(
        self,
        *,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.Series:
        """Return species abundance in the initial state.

        Args:
            min_w: Minimum weight filter.
            max_w: Maximum weight filter.
            min_l: Minimum length filter.
            max_l: Maximum length filter.

        Returns:
            A ``pandas.Series`` indexed by species name.
        """
        return _series_from_r_vector(
            self._env.call(
                "getN",
                self._r_obj,
                **_indicator_kwargs(min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
            ),
            name="abundance",
        )

    def ssb(self) -> pd.Series:
        """Return spawning stock biomass in the initial state as a pandas Series."""
        return _series_from_r_vector(self._env.call("getSSB", self._r_obj), name="ssb")

    def initial_n(self, *, as_xarray: bool = True):
        """Return the initial fish abundance density spectrum.

        Args:
            as_xarray: When ``True``, return an ``xarray.DataArray`` with
                dimensions ``("sp", "w")``. Otherwise return a NumPy array.

        Examples:
            ```python
            initial_n = params.initial_n()
            cod = initial_n.sel(sp="Cod")
            ```
        """
        value = self._env.call("initialN", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["sp", "w"])
        return to_numpy(value)

    def initial_n_resource(self) -> pd.Series:
        """Return the initial resource spectrum.

        Returns:
            A ``pandas.Series`` indexed by resource size.
        """
        value = self._env.call("initialNResource", self._r_obj)
        return _series_with_float_index(value, name="initial_n_resource", index_name="w")

    def pred_rate(self, *, as_xarray: bool = True, t: float = 0):
        """Return predation rate by predator species and prey size.

        Args:
            as_xarray: When ``True``, return an ``xarray.DataArray`` with
                dimensions ``("sp", "w_prey")``.
            t: Time passed through to ``mizer::getPredRate()``.
        """
        value = self._env.call("getPredRate", self._r_obj, t=t)
        if as_xarray:
            return to_xarray(value, ["sp", "w_prey"])
        return to_numpy(value)

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

    def growth_curves(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        max_age: float = 20,
        percentage: bool = False,
    ) -> pd.DataFrame:
        """Return species growth curves as a pandas DataFrame.

        Args:
            species: Optional species subset.
            max_age: Maximum age to evaluate.
            percentage: Return size as a percentage of ``w_max``.

        Returns:
            A ``pandas.DataFrame`` indexed by species with age values as
            columns.
        """
        value = self._env.call("getGrowthCurves", self._r_obj, **_optional_kwargs(
            species=_species_arg(species),
            max_age=max_age,
            percentage=percentage,
        ))
        return _growth_curves_to_frame(value, species_order=species)

    def diet(self, *, proportion: bool = True, as_xarray: bool = True):
        """Return diet composition in the initial state.

        Args:
            proportion: If ``True``, normalise prey contributions to
                proportions.
            as_xarray: When ``True``, return an ``xarray.DataArray`` with
                dimensions ``("predator", "w", "prey")``.
        """
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

    def mean_weight(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> float:
        """Return the mean community weight in the initial state.

        Args:
            species: Optional species subset.
            min_w: Minimum weight filter.
            max_w: Maximum weight filter.
            min_l: Minimum length filter.
            max_l: Maximum length filter.
        """
        value = self._env.call(
            "getMeanWeight",
            self._r_obj,
            **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
        )
        return _scalar_from_r(value)

    def proportion_of_large_fish(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        threshold_w: float = 100,
        threshold_l: float | None = None,
        biomass_proportion: bool = True,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> float:
        """Return the proportion of large fish in the initial state.

        Args:
            species: Optional species subset.
            threshold_w: Weight threshold separating small and large fish.
            threshold_l: Length threshold separating small and large fish.
            biomass_proportion: Use biomass rather than numbers.
            min_w: Minimum weight filter.
            max_w: Maximum weight filter.
            min_l: Minimum length filter.
            max_l: Maximum length filter.
        """
        value = self._env.call(
            "getProportionOfLargeFish",
            self._r_obj,
            **_optional_kwargs(
                threshold_w=threshold_w,
                threshold_l=to_r(threshold_l) if threshold_l is not None else None,
                biomass_proportion=biomass_proportion,
            ),
            **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
        )
        return _scalar_from_r(value)

    def community_slope(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        biomass: bool = True,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.DataFrame:
        """Return the fitted community size-spectrum slope in the initial state.

        Returns:
            A one-row ``pandas.DataFrame`` with ``slope``, ``intercept``, and
            ``r2`` columns.
        """
        return _frame_from_r_dataframe(
            self._env.call(
                "getCommunitySlope",
                self._r_obj,
                biomass=biomass,
                **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
            )
        )

    def mean_max_weight(
        self,
        measure: str = "both",
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ):
        """Return the mean maximum weight in the initial state.

        Args:
            measure: One of ``"both"``, ``"numbers"``, or ``"biomass"``.
            species: Optional species subset.
            min_w: Minimum weight filter.
            max_w: Maximum weight filter.
            min_l: Minimum length filter.
            max_l: Maximum length filter.
        """
        value = self._env.call(
            "getMeanMaxWeight",
            self._r_obj,
            measure=measure,
            **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
        )
        if measure == "both":
            return _series_from_r_vector(value, name="mean_max_weight")
        return _scalar_from_r(value)


@dataclass(frozen=True)
class MizerSim:
    """Python wrapper around an R ``MizerSim`` object.

    ``MizerSim`` stores time-resolved output from a projection. The wrapper
    exposes common summaries as labelled ``pandas`` and ``xarray`` objects.

    Examples:
        ```python
        import pymizer as mz

        params = mz.new_community_params(no_w=20)
        sim = params.project(t_max=5, dt=0.1, t_save=1, progress_bar=False)
        biomass = sim.biomass()
        ```
    """

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
        """Return saved times as a NumPy array."""
        return to_numpy(self._env.call("getTimes", self._r_obj))

    def biomass(
        self,
        *,
        use_cutoff: bool = False,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.DataFrame:
        """Return biomass through time as a pandas DataFrame.

        Args:
            use_cutoff: Use the `biomass_cutoff` species parameter when
                available.
            min_w: Minimum weight filter.
            max_w: Maximum weight filter.
            min_l: Minimum length filter.
            max_l: Maximum length filter.
        """
        return to_dataframe_2d(
            self._env.call(
                "getBiomass",
                self._r_obj,
                use_cutoff=use_cutoff,
                **_indicator_kwargs(min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
            ),
            index_name="time",
            column_name="species",
        )

    def abundance(
        self,
        *,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.DataFrame:
        """Return total abundance through time as a pandas DataFrame."""
        return to_dataframe_2d(
            self._env.call(
                "getN",
                self._r_obj,
                **_indicator_kwargs(min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
            ),
            index_name="time",
            column_name="species",
        )

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
        """Return the species abundance array.

        Args:
            as_xarray: When ``True``, return an ``xarray.DataArray`` with
                dimensions ``("time", "sp", "w")``.
        """
        value = self._env.call("N", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "sp", "w"])
        return to_numpy(value)

    def n_resource(self, *, as_xarray: bool = True):
        """Return the resource abundance array.

        Args:
            as_xarray: When ``True``, return an ``xarray.DataArray`` with
                dimensions ``("time", "w")``.
        """
        value = self._env.call("NResource", self._r_obj)
        if as_xarray:
            return to_xarray(value, ["time", "w"])
        return to_numpy(value)

    def initial_n(self, *, as_xarray: bool = True):
        """Return the initial fish abundance density spectrum used by the simulation."""
        return self.params().initial_n(as_xarray=as_xarray)

    def initial_n_resource(self) -> pd.Series:
        """Return the initial resource spectrum used by the simulation."""
        return self.params().initial_n_resource()

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

    def pred_rate(self, *, as_xarray: bool = True):
        """Return predation rate at the final simulated state.

        This uses ``setInitialValues(getParams(sim), sim)`` under the hood so
        that the predation rate is evaluated on the final simulated state.
        """
        value = self._env.call("getPredRate", self._final_params().r, t=float(self.times()[-1]))
        if as_xarray:
            return to_xarray(value, ["sp", "w_prey"])
        return to_numpy(value)

    def growth_curves(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        max_age: float = 20,
        percentage: bool = False,
    ) -> pd.DataFrame:
        """Return growth curves evaluated from the final simulation state.

        Args:
            species: Optional species subset.
            max_age: Maximum age to evaluate.
            percentage: Return size as a percentage of ``w_max``.
        """
        value = self._env.call("getGrowthCurves", self._r_obj, **_optional_kwargs(
            species=_species_arg(species),
            max_age=max_age,
            percentage=percentage,
        ))
        return _growth_curves_to_frame(value, species_order=species)

    def diet(self, *, proportion: bool = True, as_xarray: bool = True):
        """Return diet composition at the final simulated state.

        This method evaluates diet on a params object rebuilt from the final
        simulated state.
        """
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

    def mean_weight(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.Series:
        """Return mean community weight through time."""
        value = self._env.call(
            "getMeanWeight",
            self._r_obj,
            **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
        )
        time_index = [str(item) for item in self.times()]
        series = _series_from_r_vector(value, index=time_index, name="mean_weight")
        series.index.name = "time"
        return series

    def proportion_of_large_fish(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        threshold_w: float = 100,
        threshold_l: float | None = None,
        biomass_proportion: bool = True,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.Series:
        """Return the proportion of large fish through time."""
        value = self._env.call(
            "getProportionOfLargeFish",
            self._r_obj,
            **_optional_kwargs(
                threshold_w=threshold_w,
                threshold_l=to_r(threshold_l) if threshold_l is not None else None,
                biomass_proportion=biomass_proportion,
            ),
            **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
        )
        time_index = [str(item) for item in self.times()]
        series = _series_from_r_vector(value, index=time_index, name="proportion_of_large_fish")
        series.index.name = "time"
        return series

    def community_slope(
        self,
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        biomass: bool = True,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ) -> pd.DataFrame:
        """Return the fitted community size-spectrum slope through time."""
        return _frame_from_r_dataframe(
            self._env.call(
                "getCommunitySlope",
                self._r_obj,
                biomass=biomass,
                **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
            ),
            index_name="time",
        )

    def mean_max_weight(
        self,
        measure: str = "both",
        *,
        species: str | list[str] | tuple[str, ...] | None = None,
        min_w: float | list[float] | None = None,
        max_w: float | list[float] | None = None,
        min_l: float | list[float] | None = None,
        max_l: float | list[float] | None = None,
    ):
        """Return the mean maximum weight through time."""
        value = self._env.call(
            "getMeanMaxWeight",
            self._r_obj,
            measure=measure,
            **_indicator_kwargs(species=species, min_w=min_w, max_w=max_w, min_l=min_l, max_l=max_l),
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
    """Create a multispecies model from Python data structures.

    Args:
        species_params: Species parameter table as a ``pandas.DataFrame``.
        interaction: Optional interaction matrix.
        env: Optional shared R environment wrapper.
        **kwargs: Additional arguments forwarded to
            ``mizer::newMultispeciesParams()``.

    Returns:
        A wrapped :class:`MizerParams` object.

    Examples:
        ```python
        import pymizer as mz

        species = mz.load_dataset("NS_species_params")
        interaction = mz.load_dataset("NS_interaction")
        params = mz.new_multispecies_params(
            species_params=species,
            interaction=interaction,
        )
        ```
    """
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
    """Create a single-species model.

    Args:
        species_params: Single-row species parameter table.
        env: Optional shared R environment wrapper.
        **kwargs: Additional arguments forwarded to
            ``mizer::newSingleSpeciesParams()``.
    """
    env = env or get_environment()
    species_params = validate_species_params(species_params, single_species=True)
    call_kwargs = {"species_params": to_r(species_params)}
    for key, value in kwargs.items():
        call_kwargs[key] = to_r(value)
    params = env.call("newSingleSpeciesParams", **call_kwargs)
    return _wrap_params(params, env)


def new_community_params(env: MizerREnvironment | None = None, **kwargs: Any) -> MizerParams:
    """Create a simple community model.

    Args:
        env: Optional shared R environment wrapper.
        **kwargs: Additional arguments forwarded to
            ``mizer::newCommunityParams()``.

    Examples:
        ```python
        import pymizer as mz

        params = mz.new_community_params(no_w=20)
        ```
    """
    env = env or get_environment()
    params = env.call("newCommunityParams", **{key: to_r(value) for key, value in kwargs.items()})
    return _wrap_params(params, env)


def read_params(path: str | Path, env: MizerREnvironment | None = None) -> MizerParams:
    """Load a saved params object with ``mizer::readParams()``.

    Args:
        path: Path to an ``.rds`` file created by ``saveParams()``.
        env: Optional shared R environment wrapper.
    """
    env = env or get_environment()
    params = env.call("readParams", str(path))
    return _wrap_params(params, env)
