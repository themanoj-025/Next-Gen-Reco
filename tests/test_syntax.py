import nbformat as nbf


def md_cell(source):
    return nbf.v4.new_markdown_cell(source)


def nb_cell(source):
    return nbf.v4.new_code_cell(source)


cells1 = []
cells1.append(
    md_cell("""# MovieLens Dataset Analysis

---""")
)
cells1.append(nb_cell("""import pandas as pd"""))
print(f"OK: {len(cells1)} cells")
