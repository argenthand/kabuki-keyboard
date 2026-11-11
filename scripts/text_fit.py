"""Find where a line of back-silkscreen text fits, as large as possible.
Usage: text_fit.py board.kicad_pcb "text" battery|outside [heights...]
battery = inside the battery outline; outside = anywhere on the board except the battery outline.
Prints the best spot per height: centre (KiCad mm), angle, text box size, clearance to the nearest obstacle."""
import sys, pcbnew
import numpy as np
from shapely.geometry import box, Point, LineString
from shapely import affinity
from shapely.ops import unary_union
from shapely.prepared import prep
sys.path.insert(0, __import__('os').path.dirname(__file__))
from geom import board_poly, obstacles

MM, FM = pcbnew.ToMM, pcbnew.FromMM
path, text, where = sys.argv[1], sys.argv[2], sys.argv[3]
heights = [float(h) for h in sys.argv[4:]] or [3.0, 2.5, 2.0, 1.5, 1.2, 1.0]
SILK_CLR, EDGE_CLR = 0.3, 0.8

b = pcbnew.LoadBoard(path)
back, _, _ = obstacles(b)
obs = [back]
for fp in b.GetFootprints():
    for p in fp.Pads():                                   # every pad and hole, either side
        bb = p.GetBoundingBox()
        obs.append(box(MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        obs.append(Point(MM(t.GetPosition().x), MM(t.GetPosition().y)).buffer(0.3))
# board-level back silkscreen = the battery outline
bat_lines = []
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.B_SilkS and d.GetClass() != 'PCB_TEXT':
        bb = d.GetBoundingBox()
        bat_lines.append(box(MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
battery = unary_union(bat_lines).envelope
obs.append(battery.exterior.buffer(0.1))
outer, holes = board_poly(b)
inside = outer.buffer(-EDGE_CLR)
for h in holes:
    inside = inside.difference(h.buffer(EDGE_CLR))
region = inside.intersection(battery) if where == 'battery' else inside.difference(battery)
allowed = region.difference(unary_union(obs).buffer(SILK_CLR))
pa = prep(allowed)

def text_box(h):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text); t.SetLayer(pcbnew.B_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(FM(h), FM(h))); t.SetTextThickness(FM(max(0.15, 0.15 * h)))
    t.SetMirrored(True)
    bb = t.GetBoundingBox()
    return MM(bb.GetWidth()), MM(bb.GetHeight())

x0, y0, x1, y1 = allowed.bounds
for h in heights:
    w, hh = text_box(h)
    best = None
    for ang in (0, 90):
        bw, bh = (w, hh) if ang == 0 else (hh, w)
        for x in np.arange(x0 + bw / 2, x1 - bw / 2, 0.25):
            for y in np.arange(y0 + bh / 2, y1 - bh / 2, 0.25):
                r = box(x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2)
                if pa.contains(r):
                    c = allowed.boundary.distance(r)
                    if not best or c > best[0]:
                        best = (c, x, y, ang, bw, bh)
    if best:
        c, x, y, ang, bw, bh = best
        print(f'h={h}: fits at ({x:.2f}, {y:.2f}) angle {ang}, box {bw:.1f} x {bh:.1f} mm, clearance +{c:.2f} mm')
        break
    print(f'h={h}: no fit (box {w:.1f} x {hh:.1f} mm)')
print(f'battery outline {battery.bounds}')
