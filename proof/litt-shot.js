// Screenshot the real littmd gallery with a chosen face injected through --font-choice.
// usage: node litt-shot.js <url> <out.png> <face: litt|geist|arial|none> [width] [dark]
const {chromium}=require('playwright'); const fs=require('fs');
const S=process.env.S;
(async()=>{
  const [url,out,face,width='1280',dark]=process.argv.slice(2);
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:+width,height:900},deviceScaleFactor:1,colorScheme:dark?'dark':'light'});
  await p.goto(url,{waitUntil:'networkidle'});
  const b64=f=>fs.readFileSync(S+'/'+f).toString('base64');
  const faces={litt:['Litt Grotesk','litt.woff2'],geist:['Geist','geist.woff2']};
  let css='';
  if(faces[face]){const[n,f]=faces[face];css+=`@font-face{font-family:"${n}";src:url(data:font/woff2;base64,${b64(f)}) format("woff2");font-weight:100 900}`;}
  const choice={litt:'"Litt Grotesk"',geist:'"Geist"',arial:'"Liberation Sans", Arial'}[face];
  if(choice) css+=`html,body,[data-material],[data-theme]{--font-choice:${choice}}`;
  if(css) await p.addStyleTag({content:css}); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(700);
  const fam=await p.evaluate(()=>getComputedStyle(document.querySelector('main')||document.body).fontFamily);
  console.log(face, '->', fam.slice(0,60));
  await p.screenshot({path:out}); await b.close();
})();
