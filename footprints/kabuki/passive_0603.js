// Kabuki — 0603 resistor or capacitor, hand-solderable pads
//
// A plain 2-pad SMD footprint: pull-ups (R) and the trackpoint RC reset (R, C).
// Pads are slightly longer than a reflow 0603, for soldering with an iron.
//
// Params:
//   side: B (default) or F
//   dnp: default false. true marks the part "do not populate" in KiCad, so it's left
//     out of the BOM and position files, and the empty pads stay on the board
//   value: part value shown on Fab, e.g. 4.7k
//   silk: optional silkscreen label, e.g. 4.7k or DNP; Ergogen hides references by default
//   silk_offset: [x, y] of that label, default [0, 1.6]
//   from, to: nets

module.exports = {
  params: {
    designator: 'R',
    side: 'B',
    dnp: false,
    value: '',
    silk: '',
    silk_offset: [0, 1.6],
    from: undefined,
    to: undefined,
  },
  body: p => {
    const s = p.side
    const mirror = s === 'B' ? ' (justify mirror)' : ''
    return `
  (footprint "kabuki:passive_0603"
    (layer "${s}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 0 ${p.r}) (layer "${s}.SilkS") ${p.ref_hide}
      (effects (font (size 1 1) (thickness 0.15))${mirror}))
    (property "Value" "${p.value}" (at 0 1.5 ${p.r}) (layer "${s}.Fab")
      (effects (font (size 0.6 0.6) (thickness 0.1))${mirror}))
    ${p.silk ? `(fp_text user "${p.silk}" (at ${p.silk_offset[0]} ${p.silk_offset[1]} ${p.r}) (layer "${s}.SilkS") (effects (font (size 1 1) (thickness 0.15))${mirror}))` : ''}
    (attr smd${p.dnp ? ' exclude_from_bom exclude_from_pos_files dnp' : ''})
    (fp_rect (start -0.8 -0.4) (end 0.8 0.4) (stroke (width 0.1) (type solid)) (fill none) (layer "${s}.Fab"))
    (fp_rect (start -1.65 -0.75) (end 1.65 0.75) (stroke (width 0.05) (type solid)) (fill none) (layer "${s}.CrtYd"))
    (pad "1" smd roundrect (at -0.9 0 ${p.r}) (size 1 0.95) (roundrect_rratio 0.25) (layers "${s}.Cu" "${s}.Paste" "${s}.Mask") ${p.from.str})
    (pad "2" smd roundrect (at 0.9 0 ${p.r}) (size 1 0.95) (roundrect_rratio 0.25) (layers "${s}.Cu" "${s}.Paste" "${s}.Mask") ${p.to.str})
  )
  `
  }
}
