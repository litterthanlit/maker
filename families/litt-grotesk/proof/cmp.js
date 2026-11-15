const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for (const [w,out,guides] of [[1360,process.argv[3],true],[400,process.argv[4],false]]){
const p=await b.newPage({viewport:{width:w,height:900},deviceScaleFactor:1});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
if(guides) await p.click('#t-guides');
console.log(w, await p.evaluate(()=>document.documentElement.scrollWidth));
await p.screenshot({path:out,fullPage:true});}
await b.close();})();
