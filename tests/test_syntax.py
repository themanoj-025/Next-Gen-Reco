import nbformat as nbf
import structlog

logger = structlog.get_logger("test_syntax")


def md_cell(source) -> nbf.NotebookNode:
    cell: nbf.NotebookNode = nbf.v4.new_markdown_cell(source)
    return cell


def nb_cell(source) -> nbf.NotebookNode:
    cell: nbf.NotebookNode = nbf.v4.new_code_cell(source)
    return cell


cells1 = []
cells1.append(
    md_cell(
        """# MovieLens Dataset Analysis

---"""
    )
)
cells1.append(nb_cell("""import pandas as pd"""))
logger.info("cells_created", count=len(cells1))
