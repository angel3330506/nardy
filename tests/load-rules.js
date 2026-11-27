// Достаёт правила ходов прямо из index.html и запускает их в Node — без сборки и без правок самой игры.
// Берётся блок «правила» целиком (от «/* ---------- правила ---------- */» до «/* ---------- компьютер ---------- */»)
// и отдельные функции, которые живут в других местах файла: freshState, headLim, enumerate.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

function between(start, end) {
  const a = SRC.indexOf(start), b = SRC.indexOf(end, a);
  if (a < 0 || b < 0) throw new Error(`В index.html не найден блок «${start}» … «${end}» — тесты нужно поправить под новую разметку`);
  return SRC.slice(a, b);
}
// функция целиком, по парным фигурным скобкам (в этих функциях скобок внутри строк нет)
function fn(name) {
  const a = SRC.indexOf(`function ${name}(`);
  if (a < 0) throw new Error(`В index.html не найдена функция ${name}`);
  let i = SRC.indexOf('{', a), depth = 0;
  for (; i < SRC.length; i++) {
    if (SRC[i] === '{') depth++;
    else if (SRC[i] === '}' && --depth === 0) return SRC.slice(a, i + 1);
  }
  throw new Error(`Не удалось вырезать функцию ${name}`);
}
function line(prefix) {
  const a = SRC.indexOf(prefix);
  if (a < 0) throw new Error(`В index.html не найдена строка «${prefix}»`);
  return SRC.slice(a, SRC.indexOf('\n', a));
}

const code = [
  'var G = {v: "long"};',
  line('const SH='),
  between('/* ---------- правила ---------- */', '/* ---------- компьютер ---------- */'),
  line('const headLim='),
  fn('freshState'),
  fn('enumerate'),
  ';({P, Pinv, clone, key, own, homeCount, pips, violatesBlock, tryStep, tryStepShort, removeOne, nextCtx, rawSteps, maxUse, legalSteps, movesFrom, headLim, freshState, enumerate})',
].join('\n');

// Отдельный контекст на каждый вызов: состояние G у тестов не пересекается
function loadRules() {
  const sandbox = {};
  vm.createContext(sandbox);
  const R = vm.runInContext(code, sandbox, {filename: 'index.html#rules'});
  R.setVariant = v => { sandbox.G = {v}; };
  R.setHead2 = on => { sandbox.G.head2 = !!on; };
  return R;
}

module.exports = {loadRules};
