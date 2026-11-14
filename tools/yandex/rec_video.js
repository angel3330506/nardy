// Видео геймплея для карточки Яндекс Игр: настоящая партия (вы — «лучший ход», соперник — дядя Ашот), 16:9.
// node rec_video.js <папка кадров> [секунд] → кадры fNNNNN.jpg + times.json; склейка — ffmpeg (см. ниже в консоли)
const {chromium}=require('playwright'); const fs=require('fs'); const D=process.argv[2], SEC=+(process.argv[3]||28);
(async()=>{ const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:960,height:540},deviceScaleFactor:2,userAgent:'Mozilla/5.0 NardyApp NardyAndroid'}); const p=await c.newPage();
 await p.goto('http://localhost:8765/index.html?mock');
 await p.evaluate(()=>{ localStorage.clear(); localStorage.setItem('nardy-tutorial-v1','1');
   localStorage.setItem('nardy-settings-v1',JSON.stringify({sound:false,lang:'ru',skin:'ararat',tod:'day',level:'medium',automove:false,variant:'long'})); });
 await p.reload(); await p.waitForTimeout(2500);
 await p.evaluate(()=>__t.ev("rollOff=function(){ busy=false; G.ro=false; G.phase='roll'; G.turn=0; render(); }; 0"));
 await p.click('#mAi'); await p.waitForTimeout(2200);
 // водитель: за белых бросает и ходит «как сильный игрок», с паузами, как живой человек
 await p.evaluate(()=>__t.ev(`window.__drv=setInterval(()=>{ if(!G||G.phase==='over'||busy||G.auto||G.turn!==0) return;
   const now=Date.now(); if(window.__wait&&now<window.__wait) return;
   if(G.phase==='roll'){ window.__wait=now+700; __t.roll(); return; }
   if(G.phase==='move'&&G.steps.length&&!G.hist.length){ window.__wait=now+900; const path=aiChoose('hard'); if(path.length) doMove(path); return; }
   if(G.phase==='move'&&(!G.steps.length||G.hist.length)){ window.__wait=now+600; humanEnd(); } },150); 0`));
 const cdp=await c.newCDPSession(p); const frames=[]; let t0=null;
 cdp.on('Page.screencastFrame',async f=>{ const ts=f.metadata.timestamp; if(t0==null) t0=ts; fs.writeFileSync(`${D}/f${String(frames.length).padStart(5,'0')}.jpg`,Buffer.from(f.data,'base64')); frames.push(ts-t0); try{ await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId}); }catch(e){} });
 await p.addStyleTag({content:'body::after{content:"";position:fixed;left:0;top:0;width:1px;height:1px;opacity:.01;animation:tk 1s linear infinite}@keyframes tk{to{transform:translateX(1px)}}'});
 await cdp.send('Page.startScreencast',{format:'jpeg',quality:92,maxWidth:1920,maxHeight:1080,everyNthFrame:1});
 await p.waitForTimeout(SEC*1000);
 await cdp.send('Page.stopScreencast'); await p.waitForTimeout(300);
 fs.writeFileSync(D+'/times.json',JSON.stringify({frames})); console.log(frames.length,'frames',frames[frames.length-1]);
 await b.close(); })();
