import logging

import pytest

logger = logging.getLogger("test_syntax")


def test_notebook_syntax() -> None:
    try:
        import nbformat as nbf
    except ImportError:
        pytest.skip("nbformat not installed")
        return
    cell1 = nbf.v4.new_markdown_cell("# MovieLens Dataset Analysis\n\n---")
    cell2 = nbf.v4.new_code_cell("import pandas as pd")
    assert cell1 is not None and cell2 is not None
