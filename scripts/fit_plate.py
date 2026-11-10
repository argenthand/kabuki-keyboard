"""Fit-test plate from the Ergogen board: 1.5 mm MX plate (14.0 mm holes) on a 9 mm rim,
so switches, keycaps and a knob can be tried before the PCB order. Print top face down."""
import os, sys, pcbnew, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *
from shapely import affinity
from shapely.geometry import box
pcb, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(pcb)
outer, _ = board_poly(b)
holes = []
for fp in b.GetFootprints():
    name = str(fp.GetFPID().GetLibItemName())
    c = (MM(fp.GetPosition().x), MM(fp.GetPosition().y))
    if name == 'switch_mx':
        holes.append(key_square(fp, 14.0))
    elif name.startswith('rotary_encoder'):
        holes.append(key_square(fp, 13.0))      # EC11 body (12 x 12) pokes through the plate
    elif name.startswith('mounting_hole'):
        holes.append(Point(c).buffer(1.1, 32))   # M2
plate = outer.difference(unary_union(holes))
rim = outer.difference(outer.buffer(-2.0, join_style=1))
flip = lambda g: affinity.scale(g, 1, -1, origin=(0, 0))
plate_m = trimesh.creation.extrude_polygon(flip(plate), 1.5)
rim_m = trimesh.creation.extrude_polygon(flip(rim), 9.0)
m = trimesh.boolean.union([plate_m, rim_m], engine='manifold')
m.apply_translation(-m.bounds[0])
m.export(out)
print(out, 'extents mm', [round(v, 1) for v in m.extents], 'watertight', m.is_watertight)
