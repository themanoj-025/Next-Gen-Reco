"""Tests for Next-Gen-Reco data loader module.

Tests user data persistence and session state management.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


class _SessionState:
    """Minimal stand-in for streamlit's ``SessionStateProxy``.

    Supports the attribute access, ``in`` checks, ``.get`` and ``.setdefault``
    that ``app/data/loader.py`` relies on.
    """

    def __init__(self, **data: object) -> None:
        self.__dict__.update(data)

    def __contains__(self, key: object) -> bool:
        return key in self.__dict__

    def __getitem__(self, key: str) -> object:
        return self.__dict__[key]

    def __setitem__(self, key: str, value: object) -> None:
        self.__dict__[key] = value

    def get(self, key: str, default: object = None) -> object:
        return self.__dict__.get(key, default)

    def setdefault(self, key: str, default: object = None) -> object:
        return self.__dict__.setdefault(key, default)


class TestUserDataPersistence:
    """Test user data save/load cycle."""

    def test_load_user_data_creates_empty_state(self) -> None:
        with patch("app.data.loader.st") as mock_st:
            mock_st.session_state = _SessionState(user_ratings={}, watchlist={}, search_history=[])
            from app.data.loader import _load_user_data

            # Should not raise even with no file
            _load_user_data()

    def test_save_user_data_writes_json(self, tmp_path: Path) -> None:
        with patch("app.data.loader.USER_DATA_FILE", tmp_path / "test_user_data.json"):
            with patch("app.data.loader.st") as mock_st:
                mock_st.session_state = _SessionState(
                    user_ratings={1: 5.0, 2: 4.0},
                    watchlist={1: "Want to Watch", 2: "Want to Watch"},
                    search_history=[("toy story", datetime(2024, 1, 1, 12, 0))],
                )
                from app.data.loader import _save_user_data

                _save_user_data()
                data_file = tmp_path / "test_user_data.json"
                assert data_file.exists()
                data = json.loads(data_file.read_text())
                assert "ratings" in data
                assert data["ratings"] == {"1": 5.0, "2": 4.0}
                assert data["watchlist"] == {
                    "1": "Want to Watch",
                    "2": "Want to Watch",
                }
                assert data["search_history"] == [["toy story", "2024-01-01T12:00:00"]]

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        data_file = tmp_path / "roundtrip.json"
        with (
            patch("app.data.loader.USER_DATA_FILE", data_file),
            patch("app.data.loader.st") as mock_st,
        ):
            mock_st.session_state = _SessionState(
                user_ratings={10: 4.5},
                watchlist={10: "Want to Watch"},
                search_history=[],
            )
            from app.data.loader import _save_user_data

            _save_user_data()

            # Reset session state
            mock_st.session_state = _SessionState(user_ratings={}, watchlist={}, search_history=[])
            from app.data.loader import _load_user_data

            _load_user_data()
            assert mock_st.session_state["user_ratings"] == {10: 4.5}
            assert mock_st.session_state["watchlist"] == {10: "Want to Watch"}
