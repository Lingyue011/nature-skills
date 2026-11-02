# Verified ParaView patterns

## Contents

- [Source closure and reference state](#source-closure-and-reference-state)
- [Absolute vertical colouring and true vector warp](#absolute-vertical-colouring-and-true-vector-warp)
- [Real orthographic scale and direction](#real-orthographic-scale-and-direction)
- [Compact figures and portability](#compact-figures-and-portability)

The workflow was exercised with ParaView 6.2.0 / VTK 9.7.1 on Windows. Locate
the installed runtime rather than hard-coding that version as a dependency.
Use the ParaView Python interpreter, not a system Python missing `paraview`.

```powershell
& '<ParaView installation>/bin/pvpython.exe' --force-offscreen-rendering render.py
```

## Source closure and reference state

Keep NodeTag and ElementTag alongside actual geometry and connectivity. Resolve
node IDs explicitly; a node tag is not generally its zero-based array index.
Before a frame subtraction match every node ID, geometry and component order.
Use the same run's actual baseline, not an assumed zero field. Only translations
warp geometry; preserve rotations separately when recorded.

For a fire-increment figure `U_fire = U_total(t) - U_total(fire_zero)` removes
the initial gravity equilibrium displacement. The caption must say so. This is
not a plot of the complete gravity-plus-fire displaced geometry.

## Absolute vertical colouring and true vector warp

These snippets assume a verified metre-based mesh with `U_fire_m` and a
millimetre scalar `w_fire_mm = 1000*U_fire_m[z]`. Choose these definitions before
rendering, and adapt the names to the actual dataset.

```python
from paraview.simple import (
    XMLUnstructuredGridReader, Calculator, WarpByVector,
    GetActiveViewOrCreate, Show, ColorBy, GetColorTransferFunction,
    Render, SaveScreenshot, SaveState,
)
from paraview import servermanager

reader = XMLUnstructuredGridReader(FileName=[str(input_vtu)])
reader.UpdatePipeline()
absolute = Calculator(Input=reader)
absolute.ResultArrayName = 'abs_w_fire_mm'
absolute.Function = 'abs(w_fire_mm)'
absolute.UpdatePipeline()
checked = servermanager.Fetch(absolute)
# Compare every returned scalar against abs(original w) before accepting.
hi = checked.GetPointData().GetArray('abs_w_fire_mm').GetRange()[1]
assert hi > 0  # Treat an all-zero frame as a separate, explicitly labelled case.

warp = WarpByVector(Input=absolute)
warp.Vectors = ['POINTS', 'U_fire_m']
warp.ScaleFactor = 1.0
warp.UpdatePipeline()
view = GetActiveViewOrCreate('RenderView')
view.ViewSize = [3200, 2200]
view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
view.OrientationAxesVisibility = 0
rep = Show(warp, view)
rep.Representation = 'Surface With Edges'
rep.Ambient, rep.Diffuse = 1.0, 0.0  # Match scalar colours without lighting shifts.
ColorBy(rep, ('POINTS', 'abs_w_fire_mm'))
lut = GetColorTransferFunction('abs_w_fire_mm')
lut.ColorSpace = 'RGB'
lut.RGBPoints = [0,0,0,1, hi*.25,0,1,1, hi*.5,0,1,0,
                 hi*.75,1,1,0, hi,1,0,0]
lut.ScalarRangeInitialized = 1.0
rep.SetScalarBarVisibility(view, False)  # Compose matching labelled bar later.
# Set the reviewed camera explicitly before saving.
Render()
SaveScreenshot(str(raw_png), view, ImageResolution=[3200,2200])
SaveState(str(state_path))
```

Do not replace `U_fire_m` with its componentwise absolute values. That would
change the deformation direction. The Calculator above changes only colour.

Matching Matplotlib colour bar:

```python
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
cmap = LinearSegmentedColormap.from_list(
    'civil_absolute', [(0,0,1),(0,1,1),(0,1,0),(1,1,0),(1,0,0)], N=4097)
norm = Normalize(vmin=0, vmax=hi)
fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax,
             orientation='vertical')
```

The palette is a requested engineering presentation convention, not a universal
perceptual recommendation or a verified SCI journal mandate. Never use
TwoSlopeNorm for this zero-to-magnitude scale. If using a signed diverging map,
a zero-centred two-slope bar can be appropriate, but disclose unequal numerical
slopes when the negative and positive ranges differ.

## Real orthographic scale and direction

For parallel projection:

`pixels_per_metre = viewport_height_px / (2 * CameraParallelScale)`

This assumes coordinates are metres; otherwise it is pixels per geometry unit.
Different viewports with the same parallel scale do not necessarily match
pixels/metre. Equal physical panel widths are sufficient after composition only
when the horizontal source crops and source pixels/metre also match.

At fixed camera let `f=unit(focal-position)`, `r=unit(cross(f,view_up))`, and
`u=cross(r,f)`. A world vector projects to `(dot(v,r),dot(v,u))` on screen.
Raster image Y increases downwards, so flip that second component for image
coordinates. Reject a zero-length viewing direction or view-up parallel to it.

WorldToDisplay gives the exact projection used by the rendered scene:

```python
renderer = view.GetClientSideObject().GetRenderWindow().GetRenderers().GetFirstRenderer()
renderer.SetWorldPoint(x, y, z, 1.0)
renderer.WorldToDisplay()
screen = renderer.GetDisplayPoint()  # Origin lower left, unlike PNG pixels.
```

For a horizontal +Y view, camera and focal point have equal X and Z, camera Y
is smaller, view-up is +Z. Store any whole-camera Z translation used to centre
the shape; it is not deformation amplification.

## Compact figures and portability

Render model content first, measure non-background bounds, then crop and compose.
Use the union of text, images and colour-bar bounds plus a small physical pad.
After fitting, remeasure all text and panel rectangles. Aspect-preserving images
may shrink their axes: check final rendered bounds rather than only add_axes
arguments. An unequal-height side view is intentional; an unequal scale is not.

Save a manifest of the exact versions delivered. Review representative raw data,
render source, image and source/hash correspondence. A manifest is not a
substitute for reading the actual image or checking physical quantity definitions.
In PVSM relocation, verify every VTU/VTP reference points to an existing current
file. Byte-preserving replacement of a known parent directory avoids unrelated
newline or serialization changes; record the exact replacement count.
