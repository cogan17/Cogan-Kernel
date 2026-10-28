// Shared WebUI contract: drafts survive a page change and concurrent API clients cannot
// replace one another's native callback (Manager uses three clients in one WebView).
const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
const saved = new Map(), calls = [];
const context = {
  console, setTimeout, clearTimeout, Promise, Date: class extends Date { static now() { return 1000; } },
  CoganI18n: {t:s=>s, language:()=> 'id'},
  localStorage: {getItem:k=>saved.get(k)||null, setItem:(k,v)=>saved.set(k,v), removeItem:k=>saved.delete(k)},
  ksu: {exec:(command,options,callback)=>calls.push({command,callback})}
};
context.window=context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('modules/cogan-smart/webroot/client.js','utf8'),context);
(async()=>{
  const UI=context.CoganUI;
  UI.draft.set('power','TARGET_TEMP',40);
  UI.draft.set('power','FORCE',1);
  UI.draft.set('thermal','INTERVAL',20);
  assert.equal(UI.draft.get('power').TARGET_TEMP,40);
  assert.equal(UI.draft.get('power').FORCE,1);
  UI.draft.clear('power');
  assert.equal(Object.keys(UI.draft.get('power')).length,0);
  assert.equal(UI.draft.get('thermal').INTERVAL,20);
  const a=UI.create('/power/report.sh'), b=UI.create('/thermal/report.sh');
  const pending=[a.report('status'),b.report('status')];
  await Promise.resolve();
  assert.equal(calls.length,2);
  assert.notEqual(calls[0].callback,calls[1].callback);
  for(const c of calls) context[c.callback](0,'{"ok":1,"running":1}','');
  assert.deepEqual((await Promise.all(pending)).map(x=>x.running),[1,1]);
  await assert.rejects(a.report('set x;id'),/Argumen/);
  // A failed scan clears old suggestions and leaves the cause on the page after the toast.
  const nodes=new Map(), node=id=>{
    if(!nodes.has(id)) nodes.set(id,{textContent:'',innerHTML:'',classList:{add(){},remove(){}}});
    return nodes.get(id);
  };
  const cause='Pemindaian gagal pada proses berjalan (kode 42): synthetic';
  const page={ksu:{},setTimeout:()=>0,clearTimeout(){},CoganI18n:{t:s=>s},
    document:{getElementById:node},
    CoganUI:{create:()=>({report:async()=>{throw new Error(cause);}}),folds(){},
      text:(id,value)=>{node(id).textContent=value;},html:(id,value)=>{node(id).innerHTML=value;},
      action:async(button,message,task)=>task(),poll:()=>({poke(){}})}};
  page.window=page;
  vm.createContext(page);
  const html=fs.readFileSync('modules/cogan-smart/webroot/manager.html','utf8');
  vm.runInContext(html.match(/<script>\s*(const REPORT[\s\S]*?)<\/script>/)[1],page);
  node('apps').innerHTML='old suggestions';
  await node('scanApps').onclick();
  assert.equal(node('apps').innerHTML,'');
  assert.equal(node('appsInfo').textContent,'Gagal: '+cause);
  const matching=vm.runInContext('ramMessage({ram_state:"matching"})',page);
  assert.match(matching,/bawaan sistem/);
  assert.match(vm.runInContext('ramMessage({ram_state:"blocked"})',page),/restart berulang tidak/);
  assert.match(vm.runInContext('ramMessage({ram_state:"pending_boot"})',page),/belum diterapkan/);
  assert(!html.includes('bw_hwmon + LZ4'));
  console.log('WebUI drafts, native callbacks and scan errors: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
