# Scripts

How the boards in `pcb/` were made from `config.yaml`. Needs KiCad 10 (its Python `pcbnew` module and `kicad-cli`), Python 3 with `shapely`, `numpy` and, for the fit plate, `trimesh` + `manifold3d`, plus Java and Freerouting 1.9.

1. `pnpm compile` (Ergogen → `output/pcbs/left.kicad_pcb`, `right.kicad_pcb`, unrouted).
2. Route each half (`FREEROUTING="xvfb-run -a java -jar freerouting-1.9.0.jar"`):
   - `route.py` sets the rules (0.25 mm signal, 0.3 mm GND/battery tracks, 0.2 mm clearance, 0.6/0.3 mm vias), adds a no-track zone under the XIAO's antenna end and a thin one along the board edge, exports to Freerouting and imports the result.
   - `repair.py` runs one clean-up round: KiCad's DRC, delete any track it flags, let Freerouting reroute. Exit 0 = clean, 1 = something changed. `route_all.sh` chains `route.py` and up to 5 `repair.py` rounds.
   - `hand_route.py board.kicad_pcb NET width start_uuid goal_uuid` draws one connection Freerouting left out (grid search over both layers, vias allowed). Start and goal are the item UUIDs DRC lists as unconnected. The right half's C3 and BAT_SW tracks were drawn this way.
3. Silkscreen text: Ergogen places it from `config.yaml` (`ceoloide/utility_text`). To add or change text on an already routed board without rerouting, run Ergogen and then `add_text.py output/pcbs/left.kicad_pcb pcb/left/left.kicad_pcb` (copies the board's texts across). `text_fit.py board.kicad_pcb "text" battery|outside` finds the largest size and spot where a line of back-silkscreen text fits.
4. `scripts/gerbers.sh left $PWD/pcb/left/left.kicad_pcb $PWD/gerbers` (same for `right`) → JLCPCB zips.
5. `python3 scripts/fit_plate.py output/pcbs/left.kicad_pcb fit/kabuki_left_fit_plate_mx_14.0.stl` → fit-test plate.

`geom.py` holds the shared geometry helpers used to place the JST, power switch, mounting holes and text clear of everything else.

Ergogen rewrites the whole board on every run, so any change to `config.yaml` other than text means rerouting from scratch.
