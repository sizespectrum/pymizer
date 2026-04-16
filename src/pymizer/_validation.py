from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def validate_species_params(species_params: pd.DataFrame, *, single_species: bool = False) -> pd.DataFrame:
    """Validate a species parameter table before handing it to R."""
    if not isinstance(species_params, pd.DataFrame):
        raise TypeError("species_params must be a pandas.DataFrame.")
    if species_params.empty:
        raise ValueError("species_params must not be empty.")
    if "species" not in species_params.columns:
        raise ValueError("species_params must contain a 'species' column.")
    if species_params["species"].isna().any():
        raise ValueError("species_params contains missing values in the 'species' column.")
    if species_params["species"].duplicated().any():
        duplicates = species_params.loc[species_params["species"].duplicated(), "species"].tolist()
        raise ValueError(
            "species_params must not contain duplicate species names. "
            f"Duplicates: {', '.join(str(name) for name in duplicates)}."
        )
    if single_species and len(species_params) != 1:
        raise ValueError("new_single_species_params() requires exactly one row in species_params.")
    return species_params


def validate_interaction_matrix(interaction: Any, species_names: list[str]) -> Any:
    """Validate an interaction matrix against the supplied species names."""
    if interaction is None:
        return None

    expected = len(species_names)

    if isinstance(interaction, pd.DataFrame):
        if interaction.shape != (expected, expected):
            raise ValueError(
                "interaction must have shape "
                f"({expected}, {expected}), got {interaction.shape}."
            )
        if list(interaction.index) != species_names:
            raise ValueError("interaction row names must match species_params['species'] in order.")
        if list(interaction.columns) != species_names:
            raise ValueError("interaction column names must match species_params['species'] in order.")
        return interaction

    if isinstance(interaction, np.ndarray):
        if interaction.shape != (expected, expected):
            raise ValueError(
                "interaction must have shape "
                f"({expected}, {expected}), got {interaction.shape}."
            )
        return interaction

    raise TypeError("interaction must be a pandas.DataFrame, a numpy.ndarray, or None.")
