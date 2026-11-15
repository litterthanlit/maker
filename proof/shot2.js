const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for (const [w,scheme,out] of [[1400,'light',process.argv[3]],[400,'dark',process.argv[4]]]){
const p=await b.newPage({viewport:{width:w,height:900},deviceScaleFactor:1,colorScheme:scheme});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(3300);
const sw=await p.evaluate(()=>document.documentElement.scrollWidth); console.log(w,'scrollWidth',sw);
await p.screenshot({path:out,fullPage:true});}
await b.close();})();
