"""Render two small synthetic PNGs for the optional civil-engineering profile.

The curves are invented for layout QA only and are not scientific evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from civil_engineering_style import (
    add_panel_id,
    add_shared_legend,
    apply_civil_engineering_style,
    audit_png_output,
    double_column_size_mm,
    mm_to_inches,
    save_png,
    single_panel_size_mm,
    style_closed_axes,
    style_test_fe_lines,
)


def make_single(output: Path, dpi: int = 300) -> None:
    apply_civil_engineering_style()
    width, height = single_panel_size_mm()
    fig, ax = plt.subplots(figsize=(mm_to_inches(width), mm_to_inches(height)))
    x = np.linspace(0.0, 1.0, 100)
    ax.plot(x, 0.18 + 0.70 * x - 0.12 * x**2, label="Test")
    ax.plot(x, 0.16 + 0.66 * x - 0.09 * x**2, label="FE")
    style_test_fe_lines(ax)
    style_closed_axes(ax)
    ax.set_xlabel("Normalized displacement")
    ax.set_ylabel("Normalized response")
    ax.legend(loc="upper left")
    fig.subplots_adjust(left=0.19, right=0.97, bottom=0.20, top=0.97)
    save_png(fig, output, dpi=dpi)
    report = audit_png_output(fig, output, [ax], dpi=dpi)
    plt.close(fig)
    if report["findings"]:
        raise RuntimeError("Single-panel QA: " + "; ".join(report["findings"]))
    print(json.dumps(report, ensure_ascii=False))


def make_composite(output: Path, dpi: int = 300) -> None:
    apply_civil_engineering_style()
    width, height = double_column_size_mm(height_mm=173.0)
    fig, axes = plt.subplots(2, 2, figsize=(mm_to_inches(width), mm_to_inches(height)))
    x = np.linspace(0.0, 1.0, 100)
    handles = [
        Line2D([], [], color="#3A6EA5", linewidth=1.8, label="Method A"),
        Line2D([], [], color="#D17C28", linewidth=1.8, linestyle="--", label="Method B"),
    ]
    ids = []
    labels = ["(a) response", "(b) stiffness", "(c) energy", "(d) residual"]
    for i, (ax, panel_label) in enumerate(zip(axes.flat, labels)):
        a = (0.25 + 0.12 * i) * np.exp(-x * (1.2 + 0.15 * i))
        b = (0.23 + 0.10 * i) * np.exp(-x * (1.0 + 0.18 * i))
        ax.plot(x, a, color="#3A6EA5", linewidth=1.8, label="Method A")
        ax.plot(x, b, color="#D17C28", linewidth=1.8, linestyle="--", label="Method B")
        style_closed_axes(ax)
        ax.set_xlabel("Normalized time")
        ax.set_ylabel("Synthetic quantity")
        ids.append(add_panel_id(ax, panel_label, y=-0.48))
    legend = add_shared_legend(fig, handles, ["Method A", "Method B"], y=0.985)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.18, top=0.90,
                        wspace=0.30, hspace=0.68)
    save_png(fig, output, dpi=dpi)
    report = audit_png_output(fig, output, list(axes.flat), panel_ids=ids,
                              shared_legend=legend, dpi=dpi)
    plt.close(fig)
    if report["findings"]:
        raise RuntimeError("Composite QA: " + "; ".join(report["findings"]))
    print(json.dumps(report, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "assets" / "civil-engineering-demo")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    make_single(args.output_dir / "synthetic-single-panel.png", dpi=args.dpi)
    make_composite(args.output_dir / "synthetic-2x2-method-comparison.png", dpi=args.dpi)
    print(f"Wrote two synthetic PNGs to {args.output_dir}")


if __name__ == "__main__":
    main()