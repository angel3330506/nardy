'use strict';
// Длинные нарды: правила ходов
const test = require('node:test');
const assert = require('node:assert/strict');
const {setup} = require('./helpers');

const R = setup('long');
const noHead = {headUsed: 0, headLimit: 1};

test('начальная расстановка: по 15 шашек на голове, головы друг напротив друга', () => {
  const s = R.freshState('long');
  assert.deepEqual(R.view(s, 0), {0: 15});
  assert.deepEqual(R.view(s, 1), {0: 15});
  assert.equal(R.P(0, 0), 0);
  assert.equal(R.P(1, 0), 12);
  assert.equal(s.bar, undefined, 'в длинных нет бара');
});

test('оба игрока ходят в одну сторону: дом чёрных — пункты 6…11 доски', () => {
  assert.equal(R.P(1, 18), 6);
  assert.equal(R.P(1, 23), 11);
  for (let p = 0; p < 24; p++) assert.equal(R.Pinv(1, R.P(1, p)), p);
});

test('с головы за ход — одна шашка, две только первым броском 6-6, 4-4, 3-3', () => {
  for (const d of [3, 4, 6]) assert.equal(R.headLim(true, d, d), 2, `первый бросок ${d}-${d}`);
  for (const d of [1, 2, 5]) assert.equal(R.headLim(true, d, d), 1, `первый бросок ${d}-${d}`);
  assert.equal(R.headLim(true, 6, 5), 1);
  assert.equal(R.headLim(false, 6, 6), 1, 'не первый бросок');
});

test('быстрая игра (head2): с головы всегда по две', () => {
  const Q = setup('long');
  Q.setHead2(true);
  assert.equal(Q.headLim(false, 6, 5), 2);
});

test('первый ход 6-5: с головы уходит одна шашка и идёт на 11', () => {
  assert.deepEqual(R.endViews(R.freshState('long'), 0, [6, 5]), [{0: 14, 11: 1}]);
});

test('первый ход 6-6: две шашки на шестой пункт, дальше голова соперника', () => {
  assert.deepEqual(R.endViews(R.freshState('long'), 0, [6, 6], {headLimit: 2}), [{0: 13, 6: 2}]);
});

test('первый ход 4-4: две шашки на восьмой пункт', () => {
  assert.deepEqual(R.endViews(R.freshState('long'), 0, [4, 4], {headLimit: 2}), [{0: 13, 8: 2}]);
});

test('первый ход 3-3: 6+6 или 3+9', () => {
  assert.deepEqual(R.endViews(R.freshState('long'), 0, [3, 3], {headLimit: 2}), [{0: 13, 3: 1, 9: 1}, {0: 13, 6: 2}]);
});

test('первый ход 5-5: с головы только одна шашка, она проходит все четыре пятёрки', () => {
  assert.deepEqual(R.endViews(R.freshState('long'), 0, [5, 5]), [{0: 14, 20: 1}]);
});

test('чёрные ходят так же: первый ход 6-5', () => {
  assert.deepEqual(R.endViews(R.freshState('long'), 1, [6, 5]), [{0: 14, 11: 1}]);
});

test('на пункт с чужой шашкой ходить нельзя (бить нельзя)', () => {
  const s = R.pos({w: {0: 14, 10: 1}, b: {0: 14, 3: 1}});   // чёрная на своём 3-м = 15-й пункт белых
  assert.equal(R.tryStep(s, 0, 10, 5, noHead), null);
  assert.ok(R.tryStep(s, 0, 10, 4, noHead));
});

test('ходить можно только своей шашкой', () => {
  const s = R.freshState('long');
  assert.equal(R.tryStep(s, 0, 5, 1, noHead), null);
  assert.equal(R.tryStep(s, 0, 12, 1, noHead), null, 'голова чёрных');
});

test('после хода с головы второй с неё нельзя (лимит 1)', () => {
  const s = R.freshState('long');
  assert.ok(R.tryStep(s, 0, 0, 3, noHead));
  assert.equal(R.tryStep(s, 0, 0, 3, {headUsed: 1, headLimit: 1}), null);
});

test('заграждение из шести подряд нельзя, если впереди него нет ни одной шашки соперника', () => {
  const w = {0: 9, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1};
  const s = R.pos({w, b: {0: 15}});
  assert.equal(R.tryStep(s, 0, 0, 6, noHead), null);
  assert.ok(!R.stepsOf(R.ctx(s, 0, [6, 1])).some(([f, d]) => f === 0 && d === 6));
});

