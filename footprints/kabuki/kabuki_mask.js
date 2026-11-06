// Kabuki — easter egg: a small kabuki-style mask (kumadori face paint) drawn in silkscreen,
// with up to two lines of text beside it. Original line art; silkscreen only, no copper.
//
// Params:
//   side: F or B (default F). On B the art and text are mirrored so they read correctly
//     when you look at the back of the board.
//   height: mask height in mm (default 6)
//   line: silkscreen stroke width in mm (default 0.18; JLCPCB's minimum is 0.15)
//   text1, text2: text to the right of the mask ('' to leave out)
//   text_size: text height in mm (default 1.0)

module.exports = {
  params: {
    designator: 'EGG',
    side: 'F',
    height: 6,
    line: 0.18,
    text1: 'KABUKI',
    text2: '',
    text_size: 1.0,
  },
  body: p => {
    const k = p.height / 7          // art is drawn 7 mm tall, then scaled
    const mx = p.side === 'B' ? -1 : 1
    const layer = `${p.side}.SilkS`
    const f = v => (+v).toFixed(3)
    const P = ([x, y]) => [x * k * mx, y * k]
    const seg = (a, b) => `(fp_line (start ${f(P(a)[0])} ${f(P(a)[1])}) (end ${f(P(b)[0])} ${f(P(b)[1])}) (stroke (width ${p.line}) (type solid)) (layer "${layer}"))`
    const path = pts => pts.slice(1).map((q, i) => seg(pts[i], q)).join('\n    ')
    const both = pts => path(pts) + '\n    ' + path(pts.map(([x, y]) => [-x, y]))
    // simple quadratic curve sampler
    const curve = (a, c, b, n = 8) => Array.from({ length: n + 1 }, (_, i) => {
      const t = i / n
      return [(1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t ** 2 * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t ** 2 * b[1]]
    })

    const art = []
    // face: an egg shape, a little wider at the brow than at the chin
    const face = Array.from({ length: 49 }, (_, i) => {
      const t = 2 * Math.PI * i / 48
      const rx = 2.55 - 0.2 * Math.sin(t)   // KiCad y points down: sin(t) < 0 is the brow
      return [rx * Math.cos(t), 3.5 * Math.sin(t)]
    })
    art.push(path(face))
    // hairline across the forehead (stays inside the face)
    art.push(path(curve([-2.15, -2.05], [0, -2.95], [2.15, -2.05])))
    // bold brows sweeping up and out (two strokes each for weight)
    art.push(both(curve([-0.45, -1.15], [-1.25, -1.3], [-2.0, -1.95])))
    art.push(both(curve([-0.5, -0.98], [-1.3, -1.12], [-2.1, -1.75])))
    // eyes: narrow, tilted up at the outer corner
    art.push(both(curve([-0.45, -0.45], [-1.15, -0.75], [-1.85, -1.0])))
    art.push(both(curve([-0.45, -0.45], [-1.15, -0.35], [-1.85, -1.0])))
    // kumadori: two streaks from under the eye up to the temple
    art.push(both(curve([-0.7, -0.05], [-1.85, -0.15], [-2.4, -1.3])))
    art.push(both(curve([-0.9, 0.4], [-2.0, 0.35], [-2.55, -0.55])))
    // nose
    art.push(path([[0, -0.6], [0, 0.5]]))
    art.push(both([[0, 0.5], [-0.3, 0.65]]))
    // mouth: a stern down-turned line, with streaks running down from its corners
    art.push(path(curve([-0.95, 1.85], [0, 1.2], [0.95, 1.85])))
    art.push(both(curve([-0.95, 1.85], [-1.3, 2.2], [-1.35, 2.75])))
    // chin mark
    art.push(path(curve([-0.4, 2.65], [0, 2.85], [0.4, 2.65])))

    const tx = (2.75 * k + 0.9) * mx
    const just = p.side === 'B' ? '(justify right mirror)' : '(justify left)'
    const txt = (s, y) => s ? `(fp_text user "${s}" (at ${f(tx)} ${f(y)} ${p.r}) (layer "${layer}") (effects (font (size ${p.text_size} ${p.text_size}) (thickness ${Math.max(0.15, p.text_size * 0.15)})) ${just}))` : ''
    const y1 = p.text2 ? -0.75 * p.text_size : 0
    const y2 = 0.75 * p.text_size

    return `
  (footprint "kabuki:kabuki_mask"
    (layer "${p.side}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 0 ${p.r}) (layer "${p.side}.Fab") hide (effects (font (size 1 1) (thickness 0.15))))
    (attr board_only exclude_from_pos_files exclude_from_bom)
    ${art.join('\n    ')}
    ${txt(p.text1, y1)}
    ${txt(p.text2, y2)}
  )
  `
  }
}
