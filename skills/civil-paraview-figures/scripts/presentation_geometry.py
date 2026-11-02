"""Pure-Python camera projection and colour stops; no FE or file mutation."""
import argparse
import json
import math


def _vector(values):
    if len(values) != 3 or not all(math.isfinite(x) for x in values):
        raise ValueError('Expected three finite coordinates')
    return tuple(float(x) for x in values)


def _unit(v):
    n = math.hypot(*v)
    if n == 0:
        raise ValueError('Degenerate camera direction or view-up')
    return tuple(x / n for x in v)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def projected_axes(position, focal, view_up):
    """Orthographic world axes as screen (right,up), not raster (right,down)."""
    position, focal, view_up = map(_vector, (position, focal, view_up))
    forward = _unit(tuple(b-a for a, b in zip(position, focal)))
    right = _unit(_cross(forward, _unit(view_up)))
    up = _unit(_cross(right, forward))
    return {'right': right, 'up': up,
            'X': (right[0], up[0]), 'Y': (right[1], up[1]),
            'Z': (right[2], up[2])}


def pixels_per_unit(viewport_height, parallel_scale):
    if not all(math.isfinite(x) and x > 0
               for x in (viewport_height, parallel_scale)):
        raise ValueError('Viewport height and parallel scale must be positive')
    return viewport_height / (2 * parallel_scale)


def absolute_rgb_points(upper):
    """Flat ParaView RGBPoints for the requested linear absolute-value palette."""
    if not math.isfinite(upper) or upper <= 0:
        raise ValueError('Positive finite upper bound required')
    rgb = [(0,0,1), (0,1,1), (0,1,0), (1,1,0), (1,0,0)]
    return [v for i, colour in enumerate(rgb) for v in (upper*i/4, *colour)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--position', nargs=3, type=float, required=True)
    parser.add_argument('--focal', nargs=3, type=float, required=True)
    parser.add_argument('--up', nargs=3, type=float, default=[0,0,1])
    args = parser.parse_args()
    print(json.dumps(projected_axes(args.position, args.focal, args.up), indent=2))
