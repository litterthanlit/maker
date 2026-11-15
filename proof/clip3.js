const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900},colorScheme:process.argv[4]||'light'});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
for (const [id,out] of [['o-h',process.argv[3]+'-o.png'],['f-h',process.argv[3]+'-f.png']]) await (await p.$(`section[aria-labelledby="${id}"]`)).screenshot({path:out});
console.log(await p.evaluate(()=>document.documentElement.scrollWidth));await b.close();})();
