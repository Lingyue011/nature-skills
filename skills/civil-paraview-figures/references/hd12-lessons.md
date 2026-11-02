# HD12 worked lessons: observation rerun to manuscript image

This is one worked case, not a reusable FE calibration. The project retained
432 quadrilateral shells, 475 physical slab nodes, 48 compression-only supports
and seven concrete plus two smeared orthogonal reinforcement layers. Node263
was the displacement reference. Do not apply these IDs or layer counts elsewhere.

## Evidence chain

The original selected case lacked complete nodal fields. A separately authorized
observation-only Tcl modification recorded every accepted frame and fire_zero,
using committed nodal displacements. It did not change materials, temperatures,
constraints, algorithms or stepping. A 60s control preceded the complete10800s
run. Root checked the actual source/query path and runnable driver, not just
worker summaries.

The full run had392 accepted times and186200 six-DOF nodal records. Every non-wall
accepted-history value exactly reproduced the original frozen case. The entire
475-node600s snapshot also matched. Actual CPU4406.75s and wall5199.171s were
recorded. These establish numerical reproduction within the existing gates,
not independent physical accuracy of the entire deformation field.

A later disk-ejection report initially suggested restarting. Inspection showed
the run had already finished and all4181 release bindings/raw records were
intact. Reuse verified completed evidence instead of launching a redundant run.
An interruption never authorizes history splicing or pretending a partial result
is a complete state suitable for restart.

## Field and presentation decisions

The VTU subtracts each node's own same-run fire_zero translation from its180min
translation. It retains NodeTag, ElementTag, original mesh, total/zero/increment
vectors and signed vertical scalar. VTK readback checked all475nodes/432cells,
connectivity and actual scale1 warp. The centre fire increment is
-170.49667853489026mm; positive corner uplift reaches+100.8177143147673mm.
This uplift is a frozen-model prediction without independent local validation.
It was retained, not clipped to create a purely downward bowl.

The user changed a signed blue/white/red map to blue/cyan/green/yellow/red with
larger absolute displacement red. The selected scalar became abs(vertical fire
increment), not3D magnitude. All475Calculator values matched absolute original
values exactly. The actual absolute minimum is about5.44619e-7mm, with colour
bar0..170.496678535mm. Warp direction and scale stayed unchanged.

## Camera and side-view example

Oblique camera: position[-2.85,-9,12], focal[2.15,1.65,0], up[0,0,1],
parallel scale3.35, viewport3200x2200. This is an oblique view, not an exact
equal-axis isometric camera. Positive worldX projects to screen right/up
(0.9052035812,0.3034577683); positive worldY to(-0.4249782071,0.6463650464).
Put orientation arrows in white space using those directions, not generic XY.

Side camera: position[2.15,-9,-.03], focal[2.15,1.65,-.03], up+Z, same viewport
and scale. It looks horizontally along+Y from the near long edge. Equal source
crops and95mm output widths preserve equal physical scale; side panels remain
shallow. A highlighted line uses the25actual original-y=1.65nodes251..275 after
adding their own increments. Its end uplifts+12.86/+13.54mm were not forced to
zero. The originalz=0dashed reference is not a prescribed support line.

The final composition uses no(a)/(b) labels because it will itself be a panel.
X/Y arrows at the oblique corner correspond to `View along +Y` beside the side
view. It uses the actual centre signed annotation w=-170.5mm even though colour
is absolute. Both view directions and the unit deformation scale stay explicit.

## Deliverables and limits

Keep actual source fields local when images/large results are excluded from Git.
Publish reusable skill/code separately. Retain PVSM, raw renders, QA, scripts,
input hashes and versioned PNGs; do not replace a previous manifest to disguise
a new image as an old one. In the motivating project these are under
paper/figures/HD12/deformation_180min_abs_side_v05_20261102 with ROOT_REVIEW.json.
That local evidence path is provenance, not a runtime dependency of this skill.
