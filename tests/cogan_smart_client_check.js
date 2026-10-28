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
    if(!nodes.has(id)) {
      const classes=new Set();
      nodes.set(id,{textContent:'',innerHTML:'',options:[],classList:{
        add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c),
        toggle:(c,on)=>on?classes.add(c):classes.delete(c)}});
    }
    return nodes.get(id);
  };
  const cause='Pemindaian gagal pada proses berjalan (kode 42): synthetic';
  const page={ksu:{},setTimeout:()=>0,clearTimeout(){},CoganI18n:{t:s=>s,apply(){}},
    document:{getElementById:node},
    CoganUI:{create:()=>({report:async()=>{throw new Error(cause);}}),folds(){},kernel(){},
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
  assert.match(vm.runInContext('ramMessage({ram_state:"blocked"})',page),/Periksa hasil hook init/);
  assert.match(vm.runInContext('ramMessage({ram_state:"pending_boot"})',page),/belum diterapkan/);
  assert(!html.includes('bw_hwmon + LZ4'));
  // A phone with native MediaTek DRAM gets a real readback, not an unusable dropdown.
  node('bwGovernor').options=[{value:'default'},{value:'bw_hwmon'}];
  page.snapshot={writable:1,version:'v2.10.5',config:{cpu:'default',ram:'snappy',boot:0,bw:'default'},
    cpu:[],zram:[],dram:[{driver:'mtk-dvfsrc-devfreq',current:'userspace'}],bw_hwmon:[],ram_state:'matching'};
  vm.runInContext('render(snapshot)',page);
  assert.match(node('dramInfo').textContent,/mtk-dvfsrc-devfreq: userspace/);
  assert(node('bwControls').classList.contains('hidden'));
  assert.equal(node('bwGovernor').options[1].disabled,true);
  // A previously saved, now-unavailable BW setting must remain clearable via System DRAM.
  page.snapshot.config.bw='bw_hwmon';
  vm.runInContext('render(snapshot)',page);
  assert(!node('bwControls').classList.contains('hidden'));
  assert.equal(node('bwGovernor').value,'bw_hwmon');
  node('bwGovernor').value='default';
  assert.equal(vm.runInContext('values()',page),'default snappy 0 default');
  console.log('WebUI drafts, native callbacks and scan errors: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
