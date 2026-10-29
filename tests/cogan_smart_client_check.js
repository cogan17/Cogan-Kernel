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
  // Manager's script against a fake page; every read fails, so only cached answers show.
  const nodes=new Map(), node=id=>{
    if(!nodes.has(id)) {
      const classes=new Set();
      nodes.set(id,{textContent:'',innerHTML:'',options:[],children:[],style:{},addEventListener(){},classList:{
        add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c),
        toggle:(c,on)=>on?classes.add(c):classes.delete(c)}});
    }
    return nodes.get(id);
  };
  const cause='Pemindaian gagal pada proses berjalan (kode 42): synthetic';
  const page={ksu:{},setTimeout:()=>0,clearTimeout(){},CoganI18n:{t:s=>s,apply(){}},
    document:{getElementById:node},
    CoganUI:{create:path=>({report:async()=>{throw new Error(cause);},
        cached:()=>path.includes('/guard/') ? {at:Date.now()-120000,data:{modules:[{risk:2,trusted:false},{risk:1,trusted:false},{risk:2,trusted:true}]}}
          : path.includes('/apps/') ? {at:Date.now()-60000,data:{block:{on:1},apps:[{risk:2,trusted:0,core:0},{risk:1,trusted:1,core:0},{risk:0,trusted:0,core:1}]}} : null}),
      folds(){},kernel(){},recorder:()=>'● mencatat',
      text:(id,value)=>{node(id).textContent=value;},html:(id,value)=>{node(id).innerHTML=value;},
      action:async(button,message,task)=>task(),poll:()=>({poke(){}})}};
  page.window=page;
  vm.createContext(page);
  const html=fs.readFileSync('modules/cogan-smart/webroot/manager.html','utf8');
  vm.runInContext(html.match(/<script>\s*(const REPORT[\s\S]*?)<\/script>/)[1],page);
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
  // Everyday words are short; the full explanation stays for Mode Dev.
  assert.equal(vm.runInContext('ramShort({ram_state:"matching"})',page),'✓ Aktif sesuai pilihan.');
  assert.match(vm.runInContext('ramShort({ram_state:"blocked"})',page),/Mode Dev/);
  page.snapshot.ram_state='blocked';
  vm.runInContext('render(snapshot)',page);
  assert.match(node('ramPending').textContent,/Mode Dev/);
  assert.match(node('ramPendingDev').textContent,/Periksa hasil hook init/);
  // Manager only watches the other tabs (owner 2026-10-29): the mode is set in Power, the scan in Modules.
  page.fixture={running:1,body:405,main:612,battery:{level:80,temp:352,status:'charging',current:3000},
    config:{mode:'seimbang',TARGET_TEMP:41,GAME_LIMIT:44,SAVER_CAP:60},state:{limit:41,big:90,little:100,cause:'Prosesor'}};
  vm.runInContext('power=fixture; thermal={monitor:{}}; overview()',page);
  assert.match(node('overviewChips').innerHTML,/Badan HP<\/small><b class="warm">40.5°/);
  assert.match(node('overviewChips').innerHTML,/80% · 35.2°/);
  assert.equal(node('powerLine').textContent,'target batas CPU besar 90% · kecil 100% · Penyebab: Prosesor · mengecas 3000 mA');
  assert.equal(node('modeLine').innerHTML,'<b>🧠 Kernel Default</b> · <span class="muted">Badan HP dijaga ≤ 41 °C</span>');
  assert.equal(node('guardLine').textContent,'3 modul · 1 berbahaya · 1 perlu dicek · dipindai 2 menit lalu');
  assert.equal(node('appsLine').textContent,'3 aplikasi · 1 berbahaya · 0 perlu dicek · Blokir APK chat: aktif · dipindai 1 menit lalu');
  // Aplikasi tab: the last scan renders at once, with names from the root manager.
  const appNodes=new Map(), appNode=id=>{
    if(!appNodes.has(id)) { const classes=new Set(); appNodes.set(id,{textContent:'',innerHTML:'',style:{},disabled:/^block(On|Off)$/.test(id),addEventListener(){},
      classList:{add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c),toggle:(c,on)=>on?classes.add(c):classes.delete(c)}}); }
    return appNodes.get(id);
  };
  const scan={ok:1,user:0,scanned_at:2000000,missing:['internet'],block:{on:1,running:1,sources:['com.whatsapp'],events:[{at:1999700,p:'com.whatsapp'}]},
    apps:[{p:'id.scam',src:'chat',from:'com.whatsapp',inst:'2026-10-29 10:00:00',used:1999000,run:1,perms:['sms','a11y','hidden'],acc:{sms:125,cam:3723},net:-1,bat:12.5,risk:2,trusted:0,core:0},
      {p:'app.old',src:'store',from:'com.android.vending',inst:'2020-01-01 00:00:00',used:2000000-10*86400,run:0,perms:[],acc:{},net:2048,bat:0,risk:0,trusted:0,core:0},
      {p:'com.rifsxd.ksunext',src:'unknown',from:'',inst:'',used:0,run:0,perms:[],acc:{},net:0,bat:0,risk:0,trusted:0,core:1}]};
  // The block card waits for its own status read; a scan (cached or failed) never enables its buttons (audit 29 Oct).
  const nowS=Math.floor(Date.now()/1000);
  let blockStatus={on:1,running:1,query_ok:1,events:[{at:nowS-300,p:'com.whatsapp',ok:1}]};
  const appsSource=fs.readFileSync('modules/cogan-smart/webroot/apps.html','utf8');
  assert.match(appsSource,/id="blockOn" data-action disabled>/);
  assert.match(appsSource,/id="blockOff" data-action disabled>/);
  const appPage={ksu:{getPackagesInfo:list=>JSON.stringify(JSON.parse(list).map(p=>p==='id.scam'?{packageName:p,appLabel:'Undangan Nikah'}:{packageName:p,error:'not cached'}))},
    setTimeout:()=>0,clearTimeout(){},CoganI18n:{t:s=>s,apply(){}},localStorage:{getItem:()=>null,setItem(){}},
    document:{getElementById:appNode,querySelectorAll:()=>[]},addEventListener(){},
    CoganUI:{create:()=>({report:async args=>{ if(args==='status' && blockStatus) return {ok:1,block:blockStatus,trusted:[]}; throw new Error('offline'); },cached:()=>({at:Date.now(),data:scan}),revision:0}),
      folds(){},text:(id,value)=>{appNode(id).textContent=value;},html:(id,value)=>{appNode(id).innerHTML=value;},action:async(b,m,task)=>task()}};
  appPage.window=appPage;
  vm.createContext(appPage);
  const appsHtml=fs.readFileSync('modules/cogan-smart/webroot/apps.html','utf8');
  vm.runInContext(appsHtml.match(/<script>\s*(\/\/ Aplikasi[\s\S]*?)<\/script>/)[1],appPage);
  assert.match(appNode('summary').innerHTML,/3 aplikasi<\/b> · <span class="hot">1 berbahaya/);
  assert.match(appNode('summary').innerHTML,/Belum terbaca: internet/);
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(appNode('blockBrief').textContent,'aktif');
  assert.deepEqual([appNode('blockOn').disabled,appNode('blockOff').disabled],[true,false]);
  // A status read that fails leaves both buttons disabled, whatever an older scan said.
  blockStatus=null; appNode('blockOn').disabled=true; appNode('blockOff').disabled=true;
  vm.runInContext(appsHtml.match(/\n  (readStatus\(\)\.catch\(blockUnknown\));/)[1],appPage);
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(appNode('blockBrief').textContent,'status belum terbaca');
  assert.deepEqual([appNode('blockOn').disabled,appNode('blockOff').disabled],[true,true]);
  vm.runInContext('render(data)',appPage);
  assert.deepEqual([appNode('blockOn').disabled,appNode('blockOff').disabled],[true,true]);
  assert.match(appNode('blockInfo').textContent,/Terpasang: WhatsApp\nDicabut: WhatsApp 5 menit lalu/);
  const cards=appNode('apps').innerHTML;
  assert.match(cards,/Undangan Nikah/);
  assert.match(cards,/file APK dari WhatsApp/);
  assert.match(cards,/SMS 2 menit lalu · Kamera 1 jam lalu/);
  assert.match(cards,/Baterai sejak cas penuh: 12.5 mAh/);
  assert.match(cards,/data-act="remove" data-p="id.scam"/);
  assert(!cards.includes('app.old'), 'the risk filter hides apps without marks');
  vm.runInContext('filter="idle"; render(data)',appPage);
  assert.match(appNode('apps').innerHTML,/Terakhir dipakai: 10 hari lalu/);
  assert.match(appNode('apps').innerHTML,/Internet 7 hari: 2.0 KB/);
  vm.runInContext('filter="all"; render(data)',appPage);
  assert.match(appNode('apps').innerHTML,/Dilindungi: aplikasi root manager/);
  assert(!/data-act="remove" data-p="com.rifsxd.ksunext"/.test(appNode('apps').innerHTML));
  console.log('WebUI drafts, native callbacks and scan errors: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
