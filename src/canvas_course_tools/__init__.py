import importlib.metadata

try:
    __version__ = importlib.metadata.version("canvas_course_tools")
except importlib.metadata.PackageNotFoundError:
    __version__ = None
