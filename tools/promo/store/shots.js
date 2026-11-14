// Сырые кадры для скриншотов магазинов (RuStore, App Store): node shots.js <папка> <iphone|ipad|rustore>
// Игра на http://localhost:8765 (?mock). Кадры: <папка>/<сцена>.png в точном размере устройства.
const {chromium}=require('playwright'); const D=process.argv[2], DEV=process.argv[3]||'iphone';
const LANG=process.env.LANG_UI||'ru';   // язык интерфейса: ru | en
const VP={iphone:[956,440,3],ipad:[1376,1032,2],rustore:[960,540,2]}[DEV];
// позиция середины партии: обе стороны играют «лучший ход» n ходов (детерминированные кубики)
const MID=n=>`{ let r=7; const rnd=()=>(r=(r*16807)%2147483647)%6+1;
  for(let t=0;t<${n};t++){ const pl=t%2, a=rnd(), b=rnd(); const rem=a===b?[a,a,a,a]:[a,b];
    const e=bestEnd({s:G.s,pl,rem,headUsed:0,headLimit:t<2&&a===b&&(a===6||a===4||a===3)?2:1}); if(e) G.s=e.s; }
  G.turn=0; G.phase='roll'; G.rem=[]; G.first=[false,false]; render(); } 0`;
const SC=[
  {id:'1-menu', set:{skin:'ararat',tod:'evening'}, menu:true},
  {id:'2-board', set:{skin:'ararat',tod:'day',level:'medium'}, mid:14, roll:[6,3], say:{ru:'Садись, сыграем. Не торопись.',en:"Sit down, let's play. Take your time."}},
  {id:'3-gravura', set:{skin:'gravura',tod:'evening',level:'judge'}, mid:10, roll:[5,2], say:{ru:'Играем честно. Бросай.',en:'We play fair. Roll.'}},
  {id:'4-short', set:{skin:'sevan',tod:'night',level:'hard',variant:'short'}, mid:12, roll:[4,4], say:{ru:'Сначала чай, потом марс.',en:'Tea first, then a mars.'}},
  {id:'5-puzzle', set:{skin:'pomegranate',tod:'day'}, puzzle:true},
  {id:'6-mars', set:{skin:'winter',tod:'evening',level:'expert'}, mars:true},
];
(async()=>{ const b=await chromium.launch();
 for(const sc of SC){
  const c=await b.newContext({viewport:{width:VP[0],height:VP[1]},deviceScaleFactor:VP[2],userAgent:'Mozilla/5.0 NardyApp NardyAndroid'}); const p=await c.newPage();
  const ev=s=>p.evaluate(s=>__t.ev(s),s);
  await p.goto('http://localhost:8765/index.html?mock');
  await p.evaluate(([s,L])=>{ localStorage.clear(); localStorage.setItem('nardy-tutorial-v1','1'); localStorage.setItem('nardy-tutorial-short-v1','1');
    localStorage.setItem('nardy-settings-v1',JSON.stringify(Object.assign({sound:false,lang:L,automove:false,variant:'long',name:'Вы'},s))); },[sc.set,LANG]);
  await p.reload(); await p.waitForTimeout(2500);
  if(sc.menu){ await p.screenshot({path:`${D}/${sc.id}.png`}); await c.close(); continue; }
  if(sc.puzzle){ await ev('startPuzzle(); 0'); await p.waitForTimeout(3500); await p.screenshot({path:`${D}/${sc.id}.png`}); await c.close(); continue; }
  await ev("rollOff=function(){ busy=false; G.ro=false; G.phase='roll'; G.turn=0; render(); }; 0");   // без розыгрыша первого хода
  await p.click('#mAi'); await p.waitForTimeout(3000);
  if(sc.mid) await ev(MID(sc.mid));
  if(sc.mars){ await ev(`{ G.s.off[0]=15; G.s.off[1]=0; for(let i=0;i<24;i++) if(G.s.o[i]===0) G.s.n[i]=0; render(); gameOver(0); } 0`); await p.waitForFunction(()=>{ const m=document.querySelector('.mStamp .mx'); return m&&m.textContent==='×2'; }); await p.waitForTimeout(450); }
  if(sc.roll){ await ev(`{ const _dr=doRoll; doRoll=function(a,st,l,li,v){ return _dr(a,st,l,li,v||[${sc.roll}]); }; __t.roll(); } 0`); await p.waitForTimeout(2600);
    await ev(`{ const st=G.steps[0]; if(st){ G.sel=st.src; G.targets=null; render(); } } 0`); await p.waitForTimeout(400); }
  if(sc.say){ await ev(`{ const k=Object.keys(PHRASES[G.level||settings.level]||{})[0]; PHRASES[G.level||settings.level].start=[${JSON.stringify(sc.say[LANG])}]; say('start',1); } 0`); await p.waitForTimeout(700); }
  await p.screenshot({path:`${D}/${sc.id}.png`}); await c.close();
 }
 await b.close(); console.log('ok',DEV); })();
