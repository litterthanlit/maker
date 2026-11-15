const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900},deviceScaleFactor:1,colorScheme:'dark'});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(3200);
const el=await p.$('section[aria-labelledby="ui-h"]');await el.screenshot({path:process.argv[3]});await b.close();})();
