const {chromium}=require('playwright');
(async()=>{ const D='/tmp/claude-0/-home-user/fde68c0c-d46d-5e40-9449-283da98b11ce/scratchpad/vid';
 const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:D,size:{width:1920,height:1080}}});
 const p=await c.newPage();
 await p.goto('http://localhost:8765/index.html?mock'); await p.evaluate(()=>{localStorage.clear();localStorage.setItem('nardy-tutorial-v1','1');localStorage.setItem('nardy-settings-v1',JSON.stringify({sound:false,skin:'ararat',tod:'day',level:'medium',automove:true}))}); await p.reload();
 const t0=Date.now();
 await p.waitForTimeout(2200);
 await p.mouse.move(820,350,{steps:10}); await p.waitForTimeout(300);
 await p.click('#mAi');
 const st=()=>p.evaluate(()=>__t.st());
 // ждём своего броска
 for(let i=0;i<80;i++){ const s=await st(); if(s.phase==='roll'&&s.turn===0&&!s.busy) break; await p.waitForTimeout(150); }
 await p.waitForTimeout(400);
 const throwDrag=async()=>{ const d=await p.$('.d3.grab'); if(!d) return p.evaluate(()=>__t.roll()); const bb=await d.boundingBox();
   await p.mouse.move(bb.x+bb.width/2,bb.y+bb.height/2,{steps:6}); await p.mouse.down();
   for(let k=1;k<=14;k++){ await p.mouse.move(bb.x+bb.width/2+k*18,bb.y+bb.height/2+k*5); await p.waitForTimeout(16);} await p.mouse.up(); };
 const humanMoves=async()=>{ for(let g=0;g<6;g++){ const s=await st(); if(s.phase!=='move'||s.turn!==0||s.steps===0) break;
     if(s.busy||s.auto||s.pend){ await p.waitForTimeout(150); g--; continue; }
     const q=await p.evaluate(()=>__t.coords()); await p.mouse.move(q[0][0],q[0][1],{steps:8}); await p.mouse.down();
     for(let k=1;k<=14;k++){ await p.mouse.move(q[0][0]+(q[1][0]-q[0][0])*k/14,q[0][1]+(q[1][1]-q[0][1])*k/14); await p.waitForTimeout(20);} await p.mouse.up(); await p.waitForTimeout(700); }
   const s=await st(); if(s.phase==='move'&&s.turn===0&&s.steps===0){ await p.waitForTimeout(400); await p.evaluate(()=>__t.end()); } };
 for(let r=0;r<3;r++){
   await throwDrag(); await p.waitForTimeout(1500); await humanMoves();
   for(let i=0;i<120;i++){ const s=await st(); if(s.phase==='roll'&&s.turn===0&&!s.busy) break; await p.waitForTimeout(150); }
   await p.waitForTimeout(500);
 }
 // стакан кофе и чётки
 await p.click('#hotTea').catch(()=>{}); await p.waitForTimeout(1800);
 await c.close(); await b.close(); console.log('rec', (Date.now()-t0)/1000);
})();
