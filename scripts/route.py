"""Route one Kabuki half: set rules, export DSN, run Freerouting, import SES, save."""
import sys, subprocess, pcbnew, os, time, shlex
# command that runs Freerouting 1.9 headless, e.g. "xvfb-run -a java -jar freerouting-1.9.0.jar"
FREEROUTING = shlex.split(os.environ["FREEROUTING"])
half, src, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
passes = sys.argv[4] if len(sys.argv) > 4 else '100'
os.makedirs(outdir, exist_ok=True)
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(src)
ds = b.GetDesignSettings()
ns = ds.m_NetSettings
d = ns.GetDefaultNetclass()
d.SetTrackWidth(mm(0.25)); d.SetClearance(mm(0.2)); d.SetViaDiameter(mm(0.6)); d.SetViaDrill(mm(0.3))
pw = pcbnew.NETCLASS('Power')
pw.SetTrackWidth(mm(0.3)); pw.SetClearance(mm(0.2)); pw.SetViaDiameter(mm(0.6)); pw.SetViaDrill(mm(0.3))
ns.SetNetclass('Power', pw)
for net in ('GND', 'BAT_P', 'BAT_SW'):
    ns.SetNetclassPatternAssignment(net, 'Power')
ns.RecomputeEffectiveNetclasses()
b.SynchronizeNetsAndNetClasses(True)
# JLCPCB-safe minimums
ds.m_TrackMinWidth = mm(0.2); ds.m_MinClearance = mm(0.2); ds.m_ViasMinSize = mm(0.6); ds.m_MinThroughDrill = mm(0.3)
# 0.3 mm copper-to-edge (JLCPCB's routed-edge minimum) so tracks can reach the XIAO's window pads
ds.m_CopperEdgeClearance = mm(0.3)
# no tracks or vias under the XIAO's antenna end (the end away from USB-C), both layers
mcu = [f for f in b.GetFootprints() if f.GetReference() == 'MCU1'][0]
cx, cy = pcbnew.ToMM(mcu.GetPosition().x), pcbnew.ToMM(mcu.GetPosition().y)
z = pcbnew.ZONE(b)
z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True)
z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
z.SetZoneName('xiao_antenna')
ol = z.Outline(); ol.NewOutline()
for x, y in ((cx-8.9, cy+9.68), (cx+8.9, cy+9.68), (cx+8.9, cy+12.48), (cx-8.9, cy+12.48)):
    ol.Append(mm(x), mm(y))
b.Add(z)
# thin no-track ring inside the board outline: the router keeps only 0.2 mm to edges (JLCPCB's
# bare minimum), but ~0.3 mm to rule areas, so this holds tracks ~0.35 mm off the outer edge
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, False)
outer = ps.Outline(0)
inner = pcbnew.SHAPE_POLY_SET(); inner.NewOutline()
for i in range(outer.PointCount()):
    inner.Append(outer.CPoint(i))
inner.Inflate(-mm(0.1), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.01))
ring = pcbnew.SHAPE_POLY_SET(); ring.NewOutline()
for i in range(outer.PointCount()):
    ring.Append(outer.CPoint(i))
ring.BooleanSubtract(inner)
for k in range(ring.OutlineCount()):
    rz = pcbnew.ZONE(b)
    rz.SetIsRuleArea(True); rz.SetDoNotAllowTracks(True); rz.SetDoNotAllowVias(True); rz.SetDoNotAllowZoneFills(True)
    rz.SetDoNotAllowPads(False); rz.SetDoNotAllowFootprints(False)
    rz.SetLayerSet(ls); rz.SetZoneName('edge_margin')
    sub = pcbnew.SHAPE_POLY_SET(); sub.AddOutline(ring.Outline(k))
    for hidx in range(ring.HoleCount(k)):
        sub.AddHole(ring.Hole(k, hidx))
    rz.SetOutline(sub)
    b.Add(rz)
# the XIAO's BAT+ pad sits in a board window, inside the edge clearance, so the router can't
# reach it: a 1 mm back stub out of the window's bottom edge gives it a start point
bat = [p for p in mcu.Pads() if p.GetNumber() == '19'][0]
st = pcbnew.PCB_TRACK(b); st.SetLayer(pcbnew.B_Cu); st.SetWidth(mm(0.3)); st.SetNet(bat.GetNet())
st.SetStart(bat.GetPosition()); st.SetEnd(bat.GetPosition() + pcbnew.VECTOR2I(0, mm(1.0)))
st.SetLocked(True)
b.Add(st)
dsn = os.path.join(outdir, f'{half}.dsn'); ses = os.path.join(outdir, f'{half}.ses')
assert pcbnew.ExportSpecctraDSN(b, dsn), 'DSN export failed'
t = time.time()
try:
    r = subprocess.run(FREEROUTING + [
                        '-de', dsn, '-do', ses, '-mp', passes, '-mt', '1'] + os.environ.get('FR_EXTRA', '').split(), capture_output=True, text=True, timeout=300)
except subprocess.TimeoutExpired:
    sys.exit('router timed out')
print('freerouting exit', r.returncode, f'{time.time()-t:.0f}s')
if not os.path.exists(ses):
    print(r.stdout[-3000:], r.stderr[-3000:]); sys.exit(1)
assert pcbnew.ImportSpecctraSES(b, ses), 'SES import failed'
out = os.path.join(outdir, f'{half}.kicad_pcb')
pcbnew.SaveBoard(out, b)
print('saved', out, 'tracks', len(b.GetTracks()))
