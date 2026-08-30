"""Tests for Next-Gen-Reco app/_paths module — project root and path constants."""

from pathlib import Path

from app._paths import (
    CACHE_DIR,
    DATA_DIR,
    MODELS_DIR,
    ND_DIR,
    PROJECT_ROOT,
    STREAMLIT_DIR,
)


class TestProjectRoot:
    """Tests for PROJECT_ROOT resolution."""

    def test_is_path_object(self) -> None:
        assert isinstance(PROJECT_ROOT, Path)

    def test_is_absolute(self) -> None:
        assert PROJECT_ROOT.is_absolute()

    def test_points_to_repo_root(self) -> None:
        """PROJECT_ROOT should be the directory containing app/."""
        assert (PROJECT_ROOT / "app").is_dir()

    def test_has_readme(self) -> None:
        """The repo root should contain a README."""
        assert (PROJECT_ROOT / "README.md").exists()


class TestDirectoryConstants:
    """Tests for convenience path aliases."""

    def test_data_dir_is_under_root(self) -> None:
        assert DATA_DIR.parent == PROJECT_ROOT
        assert DATA_DIR.name == "data"

    def test_models_dir_is_under_root(self) -> None:
        assert MODELS_DIR.parent == PROJECT_ROOT
        assert MODELS_DIR.name == "models"

    def test_cache_dir_is_under_root(self) -> None:
        assert CACHE_DIR.parent == PROJECT_ROOT
        assert CACHE_DIR.name == ".cache"

    def test_nd_dir_is_under_data(self) -> None:
        assert ND_DIR.parent == DATA_DIR
        assert ND_DIR.name == "ND"

    def test_streamlit_dir_is_under_root(self) -> None:
        assert STREAMLIT_DIR.parent == PROJECT_ROOT
        assert STREAMLIT_DIR.name == ".streamlit"

    def test_all_are_path_objects(self) -> None:
        for d in [DATA_DIR, MODELS_DIR, CACHE_DIR, ND_DIR, STREAMLIT_DIR]:
            assert isinstance(d, Path)
