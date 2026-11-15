const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1400,height:900},deviceScaleFactor:1});
const [file,out,w]=process.argv.slice(2);
await p.goto('file://'+file+(w?'?w='+w:''));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
await p.screenshot({path:out,fullPage:true});await b.close();})();
