// Kabuki — hybrid hotswap switch: MX + Choc v1/v2 sockets on one footprint
//
// One switch at a time: either an MX switch or a Choc switch plugs in. Both Kailh sockets
// sit on the back and connect in parallel (pad 1 = from, pad 2 = to), so the matrix and the
// pin budget don't change.
//
// Geometry (KiCad axes, x right, y down, top view):
//   - MX socket in the upper half, exactly as Ergogen's built-in `mx` (MIT) places it:
//     switch pins at (2.54, -5.08) and (-3.81, -2.54), pads at (5.842, -5.08) and (-7.085, -2.54)
//   - Choc socket in the lower half: Ergogen's built-in `choc` (MIT) layout turned 180 degrees,
//     so a Choc switch goes in rotated 180 degrees: pins at (-5, 3.75) and (0, 5.95),
//     pads at (-8.275, 3.75) and (3.275, 5.95)
//   - two pads trimmed on the inner or outer side, for clearance (2026-11-08):
//     MX pad 1 is 2.3 mm tall instead of 2.5 (keeps 0.5 mm from the post slot);
//     Choc pad 2 is 1.8 mm wide instead of 2.6, outer side (1.3 mm from the XIAO pins on the
//     ring column). The socket's solder tab still sits fully on each pad
//   - centre hole 5.0 mm: fits the MX post (3.99), Choc v1 (3.43) and Choc v2 (5.0)
//   - side-post slots, 2.2 x 1.8 mm at +-5.29: cover the MX posts (+-5.08) and the Choc
//     posts (+-5.5). Same idea as the Lever Flake footprint, sized for the posts measured on
//     this project (Choc Sunset 1.59 mm; MX to caliper, #41)
//   - no hole for the corner metal leg that some Kailh Choc v2 switches have: it would land
//     0.2 mm from the MX socket hole. Clip that leg, or use v2 switches without it
//   - courtyards around both sockets on the socket side are ESTIMATES from the pad extents,
//     not from Kailh's drawings
//
// Params:
//   side: B (default) — side of the sockets. Keep B: the switch sits on top, sockets below
//   keycaps: default true — draws the 18 x 18 MX and 17.5 x 16.5 Choc keycap outlines on User.Drawings
//   center_hole: default 5.0
//   slot_length, slot_width: side-post slots, default 2.2 x 1.8
//   from, to: nets

module.exports = {
  params: {
    designator: 'S',
    side: 'B',
    keycaps: true,
    center_hole: 5.0,
    slot_length: 2.2,
    slot_width: 1.8,
    from: undefined,
    to: undefined,
  },
  body: p => {
    const s = p.side
    const mirror = s === 'B' ? ' (justify mirror)' : ''
    // switch pins are fixed in the top view, so hole and pad x never mirror: sockets go on the back
    const X = x => x
    const f = v => (+v).toFixed(4)
    const rect = (x0, y0, x1, y1, layer, w = 0.05) =>
      `(fp_rect (start ${f(X(x0))} ${f(y0)}) (end ${f(X(x1))} ${f(y1)}) (stroke (width ${w}) (type solid)) (fill none) (layer "${layer}"))`
    const pad = (num, x, y, w, h, net) =>
      `(pad "${num}" smd rect (at ${f(X(x))} ${f(y)} ${p.r}) (size ${w} ${h}) (layers "${s}.Cu" "${s}.Paste" "${s}.Mask") ${net})`
    const poly = (pts, layer, w = 0.05) =>
      `(fp_poly (pts ${pts.map(q => `(xy ${f(X(q[0]))} ${f(q[1])})`).join(' ')}) (stroke (width ${w}) (type solid)) (fill none) (layer "${layer}"))`
    const hole = (x, y, d) =>
      `(pad "" np_thru_hole circle (at ${f(X(x))} ${f(y)} ${p.r}) (size ${d} ${d}) (drill ${d}) (layers "*.Cu" "*.Mask"))`
    const slot = x =>
      `(pad "" np_thru_hole oval (at ${f(x)} 0 ${p.r}) (size ${p.slot_length} ${p.slot_width}) (drill oval ${p.slot_length} ${p.slot_width}) (layers "*.Cu" "*.Mask"))`

    return `
  (footprint "kabuki:switch_hybrid"
    (layer "${s}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 0 ${p.r}) (layer "${s}.SilkS") ${p.ref_hide}
      (effects (font (size 1 1) (thickness 0.15))${mirror}))
    (property "Value" "MX+Choc hotswap" (at 0 1.6 ${p.r}) (layer "${s}.Fab")
      (effects (font (size 0.8 0.8) (thickness 0.12))${mirror}))
    (attr smd)

    ${'' /* plate cut-out corners (14 mm) and keycaps */}
    ${rect(-7, -7, 7, 7, 'Dwgs.User', 0.1)}
    ${p.keycaps ? rect(-9, -9, 9, 9, 'Dwgs.User', 0.12) : ''}
    ${p.keycaps ? rect(-8.75, -8.25, 8.75, 8.25, 'Dwgs.User', 0.08) : ''}

    ${'' /* centre post and side-post slots */}
    ${hole(0, 0, p.center_hole)}
    ${slot(-5.29)}
    ${slot(5.29)}

    ${'' /* MX socket: pin holes + pads (upper half) */}
    ${hole(2.54, -5.08, 3)}
    ${hole(-3.81, -2.54, 3)}
    ${pad(1, -7.085, -2.64, 2.55, 2.3, p.from.str)}
    ${pad(2, 5.842, -5.08, 2.55, 2.5, p.to.str)}

    ${'' /* Choc socket, turned 180 degrees: pin holes + pads (lower half) */}
    ${hole(-5, 3.75, 3)}
    ${hole(0, 5.95, 3)}
    ${pad(1, 3.275, 5.95, 2.6, 2.6, p.from.str)}
    ${pad(2, -7.875, 3.75, 1.8, 2.6, p.to.str)}

    ${'' /* socket bodies, estimated */}
    ${poly([[-8.6, -1.2], [-8.6, -4.4], [-1.2, -4.4], [-1.2, -6.6], [7.4, -6.6], [7.4, -3.6], [0.4, -3.6], [0.4, -1.2]], `${s}.CrtYd`)}
    ${poly([[-9.0, 2.2], [4.8, 2.2], [4.8, 7.5], [-2.0, 7.5], [-2.0, 5.3], [-9.0, 5.3]], `${s}.CrtYd`)}
    ${poly([[-8.36, -1.49], [-8.36, -4.1], [-1.4, -4.1], [-1.4, -6.33], [7.12, -6.33], [7.12, -3.83], [0.2, -3.83], [0.2, -1.49]], `${s}.Fab`, 0.1)}
    ${poly([[-8.775, 2.45], [4.575, 2.45], [4.575, 7.25], [-1.8, 7.25], [-1.8, 5.05], [-8.775, 5.05]], `${s}.Fab`, 0.1)}
    (fp_text user "MX" (at ${f(X(-1))} -4.2 ${p.r}) (layer "${s}.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))${mirror}))
    (fp_text user "Choc, turned 180" (at ${f(X(-2.5))} 4.6 ${p.r}) (layer "${s}.Fab") (effects (font (size 0.7 0.7) (thickness 0.1))${mirror}))
  )
  `
  }
}
