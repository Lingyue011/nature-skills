"""Optional Matplotlib defaults for civil-engineering manuscript figures.

The profile is intentionally opt-in. It changes presentation defaults only;
it does not inspect, transform, filter, or interpret scientific data.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Text

MM_PER_INCH = 25.4
TEST_BLACK = "#000000"
FE_DARK_RED = "#8B1E2D"
ZERO_GRAY = "#A6A6A6"
GRID_GRAY = "#808080"
PANEL_NAME_FONT_PT = 10.5


def mm_to_inches(value: float) -> float:
    """Convert a physical figure dimension in millimetres to inches."""
    return value / MM_PER_INCH


def single_panel_size_mm(height_mm: float = 62.0) -> tuple[float, float]:
    """Return the adjustable single-panel default (about 85 mm wide)."""
    return 85.0, height_mm


def double_column_size_mm(height_mm: float = 160.0) -> tuple[float, float]:
    """Return the adjustable composite default (about 178 mm wide)."""
    return 178.0, height_mm


def apply_civil_engineering_style(
    *, base_font_size: float = 11.0, axis_label_size: float = 13.0,
    tick_label_size: float = 10.5, legend_size: float = 12.0,
) -> None:
    """Set compact TNR defaults; callers may override sizes per figure."""
    from matplotlib.font_manager import findfont

    findfont("Times New Roman", fallback_to_default=False)
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "mathtext.fontset": "stix",
        "font.size": base_font_size,
        "axes.labelsize": axis_label_size,
        "axes.titlesize": base_font_size,
        "xtick.labelsize": tick_label_size,
        "ytick.labelsize": tick_label_size,
        "legend.fontsize": legend_size,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID_GRAY,
        "grid.linestyle": "--",
        "grid.linewidth": 0.4,
        "grid.alpha": 1.0,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.linewidth": 0.9,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 4.0,
        "ytick.major.size": 4.0,
        "xtick.major.width": 0.85,
        "ytick.major.width": 0.85,
        "legend.frameon": False,
        "savefig.facecolor": "white",
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "lines.solid_capstyle": "butt",
        "lines.dash_capstyle": "butt",
    })


def style_closed_axes(ax: Axes, *, grid: bool = True) -> None:
    """Use closed axes, inward ticks, and the saved gray major-grid default."""
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.9)
        spine.set_color("black")
    ax.tick_params(which="both", direction="in", top=True, right=True,
                   labeltop=False, labelright=False, labelbottom=True,
                   labelleft=True)
    ax.set_axisbelow(True)
    ax.grid(False, which="minor")
    if grid:
        ax.grid(True, which="major", axis="both", color=GRID_GRAY,
                linestyle=(0, (3, 3)), linewidth=0.4, alpha=1.0)
    else:
        ax.grid(False, which="both")


def style_test_fe_lines(ax: Axes) -> None:
    """Apply the familiar Test/FE encoding only when those labels are present."""
    for line in ax.lines:
        label = line.get_label().strip().casefold()
        if label == "test":
            line.set_color(TEST_BLACK)
            line.set_linestyle("-")
        elif label == "fe":
            line.set_color(FE_DARK_RED)
            line.set_linestyle((0, (7, 3)))


def add_zero_reference(ax: Axes, *, meaningful: bool = True) -> Line2D | None:
    """Add a subtle zero line only when zero has meaning for the response."""
    if not meaningful:
        return None
    return ax.axhline(0.0, color=ZERO_GRAY, linestyle=(0, (3, 2)),
                      linewidth=0.8, zorder=0)


def add_panel_id(
    ax: Axes, text: str, *, y: float = -0.38,
    fontsize: float = PANEL_NAME_FONT_PT,
) -> Text:
    """Seed a prominent panel name; pack_composite_layout fixes its physical gap."""
    return ax.text(0.5, y, text, transform=ax.transAxes,
                   ha="center", va="top", clip_on=False, fontsize=fontsize)


def add_shared_legend(
    fig: Figure, handles: Sequence[Line2D], labels: Sequence[str], *,
    y: float = 0.99, fontsize: float = 12.0,
) -> object:
    """Add a visibly large, full-canvas centered horizontal legend."""
    return fig.legend(handles, labels, loc="upper center",
                      bbox_to_anchor=(0.5, y), ncol=max(1, len(labels)),
                      frameon=False, fontsize=fontsize, handlelength=2.8,
                      columnspacing=1.6, handletextpad=0.6)


def save_png(fig: Figure, path: str | Path, *, dpi: int = 600) -> None:
    """Write PNG at the declared canvas size without vector sidecars."""
    fig.savefig(path, dpi=dpi, facecolor="white")


def audit_rendered_layout(
    fig: Figure, axes: Iterable[Axes], *, panel_ids: Sequence[Text] = (),
    shared_legend: object | None = None, tolerance_px: float = 4.0,
) -> list[str]:
    """Check rendered centering, bounds, and collisions; return review findings."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    canvas = (0.0, 0.0, float(width), float(height))
    axes_list = list(axes)
    axis_boxes = [ax.get_window_extent(renderer) for ax in axes_list]
    findings: list[str] = []

    def within_canvas(box, name: str) -> None:
        if (box.x0 < 0 or box.y0 < 0 or box.x1 > canvas[2]
                or box.y1 > canvas[3]):
            findings.append(f"{name} extends beyond the canvas")

    for index, text in enumerate(panel_ids, start=1):
        box = text.get_window_extent(renderer)
        within_canvas(box, f"panel ID {index}")
        if index <= len(axes_list):
            ax = axes_list[index - 1]
            center_delta = abs((box.x0 + box.x1) / 2 - ax_center(text, axis_boxes, index - 1))
            if center_delta > tolerance_px:
                findings.append(f"panel ID {index} is not centered under its panel")
            xlabel_box = ax.xaxis.label.get_window_extent(renderer)
            if box.overlaps(xlabel_box) or box.y1 >= xlabel_box.y0:
                findings.append(f"panel ID {index} has no clear gap below its x-axis title")
        if any(box.overlaps(axis_box) for axis_box in axis_boxes):
            findings.append(f"panel ID {index} overlaps a plot area")

    if shared_legend is not None:
        box = shared_legend.get_window_extent(renderer)
        within_canvas(box, "shared legend")
        if abs((box.x0 + box.x1) / 2 - width / 2) > tolerance_px:
            findings.append("shared legend is not centered over the full canvas")
        if any(box.overlaps(axis_box) for axis_box in axis_boxes):
            findings.append("shared legend overlaps a plot area")
    return findings


