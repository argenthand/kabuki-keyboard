// Kabuki — Sprintek SK8707-01-008 trackpoint (detached sensor with diamond metal plate)
//
// Dimensions from Sprintek DS0048 v1.04 (2026-03-30), p. 7 "SK8707-01-008 Sensor Mechanical
// Drawing": https://docs.holykeebs.com/datasheets/SK8707-01.pdf
//
// What this footprint places (all relative to the stick):
//   - stick hole (NPTH): the stick's base boss is Ø3.70 mm
//   - 2 x M2 screw clearance holes (NPTH), 19 mm apart: the sensor's tabs have M2x0.25
//     threaded holes, screws go in from the top through the PCB
//   - courtyard + fab outline of the sensor plate on the mounting side, and a KiCad keepout
//     area over it, 0.5 mm larger: no vias under the metal plate. The courtyard already keeps
//     other parts away; banning pads here flagged this footprint's own holes and pads
//   - courtyard circles for the screw heads on the other side (they sit under the switch plate)
//   - a 1x5 row of through-hole pads (VCC, GND, CLK, DATA, RST) for the wires from the
//     controller board, which lives in the case beside the battery (no room on the PCB)
//
// The sensor's 4-pad tail is wired straight to the controller board (4 short wires); it
// doesn't connect to this PCB.
//
// Coordinates use KiCad axes (x right, y down). In the datasheet view the tail points down
// (+y); sensor_rotation turns the whole sensor around the stick (180 = tail pointing up).
//
// Params:
//   side: B (default) — the side the sensor plate is screwed to
//   sensor_rotation: degrees, default 180
//   hole_diameter: stick hole, default 4.5 (boss Ø3.70 + 0.4 mm per side)
//   screw_hole_diameter: default 2.4 (M2 clearance)
//   screw_head_diameter: default 3.8 (low-head M2), drawn as a courtyard on the other side
//   include_keepout: default true
//   pads_offset: [x, y] of pad 1, relative to the stick, default [0, 15]
//   pads_rotation: direction of the pad row in degrees (0 = towards +x), default 0
//   VCC, GND, CLK, DATA, RST: nets

