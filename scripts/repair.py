"""One repair round: delete tracks/vias that DRC flags (shorts, crossings, clearance, dangling),
then let Freerouting route what's left. Exit code 0 = clean, 1 = changed (run another round)."""
import sys, json, subprocess, os, shlex, pcbnew

# command that runs Freerouting 1.9 headless, e.g. "xvfb-run -a java -jar freerouting-1.9.0.jar"
FREEROUTING = shlex.split(os.environ['FREEROUTING'])
BAD = {'shorting_items', 'tracks_crossing', 'clearance', 'track_dangling', 'hole_clearance', 'via_dangling'}

half, board_path, r = sys.argv[1], sys.argv[2], int(sys.argv[3])
work = os.path.dirname(board_path)

rpt = os.path.join(work, 'drc.json')
subprocess.run(['kicad-cli', 'pcb', 'drc', board_path, '--format', 'json', '-o', rpt], capture_output=True)
d = json.load(open(rpt))
bad_uuids = {it['uuid'] for v in d['violations'] if v['type'] in BAD for it in v['items']}
dangling = {it['uuid'] for v in d['violations'] if v['type'] == 'track_dangling' for it in v['items']}
unconn = len(d.get('unconnected_items', []))
print(f'round {r}: {sum(v["type"] in BAD for v in d["violations"])} copper errors, {unconn} unconnected')
if not bad_uuids and unconn == 0:
    sys.exit(0)

b = pcbnew.LoadBoard(board_path)
removed = 0
for t in list(b.GetTracks()):
    uid = t.m_Uuid.AsString()
    # the locked BAT+ stub stays until the net is complete; then it's just a dangling spur
    if uid in bad_uuids and (not t.IsLocked() or (uid in dangling and unconn == 0)):
        b.Remove(t)
        removed += 1
if unconn == 0 and bad_uuids <= dangling:
    pcbnew.SaveBoard(board_path, b)
    print(f'  removed {removed} dangling stub(s)')
    sys.exit(1)

dsn, ses = os.path.join(work, f'{half}-r{r}.dsn'), os.path.join(work, f'{half}-r{r}.ses')
pcbnew.ExportSpecctraDSN(b, dsn)
try:
    subprocess.run(FREEROUTING + ['-de', dsn, '-do', ses, '-mp', '100', '-mt', '1'],
                   capture_output=True, timeout=300)
except subprocess.TimeoutExpired:
    print('  router timed out (it stalls when a connection is impossible)')
    sys.exit(1)
pcbnew.ImportSpecctraSES(b, ses)
pcbnew.SaveBoard(board_path, b)
print(f'  removed {removed}, rerouted')
sys.exit(1)
