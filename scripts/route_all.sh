#!/bin/bash
# Ergogen boards (output/pcbs) -> routed boards (pcb/<half>): one Freerouting pass, then repair
# rounds (delete what DRC flags, reroute) until DRC has no copper errors and nothing unconnected.
# Needs KiCad 10 (pcbnew Python + kicad-cli) and FREEROUTING set, e.g.
#   FREEROUTING="xvfb-run -a java -jar freerouting-1.9.0.jar" scripts/route_all.sh
set -u
cd "$(dirname "$0")/.."
for h in ${@:-left right}; do
  # attempt 1 uses Freerouting's default order; later attempts shuffle it ("-is random")
  for a in 1 2 3 4 5; do
    rm -rf pcb/$h
    [ $a -gt 1 ] && export FR_EXTRA="-is random" || export FR_EXTRA=""
    python3 scripts/route.py $h output/pcbs/$h.kicad_pcb pcb/$h
    rc=1
    for r in 0 1 2 3; do
      python3 scripts/repair.py $h pcb/$h/$h.kicad_pcb $r; rc=$?
      [ $rc -eq 0 ] && break
    done
    [ $rc -eq 0 ] && break
  done
  rm -f pcb/$h/*.dsn pcb/$h/*.ses pcb/$h/drc.json
done
