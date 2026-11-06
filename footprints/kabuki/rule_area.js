// Kabuki — rectangular KiCad rule area (keepout), placed like any other footprint
//
// ceoloide/utility_keepout_zone takes absolute board coordinates; this one follows an
// Ergogen anchor, so it moves with the layout.
//
// Params:
//   side: both (default), F or B
//   name: zone name shown in KiCad
//   width, height: size in mm, centred on the anchor
//   tracks, vias, pads, copperpour, footprints: true = allowed (all default true)

module.exports = {
  params: {
    side: 'both',
    name: 'rule_area',
    width: 10,
    height: 10,
    tracks: true,
    vias: true,
    pads: true,
    copperpour: true,
    footprints: true,
  },
  body: p => {
    const allow = v => (v ? 'allowed' : 'not_allowed')
    const sides = p.side === 'both' ? ['F', 'B'] : [p.side]
    const a = -p.r * Math.PI / 180
    const w = p.width / 2, h = p.height / 2
    const pts = [[-w, -h], [w, -h], [w, h], [-w, h]].map(([x, y]) => [
      p.x + x * Math.cos(a) - y * Math.sin(a),
      p.y + x * Math.sin(a) + y * Math.cos(a),
    ])
    return sides.map(side => `
  (zone (net 0) (net_name "") (layers "${side}.Cu") (name "${p.name}")
    (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)
    (keepout (tracks ${allow(p.tracks)}) (vias ${allow(p.vias)}) (pads ${allow(p.pads)}) (copperpour ${allow(p.copperpour)}) (footprints ${allow(p.footprints)}))
    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon (pts ${pts.map(q => `(xy ${q[0].toFixed(4)} ${q[1].toFixed(4)})`).join(' ')})))
  `).join('\n')
  }
}
