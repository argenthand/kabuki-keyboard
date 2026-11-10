# Scripts

How the boards in `pcb/` were made from `config.yaml`. Needs KiCad 10 (its Python `pcbnew` module and `kicad-cli`), Python 3 with `shapely`, `numpy` and, for the fit plate, `trimesh` + `manifold3d`, plus Java and Freerouting 1.9.

1. `pnpm compile` (Ergogen → `output/pcbs/left.kicad_pcb`, `right.kicad_pcb`, unrouted).
2. `FREEROUTING="xvfb-run -a java -jar freerouting-1.9.0.jar" scripts/route_all.sh` → `pcb/left/`, `pcb/right/`.
   - `route.py` sets the rules (0.25 mm signal, 0.3 mm GND/battery tracks, 0.2 mm clearance, 0.6/0.3 mm vias), adds a no-track zone under the XIAO's antenna end and a thin one along the board edge, exports to Freerouting and imports the result.
   - `repair.py` runs KiCad's DRC, deletes any track it flags and lets Freerouting reroute, until nothing is flagged or unconnected.
3. `scripts/gerbers.sh left $PWD/pcb/left/left.kicad_pcb $PWD/gerbers` (same for `right`) → JLCPCB zips.
4. `python3 scripts/fit_plate.py output/pcbs/left.kicad_pcb fit/kabuki_left_fit_plate_mx_14.0.stl` → fit-test plate.

`geom.py` holds the shared geometry helpers used to place the JST, power switch and mounting holes clear of everything else.

Ergogen rewrites the whole board on every run, so rerouting starts from scratch after any change to `config.yaml`.