module.exports = {
  params: {
    designator: 'TP',
    side: 'B',
    sensor_rotation: 180,
    hole_diameter: 4.5,
    screw_hole_diameter: 2.4,
    screw_head_diameter: 3.8,
    include_keepout: true,
    pads_offset: [0, 15],
    pads_rotation: 0,
    VCC: { type: 'net', value: '3V3' },
    GND: { type: 'net', value: 'GND' },
    CLK: { type: 'net', value: 'TP_CLK' },
    DATA: { type: 'net', value: 'TP_DATA' },
    RST: { type: 'net', value: 'TP_RST' },
  },
  body: p => {
    const s = p.side
    const other = s === 'B' ? 'F' : 'B'
    const mirror = s === 'B' ? ' (justify mirror)' : ''
    const f = v => (+v).toFixed(4)

    // rotate a local point around the stick (same sense as KiCad footprint rotation)
    const ra = p.sensor_rotation * Math.PI / 180
    const rot = ([x, y]) => [x * Math.cos(ra) + y * Math.sin(ra), -x * Math.sin(ra) + y * Math.cos(ra)]

    // sensor outline, datasheet orientation (tail toward +y): tabs ±11.5 x ±2.8,
    // octagon ±6.74 wide with its top edge 6.3 mm from the stick, tail ±3.0 down to 11.3 mm
    const outline = [
      [-3.2, -6.3], [3.2, -6.3], [6.74, -2.8], [11.5, -2.8], [11.5, 2.8], [6.74, 2.8],
      [6.74, 6.0], [3.0, 8.0], [3.0, 11.3], [-3.0, 11.3], [-3.0, 8.0], [-6.74, 6.0],
      [-6.74, 2.8], [-11.5, 2.8], [-11.5, -2.8], [-6.74, -2.8],
    ].map(rot)
    // the same outline grown by ~0.5 mm, for the keepout area
    const grow = (pts, d) => {
      const n = pts.length
      return pts.map((pt, i) => {
        const a = pts[(i + n - 1) % n], b = pts[(i + 1) % n]
        const cx = pts.reduce((t, q) => t + q[0], 0) / n, cy = pts.reduce((t, q) => t + q[1], 0) / n
        const vx = pt[0] - cx, vy = pt[1] - cy, len = Math.hypot(vx, vy) || 1
        return [pt[0] + vx / len * d, pt[1] + vy / len * d]
      })
    }
    const screws = [[-9.5, 0], [9.5, 0]].map(rot)

    const poly = (pts, layer, width) =>
      `(fp_poly (pts ${pts.map(q => `(xy ${f(q[0])} ${f(q[1])})`).join(' ')}) (stroke (width ${width}) (type solid)) (fill none) (layer "${layer}"))`

    const a = p.pads_rotation * Math.PI / 180
    const names = [['VCC', p.VCC], ['GND', p.GND], ['CLK', p.CLK], ['DAT', p.DATA], ['RST', p.RST]]
    const padPos = names.map((n, i) => [
      p.pads_offset[0] + Math.cos(a) * 2.54 * i,
      p.pads_offset[1] + Math.sin(a) * 2.54 * i,
    ])
    // JLCPCB's minimum silkscreen text is 1.0 mm, too big to label every pad at 2.54 mm pitch:
    // pad 1 is square (VCC), and only the two ends of the row are labelled; full order on Fab.
    const endLabel = (txt, [x, y], dir) => `
    (fp_text user "${txt}" (at ${f(x + dir * (Math.cos(a) * 2.9))} ${f(y + dir * (Math.sin(a) * 2.9))} ${p.r}) (layer "${s}.SilkS") (effects (font (size 1 1) (thickness 0.15))${mirror}))`
    const pads = names.map((n, i) => `
    (pad "${i + 1}" thru_hole ${i === 0 ? 'rect' : 'circle'} (at ${f(padPos[i][0])} ${f(padPos[i][1])} ${p.r}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") ${n[1].str})`).join('')
      + endLabel('VCC', padPos[0], -1) + endLabel('RST', padPos[4], 1) + `
    (fp_text user "VCC GND CLK DAT RST" (at ${f((padPos[0][0] + padPos[4][0]) / 2)} ${f((padPos[0][1] + padPos[4][1]) / 2 - 1.6)} ${p.r}) (layer "${s}.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))${mirror}))`

    // keepout area needs absolute board coordinates: apply the footprint rotation + position
    let zone = ''
    if (p.include_keepout) {
      const fr = -p.r * Math.PI / 180
      const abs = grow(outline, 0.5).map(([x, y]) => [
        p.x + x * Math.cos(fr) - y * Math.sin(fr),
        p.y + x * Math.sin(fr) + y * Math.cos(fr),
      ])
      zone = `
  (zone (net 0) (net_name "") (layers "${s}.Cu") (name "trackpoint_sensor_plate")
    (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)
    (keepout (tracks allowed) (vias not_allowed) (pads allowed) (copperpour allowed) (footprints allowed))
    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon (pts ${abs.map(q => `(xy ${f(q[0])} ${f(q[1])})`).join(' ')})))`
    }

    return `
  (footprint "kabuki:trackpoint_sk8707_008"
    (layer "${s}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 -8 ${p.r}) (layer "${s}.SilkS") ${p.ref_hide}
      (effects (font (size 1 1) (thickness 0.15))${mirror}))
    (attr through_hole)
    (pad "" np_thru_hole circle (at 0 0 ${p.r}) (size ${p.hole_diameter} ${p.hole_diameter}) (drill ${p.hole_diameter}) (layers "*.Cu" "*.Mask"))
    ${screws.map(([x, y]) => `(pad "" np_thru_hole circle (at ${f(x)} ${f(y)} ${p.r}) (size ${p.screw_hole_diameter} ${p.screw_hole_diameter}) (drill ${p.screw_hole_diameter}) (layers "*.Cu" "*.Mask"))`).join('\n    ')}
    ${poly(outline, `${s}.CrtYd`, 0.05)}
    ${poly(outline, `${s}.Fab`, 0.1)}
    ${screws.map(([x, y]) => `(fp_circle (center ${f(x)} ${f(y)}) (end ${f(x + p.screw_head_diameter / 2)} ${f(y)}) (stroke (width 0.05) (type solid)) (fill none) (layer "${other}.CrtYd"))`).join('\n    ')}
    (fp_text user "SK8707-01-008 sensor" (at 0 3.5 ${p.r}) (layer "${s}.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))${mirror}))
    ${pads}
  )
  ${zone}
  `
  }
}