def ax_center(text: Text, axis_boxes, index: int) -> float:
    """Resolve the corresponding axes center for layout auditing."""
    return (axis_boxes[index].x0 + axis_boxes[index].x1) / 2

def audit_png_output(
    fig: Figure, path: str | Path, axes: Iterable[Axes], *,
    panel_ids: Sequence[Text] = (), shared_legend: object | None = None,
    dpi: int = 300, min_font_pt: float = 8.0,
) -> dict[str, object]:
    """Audit a saved PNG using Matplotlib text/axes geometry, without PDF tools.

    PDF glyph-stream, PDF stroke-collision, vector-editability, and TIFF checks
    are reported as not applicable for the PNG-only civil-engineering profile.
    """
    from matplotlib.font_manager import findfont
    from PIL import Image

    png_path = Path(path)
    axes_list = list(axes)
    issues = audit_rendered_layout(fig, axes_list, panel_ids=panel_ids,
                                  shared_legend=shared_legend)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas_width, canvas_height = fig.canvas.get_width_height()
    tick_ids: set[int] = set()
    active_tick_ids: set[int] = set()
    for ax in axes_list:
        for axis, limits in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
            lower, upper = sorted(float(value) for value in limits)
            for tick in axis.get_major_ticks():
                location = float(tick.get_loc())
                for label in (tick.label1, tick.label2):
                    tick_ids.add(id(label))
                    if lower <= location <= upper and label.get_visible():
                        active_tick_ids.add(id(label))
    text_artists = [
        text for text in fig.findobj(match=Text)
        if text.get_visible() and text.get_text().strip()
        and (id(text) not in tick_ids or id(text) in active_tick_ids)
    ]
    bounds_issues: list[str] = []
    overlaps: list[str] = []
    font_size_issues: list[str] = []
    fonts: set[str] = set()
    font_sizes: list[float] = []
    text_boxes: list[tuple[str, object]] = []
    tnr_path = Path(findfont("Times New Roman", fallback_to_default=False)).resolve()

    for index, text in enumerate(text_artists, start=1):
        box = text.get_window_extent(renderer)
        label = text.get_text().replace("\n", " ")[:48] or f"text {index}"
        if (box.x0 < 0 or box.y0 < 0 or box.x1 > canvas_width
                or box.y1 > canvas_height):
            bounds_issues.append(f"text outside PNG canvas: {label}")
        font_sizes.append(float(text.get_fontsize()))
        if float(text.get_fontsize()) < min_font_pt:
            font_size_issues.append(
                f"text below minimum font size {min_font_pt:g} pt: "
                f"{label} ({float(text.get_fontsize()):g} pt)"
            )
        resolved = Path(findfont(text.get_fontproperties(),
                                 fallback_to_default=False)).resolve()
        fonts.add(resolved.name)
        if resolved != tnr_path:
            bounds_issues.append(f"non-Times-New-Roman text font: {label} ({resolved.name})")
        text_boxes.append((label, box))

    for i, (first_label, first_box) in enumerate(text_boxes):
        for second_label, second_box in text_boxes[i + 1:]:
            if first_box.overlaps(second_box):
                overlaps.append(f"text boxes overlap: {first_label} / {second_label}")

    image_format = None
    image_size_px: tuple[int, int] | None = None
    image_dpi: tuple[float, float] | None = None
    image_issues: list[str] = []
    if not png_path.is_file():
        image_issues.append(f"PNG output does not exist: {png_path.name}")
    else:
        with Image.open(png_path) as image:
            image_format = image.format
            image_size_px = tuple(int(value) for value in image.size)
            dpi_value = image.info.get("dpi")
            if isinstance(dpi_value, tuple) and len(dpi_value) >= 2:
                image_dpi = (float(dpi_value[0]), float(dpi_value[1]))
            if image_format != "PNG":
                image_issues.append(f"expected PNG output, found {image_format}")
            expected_size = tuple(
                round(float(value) * dpi) for value in fig.get_size_inches()
            )
            if any(abs(actual - expected) > 1 for actual, expected in zip(image_size_px, expected_size)):
                image_issues.append(
                    f"PNG pixels {image_size_px} do not match canvas/DPI {expected_size}"
                )
            if image_dpi is None:
                image_issues.append("PNG DPI metadata is missing")
            elif any(abs(value - dpi) > 1.0 for value in image_dpi):
                image_issues.append(f"PNG DPI metadata {image_dpi} does not match {dpi}")

    all_findings = [*issues, *bounds_issues, *font_size_issues, *overlaps, *image_issues]
    expected_width_mm = float(fig.get_size_inches()[0]) * MM_PER_INCH
    expected_height_mm = float(fig.get_size_inches()[1]) * MM_PER_INCH
    return {
        "profile": "civil-engineering",
        "output_format": image_format,
        "output_path": str(png_path),
        "pixel_size": image_size_px,
        "physical_size_mm": [round(expected_width_mm, 2), round(expected_height_mm, 2)],
        "dpi": image_dpi,
        "font_family": "Times New Roman",
        "resolved_fonts": sorted(fonts),
        "minimum_text_artist_size_pt": round(min(font_sizes), 2) if font_sizes else None,
        "minimum_font_size_pt": min_font_pt,
        "minimum_font_size_check": (
            "PASS" if not any(size < min_font_pt for size in font_sizes) else "FAIL"
        ),
        "text_artist_count": len(text_artists),
        "matplotlib_renderer_bounds": "PASS" if not bounds_issues else "FAIL",
        "text_bbox_collisions": "PASS" if not overlaps else "FAIL",
        "panel_legend_layout": "PASS" if not issues else "FAIL",
        "png_file_and_dimensions": "PASS" if not image_issues else "FAIL",
        "not_applicable": {
            "mathtext_script_glyph_floor": (
                "N/A: Matplotlib artist sizes report parent text; no PDF glyph stream is created"
                if any(re.search(r"\$[^$]*[\^_]", text.get_text()) for text in text_artists)
                else "N/A: no mathtext superscript/subscript glyphs are present"
            ),
            "pdf_glyph_stream_audit": "N/A: PNG-only profile; no PDF intermediate is required",
            "pdf_stroke_collision_audit": "N/A: PDF geometry is not part of this profile; renderer text and axes bounds are checked",
            "vector_editability": "N/A: no vector export requested",
            "tiff_export": "N/A: TIFF is not a default deliverable in this profile",
        },
        "findings": all_findings,
    }
