'use strict';
const {loadRules} = require('./load-rules');

// массивы из контекста vm — в обычные, чтобы deepStrictEqual их сравнивал
const plain = x => JSON.parse(JSON.stringify(x));

// Позиция «глазами игроков»: w и b — {пункт: шашек}, где пункт 0…23 считается от старта своего игрока (18…23 — дом).
// off — сколько уже выброшено, bar — сколько на баре (только короткие).
function setup(v) {
  const R = loadRules();
  R.setVariant(v);
  R.pos = ({w = {}, b = {}, off = [0, 0], bar = [0, 0]} = {}) => {
    const s = {o: new Int8Array(24), n: new Int8Array(24), off: off.slice()};
    if (v === 'short') s.bar = bar.slice();
    for (const [pl, side] of [[0, w], [1, b]])
      for (const [p, c] of Object.entries(side)) {
        const i = R.P(pl, +p);
        if (s.n[i]) throw new Error(`пункт ${i} уже занят`);
        s.o[i] = pl; s.n[i] = c;
      }
    return s;
  };
  // где стоят шашки игрока pl, в его собственных пунктах: {пункт: шашек}
  R.view = (s, pl) => {
    const r = {};
    for (let p = 0; p < 24; p++) { const i = R.P(pl, p); if (R.own(s, i, pl)) r[p] = s.n[i]; }
    return r;
  };
  R.ctx = (s, pl, dice, extra = {}) => ({s, pl, rem: dice[0] === dice[1] && dice.length === 2 ? [dice[0], dice[0], dice[0], dice[0]] : dice.slice(), headUsed: 0, headLimit: v === 'short' ? 99 : 1, ...extra});
  R.ends = (s, pl, dice, extra) => R.enumerate(R.ctx(s, pl, dice, extra));
  R.endViews = (s, pl, dice, extra) => plain(R.ends(s, pl, dice, extra).map(e => R.view(e.s, pl))).sort((a, b) => JSON.stringify(a) < JSON.stringify(b) ? -1 : 1);
  R.stepsOf = c => plain(R.legalSteps(c, new Map()).map(st => [st.from, st.d])).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  R.total = (s, pl) => { let c = s.off[pl] + (s.bar ? s.bar[pl] : 0); for (let i = 0; i < 24; i++) if (R.own(s, i, pl)) c += s.n[i]; return c; };
  return R;
}

// простой детерминированный генератор, чтобы случайные партии повторялись
function rng(seed) {
  let x = seed >>> 0 || 1;
  return () => { x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0; return x / 4294967296; };
}

module.exports = {setup, rng};
