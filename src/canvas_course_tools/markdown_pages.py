"""TEST: Markdown page utilities for Canvas course tools."""

import pathlib

import mistune
from bs4 import BeautifulSoup
from slugify import slugify

from canvas_course_tools.utils import find_course

markdown = mistune.create_markdown(
    plugins=["math", "footnotes", "superscript"],
)
html = markdown((pathlib.Path(__file__).parent / "testdoc.md").read_text())

canvas, course = find_course("test")

soup = BeautifulSoup(html, "html.parser")
h1 = soup.find("h1")
slug = slugify(h1.text)
h1.decompose()

print(soup)
