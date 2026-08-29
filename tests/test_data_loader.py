"""Tests for Next-Gen-Reco data loader module.

Tests user data persistence and session state management.
"""

import json
from pathlib import Path
from unittest.mock import patch


class TestUserDataPersistence:
    """Test user data save/load cycle."""

    def test_load_user_data_creates_empty_state(self) -> None:
        with patch("app.data.loader.st") as mock_st:
            mock_st.session_state = {"user_ratings": {}, "watchlist": set(), "search_history": []}
            mock_st.session_state.setdefault = mock_st.session_state.get
            from app.data.loader import _load_user_data

            # Should not raise even with no file
            _load_user_data()

    def test_save_user_data_writes_json(self, tmp_path: Path) -> None:
        with patch("app.data.loader.USER_DATA_FILE", tmp_path / "test_user_data.json"):
            with patch("app.data.loader.st") as mock_st:
                mock_st.session_state = {
                    "user_ratings": {1: 5.0, 2: 4.0},
                    "watchlist": {1, 2},
                    "search_history": ["toy story"],
                }
                from app.data.loader import _save_user_data

                _save_user_data()
                data_file = tmp_path / "test_user_data.json"
                assert data_file.exists()
                data = json.loads(data_file.read_text())
                assert "ratings" in data

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        data_file = tmp_path / "roundtrip.json"
        with patch("app.data.loader.USER_DATA_FILE", data_file), patch("app.data.loader.st") as mock_st:
            mock_st.session_state = {
                "user_ratings": {10: 4.5},
                "watchlist": set(),
                "search_history": [],
            }
            from app.data.loader import _save_user_data

            _save_user_data()

            # Reset session state
            mock_st.session_state = {
                "user_ratings": {},
                "watchlist": set(),
                "search_history": [],
            }
            from app.data.loader import _load_user_data

            _load_user_data()
            assert mock_st.session_state["user_ratings"] == {10: 4.5}
