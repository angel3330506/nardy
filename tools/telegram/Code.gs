/**
 * «Нарды» → сообщения об ошибках в Telegram.
 * Google Apps Script (бесплатно, нужен только Google-аккаунт). Токен бота хранится здесь, в свойствах скрипта,
 * а не в игре — поэтому никто не сможет им воспользоваться.
 *
 * Настройка (один раз):
 *  1. Telegram → @BotFather → /newbot → получите токен.
 *  2. Напишите своему боту любое сообщение (например «привет»).
 *  3. script.google.com → «Новый проект» → вставьте этот код целиком.
 *  4. ⚙ «Настройки проекта» → «Свойства скрипта» → добавить: TOKEN = <токен бота>.
 *  5. Выберите функцию setup → «Выполнить» → разрешите доступ. В журнале будет «chat id сохранён».
 *  6. «Начать развёртывание» → «Новое развёртывание» → тип «Веб-приложение»,
 *     «Запуск от имени»: Я, «У кого есть доступ»: Все → «Развернуть» → скопируйте URL веб-приложения.
 */
function setup() {
  const p = PropertiesService.getScriptProperties();
  const r = JSON.parse(UrlFetchApp.fetch('https://api.telegram.org/bot' + p.getProperty('TOKEN') + '/getUpdates').getContentText());
  const m = (r.result || []).reverse().find(u => u.message);
  if (!m) throw new Error('Сначала напишите боту любое сообщение в Telegram и запустите setup ещё раз');
  p.setProperty('CHAT', String(m.message.chat.id));
  tg('sendMessage', { chat_id: m.message.chat.id, text: '✅ Бот подключён: сюда будут приходить сообщения об ошибках из «Нард».' });
  Logger.log('chat id сохранён: ' + m.message.chat.id);
}

function tg(method, payload) {
  const token = PropertiesService.getScriptProperties().getProperty('TOKEN');
  return UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/' + method, { method: 'post', payload, muteHttpExceptions: true });
}

function doPost(e) {
  const chat = PropertiesService.getScriptProperties().getProperty('CHAT');
  let d; try { d = JSON.parse(e.postData.contents); } catch (err) { return out('bad json'); }
  if (!chat || !d || typeof d.text !== 'string' || !d.text.trim()) return out('skip');
  // защита от спама: не больше 30 сообщений в час
  const cache = CacheService.getScriptCache(), n = +(cache.get('n') || 0);
  if (n > 30) return out('rate'); cache.put('n', String(n + 1), 3600);
  const clip = (s, k) => String(s || '').slice(0, k);
  const msg = '🐞 Сообщение об ошибке\n\n' + clip(d.text, 1500) +
    '\n\n👤 ' + clip(d.name, 40) + '   ·   сборка ' + clip(d.v, 10) +
    '\n📱 ' + clip(d.ua, 200) + (d.state ? '\n♟ ' + clip(d.state, 600) : '');
  tg('sendMessage', { chat_id: chat, text: msg });
  const imgs = [].concat(d.img ? [d.img] : [], Array.isArray(d.pics) ? d.pics.slice(0, 3) : []);
  imgs.forEach((u, i) => {
    const m = /^data:image\/(png|jpeg);base64,(.+)$/.exec(String(u)); if (!m || m[2].length > 1200000) return;
    const blob = Utilities.newBlob(Utilities.base64Decode(m[2]), 'image/' + m[1], 'img' + i + '.' + (m[1] === 'png' ? 'png' : 'jpg'));
    tg('sendPhoto', { chat_id: chat, photo: blob, caption: d.img && i === 0 ? 'Снимок экрана' : 'Вложение ' + (d.img ? i : i + 1) });
  });
  return out('ok');
}
function out(s) { return ContentService.createTextOutput(s); }
