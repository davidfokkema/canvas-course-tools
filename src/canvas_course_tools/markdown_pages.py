"""TEST: Markdown page utilities for Canvas course tools."""

import pathlib

import mistune

markdown = mistune.create_markdown(
    plugins=["math", "footnotes", "superscript"],
)
print(markdown((pathlib.Path(__file__).parent / "testdoc.md").read_text()))
