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
  console.log('WebUI drafts and native callbacks: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
