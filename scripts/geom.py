"""Shared geometry helpers: obstacles on a Kabuki board, from the Ergogen-generated .kicad_pcb."""
import math, pcbnew
from shapely.geometry import Polygon, Point, box
from shapely import affinity
from shapely.ops import unary_union

MM = pcbnew.ToMM

def fp_bbox_poly(fp):
    """Footprint pads + graphics (no text) as a rotated rectangle, in mm."""
    ang = fp.GetOrientationDegrees()
    pos = fp.GetPosition()
    # bounding box in footprint-local frame: rotate to 0, measure, rotate back
    fp2 = pcbnew.FOOTPRINT(fp)
    fp2.SetOrientationDegrees(0)
    bb = fp2.GetBoundingBox(False)
    r = box(MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
    return affinity.rotate(r, -ang, origin=(MM(pos.x), MM(pos.y)))

def courtyard(fp, back=True):
    try:
        sps = fp.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
        if sps.OutlineCount():
            pts = [(MM(p.x), MM(p.y)) for p in sps.Outline(0).CPoints()]
            return Polygon(pts)
    except Exception:
        pass
    return None

def board_poly(b):
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, False)
    o = ps.Outline(0)
    outer = Polygon([(MM(p.x), MM(p.y)) for p in o.CPoints()])
    holes = [Polygon([(MM(p.x), MM(p.y)) for p in ps.Hole(0, i).CPoints()]) for i in range(ps.HoleCount(0))]
    return outer, holes

def key_square(fp, size=14):
    pos = fp.GetPosition(); ang = fp.GetOrientationDegrees()
    c = (MM(pos.x), MM(pos.y))
    sq = box(c[0]-size/2, c[1]-size/2, c[0]+size/2, c[1]+size/2)
    return affinity.rotate(sq, -ang, origin=c)

def obstacles(b, skip=()):
    """Back-side keep-outs and plate cutouts."""
    back, plate, front = [], [], []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref in skip: continue
        name = str(fp.GetFPID().GetLibItemName())
        pos = fp.GetPosition(); c = (MM(pos.x), MM(pos.y))
        if name == 'switch_mx':
            back.append(fp_bbox_poly(fp))                 # socket + pads
            back.append(Point(c).buffer(2.0))              # centre post
            for dx in (-5.08, 5.08):                       # 5-pin side posts
                p = affinity.rotate(Point(c[0]+dx, c[1]), -fp.GetOrientationDegrees(), origin=c)
                back.append(p.buffer(0.95))
            plate.append(key_square(fp))
        elif name.startswith('rotary_encoder'):
            back.append(fp_bbox_poly(fp))
            front.append(fp_bbox_poly(fp))
            plate.append(key_square(fp))
        elif name == 'XIAO-BLE':
            xb = box(c[0]-8.9, c[1]-10.5, c[0]+8.9, c[1]+10.5)
            back.append(xb)
        elif name.startswith('mounting_hole'):
            back.append(Point(c).buffer(1.1))
        else:
            cy = courtyard(fp, back=fp.IsFlipped())
            back.append(cy if cy is not None else fp_bbox_poly(fp))
    return unary_union(back), unary_union(plate), unary_union(front) if front else None
