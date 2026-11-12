// Запись экрана для ролика «Гравюра»: заставка «резец гравёра» → меню с крышкой → партия на «Гравюре» с судьёй Левоном.
// node rec_grav.js <папка кадров>   (игра на http://localhost:8765, кадры fNNNNN.jpg + times.json с метками)
const {chromium}=require('playwright'); const fs=require('fs'); const D=process.argv[2];
(async()=>{ const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:956,height:440},deviceScaleFactor:2,userAgent:'Mozilla/5.0 NardyApp NardyAndroid'});
 const p=await c.newPage(); const ev=s=>p.evaluate(s=>__t.ev(s),s);
 await p.goto('http://localhost:8765/index.html?mock'); await p.evaluate(()=>{localStorage.clear();localStorage.setItem('nardy-tutorial-v1','1');
   localStorage.setItem('nardy-settings-v1',JSON.stringify({sound:false,skin:'gravura',level:'judge',tod:'evening',lang:'ru',automove:false,variant:'long'}))});
 await p.reload(); await p.waitForTimeout(2500);                                            // прогреть картинки (крышки, порядок резца, доска)
 await p.addStyleTag({content:'body::after{content:"";position:fixed;left:0;top:0;width:1px;height:1px;opacity:.01;animation:tick 1s linear infinite}@keyframes tick{to{transform:translateX(1px)}}'});
 const cdp=await c.newCDPSession(p); const frames=[]; let t0=null;
 cdp.on('Page.screencastFrame',async f=>{ const ts=f.metadata.timestamp; if(t0==null) t0=ts; const n=frames.length; fs.writeFileSync(`${D}/f${String(n).padStart(5,'0')}.jpg`,Buffer.from(f.data,'base64')); frames.push(ts-t0); try{ await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId}); }catch(e){} });
 const T=Date.now(), mark=[], M=n=>mark.push([n,(Date.now()-T)/1000]); const W=ms=>p.waitForTimeout(ms);
 await cdp.send('Page.startScreencast',{format:'jpeg',quality:92,maxWidth:1912,maxHeight:880,everyNthFrame:1});
 await p.goto('http://localhost:8765/index.html?mock&intro'); M('intro');
 await p.addStyleTag({content:'body::after{content:"";position:fixed;left:0;top:0;width:1px;height:1px;opacity:.01;animation:tick 1s linear infinite}@keyframes tick{to{transform:translateX(1px)}}'});
 await W(7600); M('menu');
 await ev(`window.FV=[5,3]; window.FT=1;
  { const _dr=doRoll; doRoll=function(a,st,l,li,v){ return _dr(a,st,l,li,v||window.FV); };
    const _s=say; say=function(k){ return _s(k,1); };
    PHRASES.judge.start=['Играем честно. Бросай.']; PHRASES.judge.myDouble=['Дубль. Засчитано.'];
    rollOff=function(){ busy=false; G.ro=false; G.phase='roll'; G.turn=window.FT; render(); if(G.turn===0) promptRoll(); else setStatus(opp()[0]+' ходит первым.'); }; } 0`);
 await W(1200); await p.click('#mAi'); M('open');
 await W(3200); await ev('say("start"); 0'); M('say1'); await W(1600); await ev('aiTurn(); 0'); M('roll1');
 await W(4200); await ev('window.FV=[6,4]; __t.roll(); 0'); M('roll2');
 await W(1800); await ev('{ const st=G.steps.find(x=>x.src===0)||G.steps[0]; if(st){ G.sel=st.src; G.targets=null; render(); } } 0'); M('sel');
 await W(1700); await ev('{ const t=G.targets&&[...G.targets.values()][0]; if(t) doMove(t); } 0'); M('move');
 await W(2200); M('end');
 await cdp.send('Page.stopScreencast'); await W(300);
 fs.writeFileSync(D+'/times.json',JSON.stringify({frames,mark})); console.log(frames.length,'frames',frames[frames.length-1],JSON.stringify(mark));
 await c.close(); await b.close(); })();
