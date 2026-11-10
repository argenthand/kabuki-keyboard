#!/bin/bash
# Routed board -> JLCPCB Gerber + drill zip
set -eu
h=$1; pcb=$2; out=$3
tmp=$(mktemp -d)
kicad-cli pcb export gerbers "$pcb" -o "$tmp/" --layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts --subtract-soldermask >/dev/null
kicad-cli pcb export drill "$pcb" -o "$tmp/" --format excellon --excellon-separate-th >/dev/null
mkdir -p "$out"; rm -f "$out/kabuki-$h.zip"
(cd "$tmp" && zip -q -r "$out/kabuki-$h.zip" .)
ls "$tmp"; rm -rf "$tmp"
