from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pymizer import validate_interaction_matrix, validate_species_params


def test_validate_species_params_requires_species_column():
    species = pd.DataFrame({"w_max": [1.0]})
    with pytest.raises(ValueError, match="species"):
        validate_species_params(species)


def test_validate_species_params_rejects_duplicates():
    species = pd.DataFrame({"species": ["Cod", "Cod"], "w_max": [1.0, 2.0]})
    with pytest.raises(ValueError, match="duplicate"):
        validate_species_params(species)


def test_validate_species_params_single_species_mode():
    species = pd.DataFrame({"species": ["Cod", "Haddock"], "w_max": [1.0, 2.0]})
    with pytest.raises(ValueError, match="exactly one row"):
        validate_species_params(species, single_species=True)


def test_validate_interaction_matrix_accepts_matching_dataframe():
    species_names = ["Cod", "Haddock"]
    interaction = pd.DataFrame(
        [[1.0, 0.5], [0.5, 1.0]],
        index=species_names,
        columns=species_names,
    )
    validated = validate_interaction_matrix(interaction, species_names)
    assert validated is interaction


def test_validate_interaction_matrix_rejects_wrong_shape():
    species_names = ["Cod", "Haddock"]
    interaction = np.ones((3, 3))
    with pytest.raises(ValueError, match="shape"):
        validate_interaction_matrix(interaction, species_names)


def test_validate_interaction_matrix_rejects_mismatched_labels():
    species_names = ["Cod", "Haddock"]
    interaction = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]], index=["Cod", "Sprat"], columns=species_names)
    with pytest.raises(ValueError, match="row names"):
        validate_interaction_matrix(interaction, species_names)
