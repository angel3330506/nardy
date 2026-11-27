'use strict';
// Случайные партии от начала до конца: на каждом шаге проверяем, что правила соблюдены.
// Генератор с фиксированным зерном — при падении партия повторится один в один.
const test = require('node:test');
const assert = require('node:assert/strict');
const {setup, rng} = require('./helpers');

const GAMES = 40, MAX_TURNS = 1500;

function checkBoard(R, s, where) {
  for (let i = 0; i < 24; i++) {
    assert.ok(s.n[i] >= 0 && s.n[i] <= 15, `${where}: на пункте ${i} ${s.n[i]} шашек`);
    if (s.n[i]) assert.ok(s.o[i] === 0 || s.o[i] === 1, `${where}: у пункта ${i} нет хозяина`);
  }
  for (const pl of [0, 1]) assert.equal(R.total(s, pl), 15, `${where}: у игрока ${pl} не 15 шашек`);
}

// заграждение — своя проверка, независимо от violatesBlock: 6+ подряд перед соперником без его шашек впереди
function blockBroken(R, s, pl, to) {
  const opp = 1 - pl, q = R.Pinv(opp, R.P(pl, to));
  const held = x => R.own(s, R.P(opp, x), pl);
  let lo = q, hi = q;
  while (lo > 0 && held(lo - 1)) lo--;
  while (hi < 23 && held(hi + 1)) hi++;
  if (hi - lo + 1 < 6) return false;
  for (let x = hi + 1; x < 24; x++) if (R.own(s, R.P(opp, x), opp)) return false;
  return true;
}

function play(v, seed) {
  const R = setup(v), rnd = rng(seed), die = () => 1 + Math.floor(rnd() * 6);
  let s = R.freshState(v), pl = 0;
  const first = [true, true];
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const a = die(), b = die(), where = `${v}, зерно ${seed}, ход ${turn}, кубики ${a}-${b}`;
    const headLimit = R.headLim(first[pl], a, b); first[pl] = false;
    const ctx = R.ctx(s, pl, [a, b], {headLimit});
    const need = R.maxUse(ctx, new Map());
    const ends = R.enumerate(ctx);
    assert.ok(ends.length >= 1, `${where}: нет ни одного итога хода`);
    const keys = new Set();
    for (const e of ends) {
      assert.equal(e.path.length, need, `${where}: сыграно ${e.path.length} кубиков из возможных ${need}`);
      const k = R.key(e.s); assert.ok(!keys.has(k), `${where}: итог хода повторяется`); keys.add(k);
    }
    const end = ends[Math.floor(rnd() * ends.length)];
    // переигрываем путь по шагам и сверяем каждый
    let c = ctx, headUsed = 0;
    for (const st of end.path) {
      if (v === 'short' && c.s.bar[pl] > 0) assert.equal(st.from, -1, `${where}: ход мимо бара`);
      if (v === 'long' && st.from === 0) headUsed++;
      const ns = R.tryStep(c.s, pl, st.from, st.d, c);
      assert.ok(ns, `${where}: шаг ${st.from}+${st.d} не проходит tryStep`);
      assert.equal(R.key(ns), R.key(st.ns));
      checkBoard(R, ns, where);
      if (v === 'long') {
        assert.deepEqual(R.view(ns, 1 - pl), R.view(c.s, 1 - pl), `${where}: в длинных шашки соперника не трогаются`);
        if (st.to !== 'off') assert.ok(!blockBroken(R, ns, pl, st.from + st.d), `${where}: недопустимое заграждение`);
      }
      c = R.nextCtx(c, st);
    }
    assert.equal(R.key(c.s), R.key(end.s));
    if (v === 'long') assert.ok(headUsed <= headLimit, `${where}: с головы ${headUsed} при лимите ${headLimit}`);
    s = end.s;
    if (s.off[pl] === 15) return {winner: pl, turns: turn + 1};
    pl = 1 - pl;
  }
  assert.fail(`${v}, зерно ${seed}: партия не закончилась за ${MAX_TURNS} ходов`);
}

for (const v of ['long', 'short'])
  test(`${v === 'long' ? 'длинные' : 'короткие'}: ${GAMES} случайных партий до конца без нарушений правил`, () => {
    for (let g = 1; g <= GAMES; g++) {
      const r = play(v, g * 7919);
      assert.ok(r.winner === 0 || r.winner === 1);
    }
  });
