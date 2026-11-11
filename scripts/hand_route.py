"""Route one missing connection on a KiCad board with a grid A* search (2 layers, vias allowed).
Usage: hand_route.py board.kicad_pcb NET width_mm start_uuid goal_uuid
start/goal are the pad or track UUIDs that DRC lists as unconnected."""
import os, sys, math, heapq, pcbnew, numpy as np, shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from geom import board_poly

MM, FM = pcbnew.ToMM, pcbnew.FromMM
path, NET, W, s_uuid, g_uuid = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5]
CLR, VIA, RES, EDGE = 0.22, 0.6, 0.1, 0.3      # clearance (+0.02 margin), via size, grid, edge clearance
b = pcbnew.LoadBoard(path)
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]

def pad_poly(p, layer):
    try:
        sps = p.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)
        o = sps.Outline(0)
        return Polygon([(MM(q.x), MM(q.y)) for q in o.CPoints()])
    except Exception:
        bb = p.GetBoundingBox()
        return box(MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))

def item_geom(uuid):
    for t in b.GetTracks():
        if t.m_Uuid.AsString() == uuid:
            return LineString([(MM(t.GetStart().x), MM(t.GetStart().y)), (MM(t.GetEnd().x), MM(t.GetEnd().y))]).buffer(MM(t.GetWidth()) / 2), t.GetLayer()
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.m_Uuid.AsString() == uuid:
                lay = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
                return pad_poly(p, lay), lay
    raise SystemExit(f'item {uuid} not found')

start_geom, start_layer = item_geom(s_uuid)
goal_geom, goal_layer = item_geom(g_uuid)

# obstacles per layer: everything not on NET, grown by clearance + half our width
obs = {L: [] for L in LAYERS}
via_obs = []
for t in b.GetTracks():
    if t.GetNetname() == NET:
        continue
    if t.GetClass() == 'PCB_VIA':
        c = Point(MM(t.GetPosition().x), MM(t.GetPosition().y))
        for L in LAYERS:
            obs[L].append(c.buffer(VIA / 2 + CLR + W / 2))
        via_obs.append(c.buffer(VIA + CLR))
    else:
        g = LineString([(MM(t.GetStart().x), MM(t.GetStart().y)), (MM(t.GetEnd().x), MM(t.GetEnd().y))])
        hw = MM(t.GetWidth()) / 2
        obs[t.GetLayer()].append(g.buffer(hw + CLR + W / 2))
        via_obs.append(g.buffer(hw + CLR + VIA / 2))
for f in b.GetFootprints():
    for p in f.Pads():
        same = p.GetNetname() == NET and NET != ''
        for L in LAYERS:
            if p.IsOnLayer(L) and not same:
                pp = pad_poly(p, L)
                obs[L].append(pp.buffer(CLR + W / 2))
                via_obs.append(pp.buffer(CLR + VIA / 2))
        if p.GetDrillSize().x > 0 and not same:   # holes (incl. NPTH) block both layers
            h = Point(MM(p.GetPosition().x), MM(p.GetPosition().y)).buffer(MM(p.GetDrillSize().x) / 2)
            for L in LAYERS:
                obs[L].append(h.buffer(0.25 + W / 2))
            via_obs.append(h.buffer(0.25 + VIA / 2))
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
        o = z.Outline()
        for k in range(o.OutlineCount()):
            poly = Polygon([(MM(q.x), MM(q.y)) for q in o.Outline(k).CPoints()],
                           [[(MM(q.x), MM(q.y)) for q in o.Hole(k, h).CPoints()] for h in range(o.HoleCount(k))])
            for L in LAYERS:
                obs[L].append(poly.buffer(W / 2))
            via_obs.append(poly.buffer(VIA / 2))
outer, holes = board_poly(b)
inside = outer.buffer(-(EDGE + W / 2))
for h in holes:
    inside = inside.difference(h.buffer(EDGE + W / 2))
inside_via = outer.buffer(-(EDGE + VIA / 2))

