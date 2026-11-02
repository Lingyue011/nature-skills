# `civil-paraview-figures` Skill

[中文说明](README.md)

An independent skill for preparing civil-engineering manuscript figures from real finite-element meshes and results with ParaView and Matplotlib.

## What To Use It For

- Render finite-element displacement fields, combine oblique and side views, and check colour scales and viewing directions.
- Preserve geometric scale and traceability of nodes and field data.

## Typical Requests

- “Turn accepted finite-element results into a ParaView paper figure with an equal-scale side view.”

## What You Need To Provide

- Accepted mesh, displacement field, reference state, units, target time and output requirements.

## Outputs

- Reproducible presentation scripts, images, view states, provenance and quality-check records.

## Boundaries

- Rendering does not authorize a new solve, calibration or scientific data changes; rendering checks are not physical validation.
- The user's civil-engineering palette is a project preference, not a universal journal requirement; follow the actual submission requirements.

## Related Skills

- `nature-figure`: general scientific figures and ordinary curve plots.
