# Civil-engineering project profile

Use this optional profile for paper figures in OpenSees-PEF, SCI5-CFSTsteelReBuild, and OpenSees-Slab, or when the user explicitly requests these civil-engineering defaults. It governs presentation only. Keep the generic Nature figure contract, evidence logic, integrity checks, and target-journal requirements in force. Do not apply this profile to unrelated projects.

## Backend and exports

- Use Python/Matplotlib by default for these projects. Honor an explicit request for another backend; otherwise do not ask the user to choose Python or R.
- Export PNG by default. Create PDF, SVG, TIFF, or other formats only when requested or required by a verified target-journal contract. Follow the scoped PNG quality-assurance path in `references/qa-contract.md`; do not run vector-only preflight requirements on this route.
- Keep the plotting script and source tables needed to reproduce the figure with the PNG. Never replace or delete earlier versions without authorization.

## Adjustable visual defaults

- Use Times New Roman for English text and numbers, italic variables with upright units, a white background, four visible axes spines, and inward major ticks on all four sides. Show numeric tick labels only on the left and bottom. Do not add a grid by default.
- A standalone panel may be about 85 mm wide. A 2x2 overview may be about 175-180 mm wide at double-column size; preserve each panel's final-size lettering and a useful plot area. These are starting points, not fixed limits. Choose physical dimensions and font sizes for the journal and content.
- Keep every rendered text artist at or above 8 pt by default for final-size print readability. `audit_png_output(..., min_font_pt=...)` exposes this as an adjustable floor; use an explicit threshold when the journal or figure geometry calls for another value. The larger style defaults (for example 10.5 pt ticks and 13 pt axis labels) remain preferred starting points.
- Test/FE comparisons may use solid black for Test and long-dashed dark red for FE. Apply this encoding only when those series are present. Do not recolor unrelated series.
- For composites, center each panel ID and short group label below its x-axis title. Use a small readable gap and enough vertical clearance before the next row. Center a shared legend over the full canvas; about 14 pt is a starting point where it fits. Use compact outer margins and row/column spacing without shrinking the panels or their labels.
- Use a subtle short-dashed gray zero line only when zero is meaningful. Avoid decorative titles. Measure rendered label and legend bounds and check for clipping, overlap, and centering.

## Data and claims

Preserve measured values, including unfavorable segments. Document suspected measurement-channel issues in the figure note or README; do not silently trim, smooth, or filter them. Do not invent data, mechanisms, or scientific conclusions. Project-specific thresholds (including any LT ranges) belong only to the relevant task and must never become global figure rules.

## Reusable helper

For new Python figures, import `apply_civil_engineering_style`, `style_closed_axes`, `style_test_fe_lines`, `add_panel_id`, `add_shared_legend`, `audit_rendered_layout`, `audit_png_output`, and `save_png` from `scripts/civil_engineering_style.py`. Treat its physical sizes and type sizes as adjustable defaults. Call `audit_png_output()` after saving the final PNG while the Matplotlib figure is still available; it returns renderer-bounds, minimum-font, font, layout, text-box collision, raster-size, and DPI findings plus explicit `N/A` fields for PDF/vector/TIFF-only checks. The renderer audit does not detect a plotted curve crossing through a text label. Always inspect the final PNG at physical size and reposition labels when curves obscure them; automated checks do not replace visual QA. The helper only changes presentation and audits rendered artists; it does not read or transform input data.
