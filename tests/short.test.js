'use strict';
// Короткие нарды: правила ходов
const test = require('node:test');
const assert = require('node:assert/strict');
const {setup} = require('./helpers');

const R = setup('short');

test('начальная расстановка: 2-5-3-5, у чёрных зеркально', () => {
  const s = R.freshState('short');
  assert.deepEqual(R.view(s, 0), {0: 2, 11: 5, 16: 3, 18: 5});
  assert.deepEqual(R.view(s, 1), {0: 2, 11: 5, 16: 3, 18: 5});
  assert.deepEqual([...s.bar], [0, 0]);
  assert.equal(R.total(s, 0), 15);
  assert.equal(R.total(s, 1), 15);
});

test('игроки ходят навстречу друг другу', () => {
  assert.equal(R.P(1, 0), 23);
  assert.equal(R.P(1, 23), 0);
  for (let p = 0; p < 24; p++) assert.equal(R.Pinv(1, R.P(1, p)), p);
});

test('ограничения головы нет', () => {
  assert.equal(R.headLim(true, 6, 5), 99);
  assert.equal(R.headLim(false, 1, 1), 99);
});

test('одиночную шашку соперника сбивают на бар', () => {
  const s = R.pos({w: {5: 1}, b: {15: 1}});   // чёрная на своём 15-м = 8-й пункт белых
  const ns = R.tryStep(s, 0, 5, 3, {});
  assert.ok(ns);
  assert.deepEqual(R.view(ns, 0), {8: 1});
  assert.deepEqual(R.view(ns, 1), {});
  assert.deepEqual([...ns.bar], [0, 1]);
});

test('на пункт с двумя и больше шашками соперника нельзя', () => {
  const s = R.pos({w: {5: 1}, b: {15: 2}});
  assert.equal(R.tryStep(s, 0, 5, 3, {}), null);
});

test('на свой пункт и на пустой — можно', () => {
  const s = R.pos({w: {5: 1, 8: 3}, b: {0: 15}});
  assert.ok(R.tryStep(s, 0, 5, 3, {}));
  assert.ok(R.tryStep(s, 0, 5, 2, {}));
});

test('пока есть шашка на баре, ходить можно только ей', () => {
  const s = R.pos({w: {10: 14}, b: {0: 15}, bar: [1, 0]});
  const steps = R.stepsOf(R.ctx(s, 0, [3, 5]));
  assert.deepEqual(steps, [[-1, 3], [-1, 5]]);
  assert.equal(R.tryStep(s, 0, 10, 3, {}), null);
});

test('вход с бара: кубик 1 ставит на пункт 0, кубик 6 — на пункт 5', () => {
  const s = R.pos({w: {10: 14}, b: {0: 15}, bar: [1, 0]});
  assert.equal(R.view(R.tryStep(s, 0, -1, 1, {}), 0)[0], 1);
  assert.equal(R.view(R.tryStep(s, 0, -1, 6, {}), 0)[5], 1);
});

test('вход с бара сбивает одиночную шашку', () => {
  const s = R.pos({w: {10: 14}, b: {21: 1, 0: 14}, bar: [1, 0]});   // чёрная на своём 21-м = 2-й пункт белых
  const ns = R.tryStep(s, 0, -1, 3, {});
  assert.deepEqual(R.view(ns, 0), {2: 1, 10: 14});
  assert.deepEqual([...ns.bar], [0, 1]);
});

test('вход закрыт — ход пропадает целиком', () => {
  const s = R.pos({w: {10: 14}, b: {21: 2, 19: 2, 0: 11}, bar: [1, 0]});   // белые 2 и 4 закрыты
  assert.deepEqual(R.stepsOf(R.ctx(s, 0, [3, 5])), []);
  assert.deepEqual(R.endViews(s, 0, [3, 5]), [{10: 14}]);
});

test('с двумя шашками на баре и дублем: обе входят, потом свободный ход', () => {
  const s = R.pos({w: {10: 13}, b: {0: 15}, bar: [2, 0]});
  for (const e of R.ends(s, 0, [2, 2])) {
    assert.equal(e.s.bar[0], 0);
    assert.equal(e.path.length, 4);
    assert.deepEqual([e.path[0].from, e.path[1].from], [-1, -1]);
  }
});

test('чёрные входят с бара в свой начальный угол', () => {
  const s = R.pos({w: {0: 15}, b: {10: 14}, bar: [0, 1]});
  const ns = R.tryStep(s, 1, -1, 4, {});
  assert.equal(ns.n[R.P(1, 3)], 1);
  assert.equal(ns.o[R.P(1, 3)], 1);
  assert.equal(R.P(1, 3), 20);
});

test('выбрасывать нельзя, пока шашка на баре', () => {
  const s = R.pos({w: {18: 14}, b: {0: 15}, bar: [1, 0]});
  assert.equal(R.tryStep(s, 0, 18, 6, {}), null);
});

test('выброс: точный кубик — всегда, больший — только с дальнего пункта', () => {
  const s = R.pos({w: {18: 5, 20: 10}, b: {0: 15}});
  assert.ok(R.tryStep(s, 0, 18, 6, {}));
  assert.ok(R.tryStep(s, 0, 20, 4, {}));
  assert.equal(R.tryStep(s, 0, 20, 6, {}), null);
  const t = R.pos({w: {20: 15}, b: {0: 15}});
  assert.ok(R.tryStep(t, 0, 20, 6, {}));
});

test('не все в доме — выбрасывать нельзя', () => {
  const s = R.pos({w: {17: 1, 18: 14}, b: {0: 15}});
  assert.equal(R.tryStep(s, 0, 18, 6, {}), null);
});

test('если сыграть можно только один кубик — обязательно больший', () => {
  // одна белая на 10-м, остальные выброшены: 10+3 и 10+5 свободны, а 18 закрыто
  const s = R.pos({w: {10: 1}, b: {5: 2, 0: 13}, off: [14, 0]});   // чёрные 2 на своём 5-м = 18-й пункт белых
  assert.deepEqual(R.stepsOf(R.ctx(s, 0, [3, 5])), [[10, 5]]);
  assert.deepEqual(R.endViews(s, 0, [3, 5]), [{15: 1}]);
});

test('первый ход 6-1 из начальной: несколько вариантов, все с двумя шагами', () => {
  const ends = R.ends(R.freshState('short'), 0, [6, 1]);
  assert.ok(ends.length > 1);
  for (const e of ends) {
    assert.equal(e.path.length, 2);
    assert.equal(R.total(e.s, 0), 15);
  }
  // классический ход «6-1: закрыть 7-й пункт» (белые 11+6 → 17 и 16+1 → 17)
  assert.ok(ends.some(e => R.view(e.s, 0)[17] === 2));
});
