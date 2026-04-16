from __future__ import annotations

from pymizer import evaluate_versions


def test_evaluate_versions_accepts_supported_stack():
    report = evaluate_versions(
        {
            "python": "3.12.0",
            "rpy2": "3.6.7",
            "R": "4.5.3",
            "mizer": "2.5.4.9113",
        }
    )
    assert report.ok is True
    assert report.issues == []


def test_evaluate_versions_flags_old_versions():
    report = evaluate_versions(
        {
            "python": "3.9.9",
            "rpy2": "3.4.0",
            "R": "3.4.0",
            "mizer": "2.4.9",
        }
    )
    assert report.ok is False
    assert any("python 3.9.9" in issue for issue in report.issues)
    assert any("rpy2 3.4.0" in issue for issue in report.issues)
    assert any("R 3.4.0" in issue for issue in report.issues)
    assert any("mizer 2.4.9" in issue for issue in report.issues)


def test_evaluate_versions_flags_missing_version_information():
    report = evaluate_versions({"python": "3.12.0"})
    assert report.ok is False
    assert any("Missing version information for rpy2." == issue for issue in report.issues)