# grid over the area around the two ends
x0, y0, x1, y1 = unary_union([start_geom, goal_geom]).bounds
x0, y0, x1, y1 = x0 - 20, y0 - 20, x1 + 20, y1 + 20
xs = np.arange(x0, x1, RES); ys = np.arange(y0, y1, RES)
XX, YY = np.meshgrid(xs, ys)
free = {}
for i, L in enumerate(LAYERS):
    blocked = shapely.contains_xy(unary_union(obs[L]), XX, YY)
    free[i] = shapely.contains_xy(inside, XX, YY) & ~blocked
via_ok = shapely.contains_xy(inside_via, XX, YY) & ~shapely.contains_xy(unary_union(via_obs), XX, YY) & free[0] & free[1]
start_mask = shapely.contains_xy(start_geom, XX, YY)
goal_mask = shapely.contains_xy(goal_geom, XX, YY)
li = {pcbnew.F_Cu: 0, pcbnew.B_Cu: 1}
sl, gl = li[start_layer], li[goal_layer]
gy, gx = np.argwhere(goal_mask).mean(axis=0)
H = lambda r, c: math.hypot(r - gy, c - gx)
pq, dist, prev = [], {}, {}
for r, c in np.argwhere(start_mask):
    n = (sl, r, c); dist[n] = 0; heapq.heappush(pq, (H(r, c), 0, n))
moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
end = None
R, C = XX.shape
while pq:
    _, d, (l, r, c) = heapq.heappop(pq)
    if d > dist.get((l, r, c), 1e18):
        continue
    if l == gl and goal_mask[r, c]:
        end = (l, r, c); break
    nbrs = [((l, r + dr, c + dc), w) for dr, dc, w in moves]
    if via_ok[r, c]:
        nbrs.append(((1 - l, r, c), 25))   # a via costs like 2.5 mm of track
    for (nl, nr, nc), w in nbrs:
        if not (0 <= nr < R and 0 <= nc < C):
            continue
        if not (free[nl][nr, nc] or (start_mask[nr, nc] and nl == sl) or (goal_mask[nr, nc] and nl == gl)):
            continue
        # bend penalty keeps the track tidy
        pr = prev.get((l, r, c))
        bend = 0
        if pr and pr[0] == l and nl == l and (r - pr[1], c - pr[2]) != (nr - r, nc - c):
            bend = 0.5
        nd = d + w + bend
        if nd < dist.get((nl, nr, nc), 1e18):
            dist[(nl, nr, nc)] = nd; prev[(nl, nr, nc)] = (l, r, c)
            heapq.heappush(pq, (nd + H(nr, nc), nd, (nl, nr, nc)))
if not end:
    raise SystemExit('no path found')
pts = [end]
while pts[-1] in prev:
    pts.append(prev[pts[-1]])
pts.reverse()
# compress into straight segments and vias
net = b.FindNet(NET)
segs, vias = 0, 0
def xy(n): return pcbnew.VECTOR2I(FM(float(xs[n[2]])), FM(float(ys[n[1]])))
i = 0
while i < len(pts) - 1:
    a = pts[i]
    if pts[i + 1][0] != a[0]:
        v = pcbnew.PCB_VIA(b); v.SetPosition(xy(a)); v.SetWidth(FM(VIA)); v.SetDrill(FM(0.3)); v.SetNet(net)
        b.Add(v); vias += 1; i += 1; continue
    dirn = (pts[i + 1][1] - a[1], pts[i + 1][2] - a[2]); j = i + 1
    while j + 1 < len(pts) and pts[j + 1][0] == a[0] and (pts[j + 1][1] - pts[j][1], pts[j + 1][2] - pts[j][2]) == dirn:
        j += 1
    t = pcbnew.PCB_TRACK(b); t.SetStart(xy(a)); t.SetEnd(xy(pts[j])); t.SetWidth(FM(W))
    t.SetLayer(LAYERS[a[0]]); t.SetNet(net); b.Add(t); segs += 1
    i = j
pcbnew.SaveBoard(path, b)
L = sum(math.hypot(xs[p[2]] - xs[q[2]], ys[p[1]] - ys[q[1]]) for p, q in zip(pts, pts[1:]))
print(f'{NET}: {segs} segments, {vias} vias, {L:.1f} mm')
