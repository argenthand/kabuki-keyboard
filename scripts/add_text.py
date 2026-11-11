"""Copy the board-level silkscreen texts from a fresh Ergogen board into the routed board, without rerouting.
Usage: add_text.py ergogen.kicad_pcb routed.kicad_pcb"""
import sys, pcbnew

# read everything from the Ergogen board into plain values first
src = pcbnew.LoadBoard(sys.argv[1])
texts = []
for d in src.GetDrawings():
    if d.GetClass() != 'PCB_TEXT':
        continue
    pos, size = d.GetPosition(), d.GetTextSize()
    texts.append(dict(text=d.GetText(), layer=d.GetLayer(), x=int(pos.x), y=int(pos.y),
                      angle=d.GetTextAngle().AsDegrees(), w=int(size.x), h=int(size.y),
                      thickness=d.GetTextThickness(), mirrored=d.IsMirrored(),
                      hj=d.GetHorizJustify(), vj=d.GetVertJustify()))

dst = pcbnew.LoadBoard(sys.argv[2])
for d in [d for d in dst.GetDrawings() if d.GetClass() == 'PCB_TEXT']:   # replace any earlier copy
    dst.Remove(d)
for t in texts:
    n = pcbnew.PCB_TEXT(dst)
    n.SetText(t['text']); n.SetLayer(t['layer']); n.SetPosition(pcbnew.VECTOR2I(t['x'], t['y']))
    n.SetTextAngle(pcbnew.EDA_ANGLE(t['angle'], pcbnew.DEGREES_T))
    n.SetTextSize(pcbnew.VECTOR2I(t['w'], t['h'])); n.SetTextThickness(t['thickness'])
    n.SetMirrored(t['mirrored']); n.SetHorizJustify(t['hj']); n.SetVertJustify(t['vj'])
    dst.Add(n)
    print(f"{t['text']!r} at ({t['x'] / 1e6:.2f}, {t['y'] / 1e6:.2f}) {t['angle']:.0f} deg, {t['h'] / 1e6:g} mm, mirrored {t['mirrored']}")
pcbnew.SaveBoard(sys.argv[2], dst)
print(f'{len(texts)} text(s) added')
