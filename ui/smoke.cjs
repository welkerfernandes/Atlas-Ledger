const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const project='atlas-ledger';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8000/',{waitUntil:'networkidle'});
  if(['atlas-ledger','evidence-hub','signal-ops'].includes(project)){
   const count=project==='atlas-ledger'?3:project==='evidence-hub'?2:1;
   for(let i=0;i<count;i++){
    await page.selectOption('#operation',String(i));
    const [response]=await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'),page.click('#send')]);
    assert.ok(response.ok(),await response.text());
   }
   if(project==='signal-ops')assert.ok((await page.locator('#result').textContent()).includes('rollback'));
  }else{
   await page.click('#run');
   await page.waitForFunction(()=>!document.querySelector('#run').disabled,{},{timeout:30000});
   assert.equal(await page.locator('[role="alert"]:visible').count(),0);
   if(project==='agent-mesh')assert.equal(await page.locator('#status').textContent(),'completed');
   else{
    assert.ok(await page.locator('tbody tr').count()>0);
    assert.equal(await page.locator('.history-item').count(),1);
    await page.locator('#key').fill('local-beta');
    await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/history')),page.getByRole('button',{name:'Atualizar',exact:true}).click()]);
    assert.equal(await page.locator('.history-item').count(),0);
    await page.locator('#key').fill('local-alpha');
    await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/history')),page.getByRole('button',{name:'Atualizar',exact:true}).click()]);
    await page.getByRole('button',{name:'Abrir',exact:true}).click();
   }
  }
  assert.deepEqual(errors,[]);
  fs.mkdirSync(path.resolve('docs'),{recursive:true});
  await page.screenshot({path:'docs/dashboard.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(100);
  const size=await page.evaluate(()=>({body:document.documentElement.scrollWidth,viewport:innerWidth}));
  assert.ok(size.body<=size.viewport+1,'Mobile page overflow '+JSON.stringify(size));
  await page.screenshot({path:'docs/mobile.png',fullPage:true});
  console.log(JSON.stringify({project,desktop:'passed',mobile:'passed',javascriptErrors:errors.length}));
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
