// Crop the world page's first demo (the deploy card) with a given face. node litt-card.js <world> <face> <theme> <out>
const {chromium}=require('playwright'); const fs=require('fs'); const S=process.env.S;
(async()=>{
  const [world,face,theme,out]=process.argv.slice(2);
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1280,height:1400},deviceScaleFactor:2,colorScheme:theme});
  await p.goto('http://localhost:5173/'+world,{waitUntil:'networkidle'});
  const b64=f=>fs.readFileSync(S+'/'+f).toString('base64');
  const faces={litt:['Litt Grotesk','litt.woff2'],geist:['Geist','geist.woff2']};
  let css='';
  if(faces[face]){const[n,f]=faces[face];css+=`@font-face{font-family:"${n}";src:url(data:font/woff2;base64,${b64(f)}) format("woff2");font-weight:100 900}`;}
  const choice={litt:'"Litt Grotesk"',geist:'"Geist"',arial:'"Liberation Sans", Arial'}[face];
  css+=`html,body,[data-material],[data-theme]{--font-choice:${choice}}`;
  await p.addStyleTag({content:css}); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(600);
  // the smallest element holding the whole card: its name and its last button
  const box=await p.evaluate(()=>{
    const [a,z]=location.pathname.includes('flat')?[/Bakehouse Nord, Copenhagen/,/Signage/]:[/harbor-web/,/Logs/]; const all=[...document.querySelectorAll('main *')].filter(e=>a.test(e.textContent)&&z.test(e.textContent));
    const el=all.filter(e=>e.getBoundingClientRect().width<520).sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0]; const r=el.getBoundingClientRect();
    return {x:r.x-16,y:r.y-16+scrollY,width:r.width+32,height:r.height+32};
  });
  await p.screenshot({path:out,clip:box,fullPage:true}); console.log(world,face,theme,Math.round(box.width),Math.round(box.height)); await b.close();
})();
