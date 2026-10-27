"""Helpers for consistently exporting labeled analysis figures."""

from pathlib import Path

from matplotlib.figure import Figure

from .config import SECTION_FIGURE_DIRS


def save_figure(
    figure: Figure,
    filename: str,
    section: int,
    *,
    title: str | None = None,
) -> Path:
    """Save a figure to its section folder at 300 DPI and return its path."""
    if section not in SECTION_FIGURE_DIRS:
        raise ValueError(f"section must be between 1 and 6; got {section}")
    if Path(filename).name != filename or not filename:
        raise ValueError("filename must be a non-empty file name, not a path")

    output_path = SECTION_FIGURE_DIRS[section] / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if title:
        figure.suptitle(title)
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    return output_path
