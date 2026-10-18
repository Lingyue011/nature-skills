"""Pack a civil-engineering equal-panel grid using rendered physical gaps.

Presentation only: no data loading, coordinate transforms or scientific filtering.
"""
from __future__ import annotations

import math
import numpy as np
from matplotlib.transforms import Bbox


def pack_composite_layout(
    fig, axes, panel_ids, legend, *, outer_padding_mm=0.6,
    xlabel_to_panel_name_mm=0.8, row_content_gap_mm=1.2,
    column_content_gap_mm=1.2, legend_to_panels_mm=1.5,
    tolerance_mm=0.05,
):
    """Pack an equal-cell rectangular grid with a shared top legend.

    axes must be a nonempty 2-D rectangular matrix; panel_ids is its row-major
    sequence of text artists created with va='top', ha='center' and ax.transAxes.
    Use a normal upper-center shared legend. Unequal cells, extra figure text,
    colorbars and insets require a different layout. Run the alignment and PNG
    audits afterwards. Existing plot-area dimensions and text sizes are retained.
    """
    axes = np.asarray(axes, dtype=object)
    if axes.ndim != 2 or not axes.size:
        raise ValueError('axes must be a nonempty two-dimensional grid')
    nrows, ncols = axes.shape
    if len(panel_ids) != axes.size:
        raise ValueError('one panel-name Text artist is required per axes')
    if set(map(id, fig.axes)) != set(map(id, axes.flat)) or fig.texts:
        raise ValueError('extra axes or figure text need a dedicated layout contract')
    if legend not in fig.legends or len(fig.legends) != 1:
        raise ValueError('exactly one figure-level shared legend is required')
    spacing = {
        'outer_padding': outer_padding_mm,
        'xlabel_to_panel_name': xlabel_to_panel_name_mm,
        'row_content_gap': row_content_gap_mm,
        'column_content_gap': column_content_gap_mm,
        'legend_to_panels': legend_to_panels_mm,
    }
    if any(not math.isfinite(v) or v < 0 for v in spacing.values()):
        raise ValueError('physical gaps must be finite and nonnegative')
    if not math.isfinite(tolerance_mm) or tolerance_mm <= 0:
        raise ValueError('tolerance_mm must be finite and positive')
    if any(ax.get_aspect() != 'auto' for ax in axes.flat):
        raise ValueError('fixed-aspect axes need a dedicated layout contract')
    for ax, name in zip(axes.flat, panel_ids):
        if name.axes is not ax or name.get_transform() is not ax.transAxes:
            raise ValueError('panel names must use their corresponding ax.transAxes')
        if name.get_va() != 'top' or name.get_ha() != 'center':
            raise ValueError('panel names must have va=top and ha=center')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    sizes = [(ax.get_window_extent(renderer).width, ax.get_window_extent(renderer).height)
             for ax in axes.flat]
    if any(abs(v[i] - sizes[0][i]) / fig.dpi * 25.4 > tolerance_mm
           for v in sizes for i in (0, 1)):
        raise ValueError('all plot rectangles must have equal physical size')
    # Freeze measured rectangles before manual physical packing.
    positions = [ax.get_position().frozen() for ax in axes.flat]
    fig.set_layout_engine('none')
    for ax, position in zip(axes.flat, positions):
        ax.set_position(position)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px_per_mm = fig.dpi / 25.4
    axes_list = list(axes.flat)
    # Anchor each caption to the actual x-label bottom, not axes height.
    for ax, caption in zip(axes_list, panel_ids):
        box = ax.xaxis.label.get_window_extent(renderer)
        point = (ax.get_window_extent(renderer).x0 + ax.get_window_extent(renderer).width / 2,
                 box.y0 - spacing['xlabel_to_panel_name'] * px_per_mm)
        caption.set_position(ax.transAxes.inverted().transform(point))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def content_box(ax):
        index = axes_list.index(ax)
        return Bbox.union([ax.get_tightbbox(renderer),
                           panel_ids[index].get_window_extent(renderer)])

    # Compute a common physical gutter from the largest neighbouring overhangs.
    # This preserves equal plot rectangles and equal repeated frame spacing.
    columns = [axes[:, i] for i in range(ncols)]
    column_gaps = []
    for c in range(1, ncols):
        right_overhang = max(content_box(ax).x1 - ax.get_window_extent(renderer).x1
                             for ax in columns[c - 1])
        left_overhang = max(ax.get_window_extent(renderer).x0 - content_box(ax).x0
                            for ax in columns[c])
        column_gaps.append(right_overhang + left_overhang
                           + spacing['column_content_gap'] * px_per_mm)
    column_frame_gap = max(column_gaps, default=0.0)
    for c in range(1, ncols):
        previous_right = axes[0, c - 1].get_window_extent(renderer).x1
        current_left = axes[0, c].get_window_extent(renderer).x0
        delta = previous_right + column_frame_gap - current_left
        for ax in columns[c]:
            p = ax.get_position().frozen()
            ax.set_position([p.x0 + delta / fig.bbox.width, p.y0, p.width, p.height])
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    row_gaps = []
    for r in range(1, nrows):
        bottom_overhang = max(ax.get_window_extent(renderer).y0 - content_box(ax).y0
                              for ax in axes[r - 1])
        top_overhang = max(content_box(ax).y1 - ax.get_window_extent(renderer).y1
                           for ax in axes[r])
        row_gaps.append(bottom_overhang + top_overhang
                        + spacing['row_content_gap'] * px_per_mm)
    row_frame_gap = max(row_gaps, default=0.0)
    for r in range(1, nrows):
        previous_bottom = axes[r - 1, 0].get_window_extent(renderer).y0
        current_top = axes[r, 0].get_window_extent(renderer).y1
        delta = previous_bottom - row_frame_gap - current_top
        for ax in axes[r]:
            p = ax.get_position().frozen()
            ax.set_position([p.x0, p.y0 + delta / fig.bbox.height, p.width, p.height])
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    grid = Bbox.union([content_box(ax) for ax in axes_list])
    legend.borderaxespad = 0.0
    legend_height = legend.get_window_extent(renderer).height
    legend.set_bbox_to_anchor(((grid.x0 + grid.x1) / 2 / fig.bbox.width,
                              (grid.y1 + spacing['legend_to_panels'] * px_per_mm
                               + legend_height) / fig.bbox.height),
                             transform=fig.transFigure)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    full = Bbox.union([*[content_box(ax) for ax in axes_list],
                       legend.get_window_extent(renderer)])
    inverse = fig.dpi_scale_trans.inverted()
    full_in = full.transformed(inverse)
    axis_in = [ax.get_window_extent(renderer).transformed(inverse) for ax in axes_list]
    legend_in = legend.get_window_extent(renderer).transformed(inverse)
    padding = spacing['outer_padding'] / 25.4
    shift_x, shift_y = padding - full_in.x0, padding - full_in.y0
    width, height = full_in.width + 2 * padding, full_in.height + 2 * padding
    fig.set_size_inches(width, height, forward=True)
    for ax, box in zip(axes_list, axis_in):
        ax.set_position([(box.x0 + shift_x) / width, (box.y0 + shift_y) / height,
                         box.width / width, box.height / height])
    legend.set_bbox_to_anchor(((legend_in.x0 + legend_in.width / 2 + shift_x) / width,
                              (legend_in.y1 + shift_y) / height), transform=fig.transFigure)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px_per_mm = fig.dpi / 25.4
    actual_full = Bbox.union([*[content_box(ax) for ax in axes_list],
                              legend.get_window_extent(renderer)])
    actual = {
        'outer_mm': {
            'left': actual_full.x0 / px_per_mm,
            'right': (fig.bbox.width - actual_full.x1) / px_per_mm,
            'bottom': actual_full.y0 / px_per_mm,
            'top': (fig.bbox.height - actual_full.y1) / px_per_mm,
        },
        'xlabel_to_panel_name_mm': [
            (ax.xaxis.label.get_window_extent(renderer).y0 - caption.get_window_extent(renderer).y1) / px_per_mm
            for ax, caption in zip(axes_list, panel_ids)
        ],
        'row_content_gap_mm': [
            (min(content_box(ax).y0 for ax in axes[r - 1])
             - max(content_box(ax).y1 for ax in axes[r])) / px_per_mm
            for r in range(1, nrows)
        ],
        'column_content_gap_mm': [
            (min(content_box(ax).x0 for ax in columns[c])
             - max(content_box(ax).x1 for ax in columns[c - 1])) / px_per_mm
            for c in range(1, ncols)
        ],
        'legend_to_panels_mm': (legend.get_window_extent(renderer).y0
                                - max(content_box(ax).y1 for ax in axes_list)) / px_per_mm,
    }
    for value in actual['outer_mm'].values():
        assert abs(value - spacing['outer_padding']) < tolerance_mm
    assert all(abs(value - spacing['xlabel_to_panel_name']) < tolerance_mm
               for value in actual['xlabel_to_panel_name_mm'])
    for key in ['row_content_gap', 'column_content_gap']:
        assert all(value >= spacing[key] - tolerance_mm for value in actual[key + '_mm'])
    assert abs(actual['legend_to_panels_mm'] - spacing['legend_to_panels']) < tolerance_mm
    return {'target_mm': spacing, 'measured': actual,
            'content_gaps_are_minima_for_equal_frame_gutters': True,
            'frame_gap_mm': {'horizontal': column_frame_gap / px_per_mm,
                             'vertical': row_frame_gap / px_per_mm},
            'physical_size_mm': [width * 25.4, height * 25.4],
            'outer_percent': {k: v / (width * 25.4 if k in ('left', 'right') else height * 25.4) * 100
                              for k, v in actual['outer_mm'].items()}}

