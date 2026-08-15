"""
Fix regex patterns in create_notebook1.py and create_notebook2.py.

The current file has too many backslashes. The outer triple-quoted string
needs:  r'\\(\\d{4}\\)'
to produce the cell code: r'\\((\\d{4})\\)'

Which is a raw string whose value is: \\((\\d{4})\\)
This regex matches (YYYY) and captures YYYY.
"""

import re

# Fix create_notebook1.py
with open("create_notebook1.py", "r", encoding="utf-8") as f:
    content1 = f.read()

# Current pattern in the file (inside the triple-quoted string):
# r'\\\\\\\\(\\\\\\\\d{4}\\\\\\\)'  (waaay too many backslashes)
# After my last str_replace it became:
# r'\\\\(\\\\d{4}\\\\)'

# We need the OUTER string to contain: r'\\(\\d{4}\\)'
# This means the SOURCE file text should literally be: r'\\(\\d{4}\\)'

old = r"r'\\\\(\\\\d{4}\\\\)'"
new = r"r'\\(\\d{4}\\)'"

if old in content1:
    content1 = content1.replace(old, new)
    print("Notebook 1: Replaced pattern")
else:
    print("Notebook 1: Pattern NOT FOUND - checking for alternatives")
    # Let's find what patterns exist around str.extract
    for i, line in enumerate(content1.split("\n")):
        if "str.extract" in line:
            print(f"  Line {i + 1}: {line.strip()}")

with open("create_notebook1.py", "w", encoding="utf-8") as f:
    f.write(content1)

# Fix create_notebook2.py
with open("create_notebook2.py", "r", encoding="utf-8") as f:
    content2 = f.read()

if old in content2:
    content2 = content2.replace(old, new)
    print("Notebook 2: Replaced pattern")
else:
    print("Notebook 2: Pattern NOT FOUND - checking for alternatives")
    for i, line in enumerate(content2.split("\n")):
        if "str.extract" in line:
            print(f"  Line {i + 1}: {line.strip()}")

with open("create_notebook2.py", "w", encoding="utf-8") as f:
    f.write(content2)

# Verify by reading back
print()
print("Verification:")
with open("create_notebook1.py", "r", encoding="utf-8") as f:
    for line in f:
        if "str.extract" in line:
            line = line.strip()
            print(f"  Notebook1: {line}")
            # Extract the raw string portion between r' and '
            m_inner = re.search(r"r'(.+?)'", line)
            if m_inner:
                inner = m_inner.group(1)
                print(f"  Inner pattern: {inner!r}")

with open("create_notebook2.py", "r", encoding="utf-8") as f:
    for line in f:
        if "str.extract" in line:
            line = line.strip()
            print(f"  Notebook2: {line}")
            m_inner = re.search(r"r'(.+?)'", line)
            if m_inner:
                inner = m_inner.group(1)
                print(f"  Inner pattern: {inner!r}")

print()
print("Done!")
