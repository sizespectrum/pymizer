from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.integration
def test_community_model_example_runs(capsys):
    module = _load_module("community_model_example", EXAMPLES_DIR / "community_model.py")

    module.main()

    captured = capsys.readouterr()
    assert "[0." in captured.out
    assert "Community" in captured.out


@pytest.mark.integration
def test_north_sea_example_runs(capsys):
    module = _load_module("north_sea_example", EXAMPLES_DIR / "north_sea.py")

    module.main()

    captured = capsys.readouterr()
    assert "species" in captured.out
    assert "Sprat" in captured.out


@pytest.mark.integration
def test_north_sea_analysis_example_creates_expected_plots(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MPLBACKEND", "Agg")
    module = _load_module("north_sea_analysis_example", EXAMPLES_DIR / "north_sea_analysis.py")

    module.main()

    output_dir = tmp_path / "examples" / "output"
    captured = capsys.readouterr()
    assert "Saved plots to examples/output" in captured.out
    assert (output_dir / "north_sea_biomass.png").exists()
    assert (output_dir / "north_sea_cod_pred_mort.png").exists()