test('заграждение из шести можно, если впереди него есть шашка соперника', () => {
  // чёрная на своём 20-м (8-й пункт белых) — впереди белых пунктов 1…6, если смотреть глазами чёрных
  const s = R.pos({w: {0: 9, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, b: {0: 14, 20: 1}});
  assert.ok(R.tryStep(s, 0, 0, 6, noHead));
});

test('пять подряд — не заграждение, ходить можно', () => {
  const s = R.pos({w: {0: 10, 1: 1, 2: 1, 3: 1, 4: 1}, b: {0: 15}});
  assert.ok(R.tryStep(s, 0, 0, 6, noHead), 'пункты 0…4 и 6 — разрыв на 5-м');
  assert.equal(R.tryStep(s, 0, 0, 5, noHead), null, 'пункты 0…5 — уже шесть подряд вместе с головой');
});

test('если можно сыграть оба кубика — играть обязательно оба', () => {
  // 10+3 закрыто, 10+5 → 15, потом 15+3 → 18; с головы 3 и 5 закрыты
  const s = R.pos({w: {0: 14, 10: 1}, b: {0: 12, 15: 1, 17: 1, 1: 1}});   // чёрные на белых 3, 5 и 13
  assert.deepEqual(R.stepsOf(R.ctx(s, 0, [3, 5])), [[10, 5]]);
  assert.deepEqual(R.endViews(s, 0, [3, 5]), [{0: 14, 18: 1}]);
});

test('если сыграть можно только один кубик — обязательно больший', () => {
  // 10+3 → 13 и 10+5 → 15 свободны, но 18 закрыто, с головы 3 и 5 закрыты
  const s = R.pos({w: {0: 14, 10: 1}, b: {0: 12, 15: 1, 17: 1, 6: 1}});   // чёрные на белых 3, 5 и 18
  assert.deepEqual(R.stepsOf(R.ctx(s, 0, [3, 5])), [[10, 5]]);
  assert.deepEqual(R.endViews(s, 0, [3, 5]), [{0: 14, 15: 1}]);
});

test('нет ходов — ход пропадает, позиция не меняется', () => {
  const s = R.pos({w: {0: 15}, b: {0: 10, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1}});   // чёрные на белых 1…5
  assert.deepEqual(R.stepsOf(R.ctx(s, 0, [2, 4])), []);
  assert.deepEqual(R.endViews(s, 0, [2, 4]), [{0: 15}]);
});

test('выбрасывать можно, только когда все 15 шашек в доме', () => {
  const s = R.pos({w: {17: 1, 18: 14}, b: {0: 15}});
  assert.equal(R.tryStep(s, 0, 18, 6, noHead), null);
  const t = R.pos({w: {18: 15}, b: {0: 15}});
  const ns = R.tryStep(t, 0, 18, 6, noHead);
  assert.ok(ns);
  assert.equal(ns.off[0], 1);
});

test('выброс большим кубиком — только с самого дальнего пункта', () => {
  const s = R.pos({w: {18: 5, 20: 10}, b: {0: 15}});
  assert.equal(R.tryStep(s, 0, 20, 6, noHead), null, 'на 18-м ещё есть шашки');
  const t = R.pos({w: {20: 15}, b: {0: 15}});
  assert.ok(R.tryStep(t, 0, 20, 6, noHead), 'дальше 20-го никого — можно выбросить шестёркой');
  assert.ok(R.tryStep(s, 0, 20, 4, noHead), 'точным кубиком можно всегда');
});

test('в доме можно ходить и внутри, если выбросить нельзя', () => {
  const s = R.pos({w: {18: 15}, b: {0: 15}});
  const steps = R.stepsOf(R.ctx(s, 0, [6, 1]));
  assert.deepEqual(steps, [[18, 1], [18, 6]]);
});

test('выброшенные шашки считаются в доме', () => {
  const s = R.pos({w: {23: 1}, b: {0: 15}, off: [14, 0]});
  assert.equal(R.homeCount(s, 0), 15);
  assert.deepEqual(R.endViews(s, 0, [6, 2]), [{}]);
});

test('movesFrom: куда дойдёт шашка с головы при 6-5', () => {
  const m = R.movesFrom(R.ctx(R.freshState('long'), 0, [6, 5]), 0);
  assert.deepEqual([...m.keys()].sort((a, b) => a - b), [5, 6, 11]);
  assert.equal(m.get(11).length, 2);
});
