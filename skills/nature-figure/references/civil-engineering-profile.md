# Civil-engineering project profile

Use this saved user profile for paper figures in OpenSees-PEF, SCI5-CFSTsteelReBuild, SCI5-1_Wsection, and OpenSees-Slab, or when the user requests their civil-engineering SCI style. It governs presentation only; retain the general figure contract, data integrity, and verified target-journal requirements. Do not apply it to unrelated projects. Current task instructions take precedence over these defaults.

## Backend and delivery

- Use Python/Matplotlib by default within this scope; honor an explicit backend choice without asking again.
- Default to a 600-dpi PNG manuscript figure and a smaller PNG preview. Produce PDF, SVG, or TIFF when requested or required by the verified journal contract. Follow the scoped PNG QA route; vector-only checks are N/A for PNG-only delivery.
- Keep reproducible plotting code, source data or immutable source references, and QA/provenance records. Save requested alternative designs as separate versions. Preserve existing versions.
- Follow the requested panel arrangement; a 4-row by 3-column plate is a task choice, not a universal template.

## Visual language

- Use Times New Roman for English text and numbers, italic variables, upright units, a white background, four visible spines, and inward ticks on all four sides. Label ticks only at the bottom and left.
- For Test/FE comparisons, use solid black Test (#000000) and long-dashed dark red FE (#8B1E2D), consistently across panels. Do not recolor unrelated series using this two-series mapping.
- Default to ordinary gray (#808080) dashed major grids on both axes, drawn behind the curves. A useful starting point is 0.4-pt lines, alpha 1, dash pattern (3, 3). Do not revert to very pale gray or no grid unless the current request calls for that.
- Use one shared, centered Test/FE legend above the plate. Center each panel letter and specimen name below its x-axis title, with a small readable gap and clear separation from the next row.
- Omit decorative titles, mesh metadata, internal QA badges, and workflow commentary from the manuscript image. Keep accompanying caption content to what the user requests; internal scientific checks and provenance remain separate and truthful.
- Use compact, balanced margins and adequate plot areas. About 85 mm for a standalone panel and 175-180 mm for a double-column composite are starting points, not fixed limits. Resolve dense plates with layout and sensible tick density before shrinking text. Check the actual intended publication size; do not assume an oversized canvas remains legible after reduction.
- Keep rendered text at least 8 pt by default, adjustable for an explicit journal/size contract. Font sizes, margins, and line weights should be consistent across a composite.

## Tight composite layout and text hierarchy

Use renderer-measured physical gaps as the primary control; use percentages only to report overall whitespace. An axes-relative caption position such as y=-0.30 does not specify the visible gap from the x-axis title and becomes too loose when panels grow.

Preferred adjustable starting values, accepted on a dense manuscript plate:

| Control | Starting value | Measurement |
|---|---|---|
| Outer padding | 0.6 mm on each side | Union of all rendered axes, tick labels, axis titles, specimen names and shared legend |
| X-axis title to panel name | 0.8 mm | Bottom of rendered x-label to top of specimen-name text |
| Adjacent row/column content clearance | At least 1.2 mm | Neighbouring full content bounds; maintain uniform repeated plot-frame gutters |
| Shared legend to panel region | 1.5 mm | Legend bottom to the highest rendered panel content |
| Panel letter and specimen name | 10.5 pt | Same font size across all panels, clearly more prominent than tick labels |

- The accepted text hierarchy starts at 8-pt tick labels, 9-pt axis titles, 10.5-pt panel letters/names and a 12-pt shared legend. Scale deliberately for the actual target size; do not shrink names to 8.5 pt merely because this is a dense composite.
- Increase specimen-name text first when it is too small, then repack and remeasure. Do not preserve an old axes-fraction offset or enlarge the inter-row gap arbitrarily.
- Preserve equal plot widths/heights and uniform repeated frame gutters. Because neighbouring tick labels occupy different widths/heights, content gaps are minimum clearances; they need not all be identical. Use the largest necessary neighbouring overhang to set the common frame gutter.
- Fit the final canvas to the union of rendered content plus the small padding. About 0.3% outer whitespace per side was accepted on the current plate; this is a consequence of the physical padding, not a mandatory percentage on every figure.
- Tighten the canvas and move whole axes blocks without shrinking plot areas or fonts. Include the bottom-row specimen names and outer tick labels when fitting the canvas; never crop them or erase white pixels after rasterization.
- `bbox_inches="tight"` alone only addresses outer whitespace; it does not repair xlabel/name gaps or inter-row gaps. If used, account for the resulting physical output dimensions in QA rather than reporting the original figure size.
- After changing fonts, labels or figure size, draw again, measure actual text bounds, pack the layout, then run alignment and PNG audits. Do not hide a font collision by weakening the alignment tolerance.
- Use `pack_composite_layout()` from `scripts/civil_engineering_layout.py` for an equal-panel rectangular grid. It preserves the physical size of the existing plot rectangles, positions names from actual x-label bounds, aligns common gutters, centers the legend and fits the canvas. It returns measured gaps and output dimensions for the QA record. Intentional unequal-span grids, colorbars, insets or extra figure-level notes require their own layout contract; do not force them into this helper.

## Coordinate decisions: comparability first, economical whitespace second

Decide x and y groups independently. Do not use one grouping decision to bind both axes automatically.

- For specimens from the same paper or a meaningful comparison family, prefer a shared load-response axis (force, moment, stress, etc.), using the same limits and ticks. A lower-capacity specimen then legitimately occupies less vertical space: that is visible evidence of a capacity difference, not automatically a layout defect. Different sections or loading histories alone do not justify independently magnifying each response axis. Honor explicit user choices about which responses share a scale.
- Group displacement/rotation axes by actual loading history and range. Comparable cyclic protocols share limits and ticks. Markedly biased, one-sided, or longer protocols may use a separate x group while retaining the shared response-axis scale.
- For a specimen with no meaningful same-protocol comparator, use its own compact x range. Do not borrow an unnecessarily wide range merely because another specimen has the same author.
- Preserve comparable units and axis definitions. A moment curve remains moment, even when the user informally calls it horizontal load; never relabel M as F or manufacture a conversion.
- Use the complete Test and FE extents together to choose each group's axis limits. Add a modest visual margin; never clip or discard curve segments to make the plot fill the frame.
- Choose readable, regular major tick intervals separately from axis limits. Labelled ticks do NOT have to bracket every extreme. Curves may extend slightly beyond the last labelled tick while remaining completely inside the frame. Do not add an awkward boundary number just to enclose the data.
- Prefer simple numeric labels and useful reference levels over unnecessary scientific notation. For example, a response slightly above 3000 can retain a 3000 last label; do not force a 3500 or 4000 label. An extreme near -0.129 rad may have -0.12 as the leftmost labelled tick with an axis limit a little farther left; -0.16 need not appear.
- Remove redundant endpoint labels such as 0.055 when regular interior ticks already support estimation. Keep tick density sufficient to judge the attained loading range without crowding.
- Do not optimize whitespace independently in every panel at the cost of the requested comparison. When common scales leave substantial empty area, first reconsider the physical comparison groups; do not silently abandon the shared response scale.

### Examples from the accepted twelve-specimen plate

These illustrate grouping decisions, not reusable numeric limits:

- Elkady C1/C2/C3/C7 share the displacement/rotation group; C5/C8 share a separate biased-loading group. Same response units and comparable capacity scales support reading the differences. Retain the user's selected grouping and adjust limits to the current complete data.
- Suzuki W-6-34-C1-C uses its own compact, markedly negative-biased x range. It need not show -0.16 when -0.12 adequately supports estimating its attained rotation. The three S-C specimens use their comparable x group.
- Cravero C3 and A3 retain different x ranges for their different loading histories but share the moment-axis range and ticks. Do not repeat the earlier independent vertical magnification of A3 simply to make its loop taller.

## Data, figure text, and validation

- Preserve all selected raw curve vertices and source definitions. Do not smooth, recenter, interpolate, decimate, alter signs, or trim unfavorable segments for appearance. Record any explicitly requested scientific transform accurately.
- Keep source identities, relevant uncertainties, and numerical QA in the supporting records. A request to omit QA warnings from the manuscript figure/caption does not authorize changing scientific gates or making unsupported validation claims. Avoid adding workflow caveats to a caption the user has requested to keep clean.
- Verify axis-limit containment of all Test/FE vertices, identical limits/ticks within each intended x/y group, exact data coordinates, and renderer geometry. Do NOT validate containment against the minimum/maximum labelled ticks: that would reintroduce the rejected boundary-label rule.
- Run the multi-panel alignment gate and PNG renderer audit, then visually check every panel, final-size labels, legend clearance, line/grid distinction, and the comparison conveyed by shared scales. A geometry pass does not replace that review.

## Reusable helper

Use the relevant functions in `scripts/civil_engineering_style.py`: `apply_civil_engineering_style`, `style_closed_axes`, `style_test_fe_lines`, `add_panel_id`, `add_shared_legend`, `save_png`, and `audit_png_output`. `add_panel_id()` now starts panel-name text at 10.5 pt; its y argument is only an initial seed before physical layout packing. `style_closed_axes(ax)` applies the ordinary gray major grid; `style_closed_axes(ax, grid=False)` honors an explicit grid-free request. The helper controls presentation only; axis grouping still requires the physical and task-context decisions above.

Call `audit_png_output()` after saving the PNG while its Matplotlib figure is available. Preserve the report and any panel-alignment report. The renderer checks text bounds, font floor, PNG size/DPI and layout; it does not detect every curve-text intersection. Keep PDF/vector/TIFF-only checks N/A unless those formats are part of the deliverable.
