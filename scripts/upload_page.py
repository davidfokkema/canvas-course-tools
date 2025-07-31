from canvas_course_tools.utils import find_course

canvas, course = find_course("test")
page = canvas.upload_markdown_page(
    course,
    content="""\
# HA fancy new page

This is a new fancy page.

## Section heading

### Subsection

```python
print("Hello, world!")
```

$$
E = mc^2
$$
""",
)
print(page)
