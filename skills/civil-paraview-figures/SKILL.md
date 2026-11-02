---
name: civil-paraview-figures
description: Render real finite-element meshes and deformation fields in ParaView and compose civil-engineering manuscript figures with reliable colour bars, camera directions, and side views. Use for ParaView渲染、有限元变形云图、土木SCI位移图、轴测与平视合图; ordinary curve plots belong in a general scientific-figure workflow.
---

# Civil ParaView figures

Create reproducible figures from actual FE geometry and accepted fields. Use
`pvpython` for ParaView and Python/Matplotlib for compact composition. Respect
the user's chosen visual style; a palette or layout preference is not a journal
requirement. Rendering does not authorize a new solve, calibration, or push.

## Establish what the figure means

Before rendering, identify the source mesh, time/frame, node/element IDs, vector
units, displacement reference state, colour quantity and deformation factor.
Reuse established project choices instead of asking again. Distinguish:

- Total displacement from a single frame.
- An increment `U(t)-U(t0)` from the **same run**, matched by node tag.
- Signed vertical displacement `w`, absolute vertical displacement `abs(w)`,
  and vector magnitude `sqrt(Ux^2+Uy^2+Uz^2)`; these are different quantities.

Do not synthesize a full field from a measured centre displacement. Do not fill
a failed tail, fit deformations to a target curve, or subtract another run's
baseline. If the necessary field is absent, explain the missing observation;
seek a separately authorized recording rerun only when required.

Use immutable raw data and a new figure version directory. Hash the inputs;
check original node coordinates, connectivity, IDs, finite values, array units
and dimensions. Read the exported VTU back with VTK. Compare a known reference
node to the same-run recorder. A valid VTU or exit code is not FE acceptance.

## Render and choose colour

Read [ParaView recipes](references/paraview-recipes.md) for verified API patterns,
reference-state handling, scalar mapping and state portability.

Warp geometry using the reviewed displacement vector, normally in metres with
`ScaleFactor=1`. If geometry and vectors use different units, convert explicitly.
Report any visual amplification. Keep original signed vectors unchanged when
colouring with an absolute value.

For this user's civil deformation figures, the established magnitude convention
is blue → cyan → green → yellow → red, with larger absolute displacement red.
For a vertical response use `abs(w)` and label `Absolute vertical displacement,
|w| (mm)`; do not label it as 3D magnitude. Use a linear scale from zero to a
declared upper bound containing all values. A near-zero actual minimum does
not prevent a zero-origin colour bar. Retain the actual minimum in provenance.

When a signed response is requested, preserve its sign and choose an appropriate
map. For comparisons use a common stated range. Do not silently clip extrema.
ParaView and the composed colour bar must share scalar definition, units, RGB
control points, colour space, normalization and limits. RGB interpolation with
uniform five-stop points is easy to reproduce using Matplotlib `Normalize`.

## Camera, directions and side view

Save camera position, focal point, view-up, projection, parallel scale and image
size. Prefer orthographic projection for comparable views. A familiar oblique
view is not necessarily a mathematically isometric camera; describe it accurately.

When a view is labelled along +Y, orient it from negative Y toward positive Y,
with +Z upward and equal camera/focal Z for a horizontal view. Match actual
project axes; do not assume all structures use this convention.

Project X/Y direction arrows through the actual oblique camera. Use
`scripts/presentation_geometry.py` or VTK WorldToDisplay. Put the glyph in a
white corner and check it does not overlap mesh, title or colour bar. A direction
glyph has no implied origin in the physical structure unless explicitly placed.

For equal-scale stacked views, use the same viewport height and parallel scale,
the same horizontal crop, and the same rendered physical width. Preserve image
aspect. A shallow side view should remain shallow: stretching it vertically
contradicts a scale=1 label. If requested, provide an explicitly labelled
exaggerated inset separately. Record pixels/metre and final panel dimensions.

To make central sag legible, a thin dashed original-midsurface reference and a
signed centre annotation may help. The reference is not automatically a support
line. A highlighted centre row must connect actual selected nodes after adding
their actual vectors, without fitting; identify that row and do not call it the
whole slab envelope. Side-view occlusion can otherwise hide the centre.

## Composition and delivery

Use white backgrounds, Times New Roman for English/numbers, italic variables,
upright units and a readable right-side colour bar when suitable. Default to
600-dpi PNG plus a preview. At the intended placement width aim for at least
10-pt effective text; DPI alone does not make text larger. Compute effective
font size from the **final fitted canvas width**, not the initial figure size.

Minimize whitespace using rendered bounds and small physical padding, while
preserving plot areas, aspect and text clearance. Crop only exterior background;
check no non-background pixels were lost. Do not add (a)/(b) or repeated view
titles when the user is placing this image within an already labelled panel.
For this user's combined deformation image, X/Y arrows and `View along +Y`
replace redundant subpanel labels.

Inspect the actual preview for direction, sag sign, colour meaning, clipping and
overlap. For stacked comparable views verify equal widths/column edges and
document intentional unequal heights. If the installed `nature-figure` civil
profile is available, reuse its PNG/font and panel-alignment helpers; otherwise
measure those properties directly and preserve the results. Do not claim a QA
pass for a check that was not run.

Keep scripts, raw renders, VTU/source hashes, PVSM, preview, final PNG and a short
caption/QA record. Ensure PVSM input paths actually resolve; use data relocation
or precise path substitutions for a moved version. Inspect path substitutions
without rewriting unrelated state. Keep publication code/text separate from
large raw fields/images when the user excludes those from Git.

Read [HD12 worked lessons](references/hd12-lessons.md) only for the motivating
case, failure modes and concrete validation examples. Its mesh, camera and
material choices are examples, not defaults for other studies.
