const {chromium}=require('playwright'); const fs=require('fs'); const D=process.argv[2];
const SC=[ // уровень, доска, кто ходит первым, бросок, фразы
 ['easy','ararat',1,[6,6],{start:['Давай, кто кого!'],myDouble:['Ду-шеш! Вот это я понимаю!']}],
 ['medium','yerevan',0,[6,5],{start:['Садись, сыграем. Не торопись.'],slow:['Думай, думай, я не спешу.']}],
 ['hard','pomegranate',1,[2,1],{start:['Садись, чай остынет.'],mars:['Марс, родной. Иди чай пей.']}],
 ['expert','goldrev',1,[5,5],{start:['Нарды — это терпение.'],myDouble:['Так и было задумано.']}]];
(async()=>{ const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:956,height:440},deviceScaleFactor:2,userAgent:'Mozilla/5.0 NardyApp NardyAndroid'});
 const p=await c.newPage(); const ev=s=>p.evaluate(s=>__t.ev(s),s);
 await p.goto('http://localhost:8765/index.html?mock'); await p.evaluate(()=>{localStorage.clear();localStorage.setItem('nardy-tutorial-v1','1');localStorage.setItem('nardy-stats-v1',JSON.stringify({ach:{puz1:1,puz30:1,puz7:1}}));localStorage.setItem('nardy-settings-v1',JSON.stringify({sound:false,skin:'ararat',tod:'evening',lang:'ru',automove:false,variant:'long'}))});
 await p.reload(); await p.waitForTimeout(1500);
 for(const s of SC){ await ev(`settings.skin='${s[1]}'; buildStatic(); 0`); await p.waitForTimeout(700); }   // прогреть картинки досок
 await ev(`window.FV=null; window.FT=0;
  { const _dr=doRoll; doRoll=function(a,st,l,li,v){ return _dr(a,st,l,li,v||window.FV); };
    const _s=say; say=function(k){ return _s(k,1); };
    rollOff=function(){ busy=false; G.ro=false; G.phase='roll'; G.turn=window.FT; render(); if(G.turn===0) promptRoll(); else setStatus(opp()[0]+' ходит первым.'); }; } 0`);
 await p.addStyleTag({content:'body::after{content:"";position:fixed;left:0;top:0;width:1px;height:1px;opacity:.01;animation:tick 1s linear infinite}@keyframes tick{to{transform:translateX(1px)}}'});
 const scene=async(i)=>{ const [l,sk,ft,fv,ph]=SC[i];
   await ev(`settings.level='${l}'; settings.skin='${sk}'; saveSettings(); buildStatic(); Object.assign(PHRASES['${l}'],${JSON.stringify(ph)}); window.FT=${ft}; window.FV=${JSON.stringify(fv)}; newGame('ai'); $('bubble').classList.remove('show'); clearTimeout(say.t); if(${i}===2){ const q=G.s; q.o.fill(0); q.n.fill(0); for(const [p,c] of [[14,3],[15,2],[16,3],[17,2],[19,2],[20,3]]){q.o[p]=0;q.n[p]=c;} for(const p of [10,11]){q.o[p]=1;q.n[p]=1;} q.off=[0,13]; G.first=[false,false]; render(); } 0`); };
 const cdp=await c.newCDPSession(p); const frames=[]; let t0=null;
 cdp.on('Page.screencastFrame',async f=>{ const ts=f.metadata.timestamp; if(t0==null) t0=ts; const n=frames.length; fs.writeFileSync(`${D}/f${String(n).padStart(5,'0')}.jpg`,Buffer.from(f.data,'base64')); frames.push(ts-t0); try{ await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId}); }catch(e){} });
 await scene(0); await p.waitForTimeout(300);
 await cdp.send('Page.startScreencast',{format:'jpeg',quality:92,maxWidth:1912,maxHeight:880,everyNthFrame:1});
 const T=Date.now(), mark=[], M=n=>mark.push([n,(Date.now()-T)/1000]); const W=ms=>p.waitForTimeout(ms);
 M('s0'); await W(2700); await ev('aiTurn(); 0'); M('roll0'); await W(3800);
 await scene(1); M('s1'); await W(2500); await ev('__t.roll(); 0'); M('roll1'); await W(1700); await ev(`say('slow'); 0`); M('slow'); await W(1900);
 await scene(2); M('s2'); await W(2700); await ev('aiTurn(); 0'); M('roll2'); await W(7400);
 await scene(3); M('s3'); await W(2700); await ev('aiTurn(); 0'); M('roll3'); await W(5200); M('end');
 await cdp.send('Page.stopScreencast'); await W(300);
 fs.writeFileSync(D+'/times.json',JSON.stringify({frames,mark})); console.log(frames.length,'frames',frames[frames.length-1],JSON.stringify(mark));
 await c.close(); await b.close(); })();
