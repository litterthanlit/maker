const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900},colorScheme:process.argv[4]||'light'});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
if(process.argv[5]) await p.click(process.argv[5]);
await (await p.$('section[aria-labelledby="w-h"]')).screenshot({path:process.argv[3]});await b.close();})();
