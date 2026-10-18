// Records the current application, using only retained actual native run artifacts.
// Editorial overlays identify the replay and synthetic data; no model state is invented.
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve('..');
const output = path.join(root, 'artifacts/submission-film');
await mkdir(output, {recursive:true});
const script = JSON.parse(await readFile(path.join(root, 'demo/film-script.json'), 'utf8'));
const native = {};
for (const name of ['0091d790d71e40269b534463a162442d','38503689004b4d4ab6a0ffc7ad918919','4a5e8e28ae704314b702a51f8c3df7ba']) {
  const record = JSON.parse(await readFile(path.join(root, `demo/live/sequence/replays/${name}.json`), 'utf8'));
  assert.equal(record.model_provider, 'gemini');
  native[record.demonstration_phase] = record;
}
assert.equal(native.recovery.status, 'recovered');
assert.equal(native.memory.status, 'recovered');
assert.equal(native.insufficient.status, 'needs_evidence');
assert(native.memory.proposals.some(p=>p.evidence_ids.some(id=>id.startsWith('memory-'))));
const browser = await chromium.launch({headless:true, args:['--disable-gpu']});
const context = await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1, reducedMotion:'reduce',recordVideo:{dir:output,size:{width:1920,height:1080}}});
const started = performance.now();
const page = await context.newPage();
const errors = [];
page.on('pageerror',e=>errors.push(e.message));
const base = process.env.DEMO_URL || 'http://127.0.0.1:8104/';
await page.goto(base);
await page.getByText('REPLAY',{exact:true}).waitFor();
await page.evaluate(()=>document.fonts.ready);

async function results() {
  await page.getByRole('button',{name:'Evaluation results',exact:true}).click();
  await page.locator('.comparison-panel').waitFor();
}
async function open(phase) {
  await results();
  const row = page.locator(`[data-replay-id="${native[phase].id}"]`);
  await row.waitFor({timeout:60000});
  assert.equal(await row.getAttribute('data-replay-status'),native[phase].status);
  await row.click();
  await page.getByText('REPLAY',{exact:true}).waitFor();
}
async function frame(locator) {
  await locator.waitFor();
  await locator.evaluate(el=>window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-175,behavior:'instant'}));
  await page.waitForTimeout(450);
}
async function overlay(chapter, index, card=false, proof=false) {
  await page.evaluate(({chapter,index,total,card,proof})=>{
    document.querySelector('#film-editorial')?.remove();
    const el=document.createElement('div'); el.id='film-editorial';
    const style=document.createElement('style');
    style.textContent=`#film-editorial{font-family:Inter,system-ui,sans-serif;pointer-events:none;color:#effbf5;position:fixed;inset:0;z-index:99999}#film-editorial *{box-sizing:border-box}.film-top{position:absolute;top:22px;left:50%;transform:translateX(-50%);background:#09140fec;border:1px solid #ffffff1c;border-radius:50px;padding:12px 24px;letter-spacing:.12em;font-size:13px;color:#9ef0d0;box-shadow:0 10px 40px #0005}.film-caption{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(0deg,#070f0dfc 55%,#070f0de8 85%,transparent);padding:58px 100px 32px}.film-kicker{font-size:13px;color:#65e9bf;letter-spacing:.16em;font-weight:650;margin-bottom:10px}.film-title{font-size:30px;font-weight:650;letter-spacing:-.8px;margin-bottom:10px}.film-text{font-size:23px;line-height:1.55;color:#d5e4dc;max-width:1610px}.film-progress{position:absolute;bottom:0;left:0;height:3px;background:#2dd4a7}.film-cover{position:absolute;inset:0;background:radial-gradient(ellipse at 75% 25%,#144c39c9,transparent 55%),#07100ff5;display:flex;flex-direction:column;justify-content:center;padding:130px 190px}.film-cover .film-title{font-size:80px;line-height:1.12;letter-spacing:-3px;max-width:1350px;margin:20px 0 32px}.film-cover .film-text{font-size:28px;max-width:1190px;line-height:1.65}.film-brand{font-size:38px;letter-spacing:-2px;margin-bottom:74px;font-weight:750}.film-brand span{color:#2dd4a7}.film-links{margin-top:40px;font-size:20px;color:#88cab2;line-height:1.9}`;
    el.append(style);
    const top=document.createElement('div');top.className='film-top';top.textContent=proof?'PUBLIC EVIDENCE RECEIPTS · SYNTHETIC DATA':'ACTUAL GEMINI RUN · REPLAY · SYNTHETIC DATA';el.append(top);
    const panel=document.createElement('div');panel.className=card?'film-cover':'film-caption';
    if(card){const brand=document.createElement('div');brand.className='film-brand';brand.innerHTML='ripple<span>.</span>';panel.append(brand);}
    for(const [klass,value] of [['film-kicker',chapter.label],['film-title',chapter.title],['film-text',chapter.text]]){const child=document.createElement('div');child.className=klass;child.textContent=value;panel.append(child);}
    if(card&&index===total-1){const links=document.createElement('div');links.className='film-links';links.textContent='guruchandar360.github.io/ripple-graph-hacks/  •  /proof/\ngithub.com/Guruchandar360/ripple-graph-hacks';links.style.whiteSpace='pre-line';panel.append(links);}
    el.append(panel);const progress=document.createElement('div');progress.className='film-progress';progress.style.width=`${(index+1)/total*100}%`;el.append(progress);document.body.append(el);
  },{chapter,index,total:script.chapters.length,card,proof});
}
async function proofHeading(name) {
  await page.goto(new URL('proof/',base).href);
  await page.getByRole('heading',{name,exact:true}).waitFor();
  await frame(page.getByRole('heading',{name,exact:true}).locator('..'));
}
const timing=[];
for(const [i,chapter] of script.chapters.entries()) {
  await page.evaluate(()=>document.querySelector('#film-editorial')?.remove());
  if(chapter.id==='opening') await page.evaluate(()=>scrollTo(0,0));
  if(chapter.id==='graph'){
    await open('recovery');
    const pathEvent=native.recovery.events.find(e=>e.paths?.some(p=>p.edges.length>1));
    assert(pathEvent,'Actual connected path evidence is required');
    await page.locator(`[data-event-id="${pathEvent.id}"]`).getByRole('button',{name:'Show supporting paths'}).click();
    await page.waitForTimeout(1000); // Let the application's source-inspector scroll finish.
    await frame(page.locator('.graph-panel'));
    const graphBounds=await page.locator('.graph-panel').boundingBox();
    assert(graphBounds.y>=100 && graphBounds.y+graphBounds.height<=870,'The full graph must remain above the captions');
    assert(await page.getByText('depends on',{exact:true}).count()>0);
  }
  if(chapter.id==='old-fix') await frame(page.locator('.timeline-event').filter({hasText:'Recovery proposed'}).first());
  if(chapter.id==='changed') await frame(page.locator('.evidence-change-card'));
  if(chapter.id==='constraints'){
    await frame(page.locator('.policy-list'));
    await page.locator('.policy-list > button').first().click();
    await frame(page.locator('.inspector'));
  }
  if(chapter.id==='recovery') await frame(page.locator('.recommendation'));
  if(chapter.id==='memory'){await open('memory');await frame(page.locator('.timeline-event').filter({hasText:'Incident memory retrieved'}).first());}
  if(chapter.id==='insufficient'){await open('insufficient');await frame(page.locator('.recommendation'));}
  if(chapter.id==='hosted') await proofHeading('A hosted recovery, verified.');
  if(chapter.id==='benchmark'){await page.goto(base);await page.getByText('REPLAY',{exact:true}).waitFor();await results();await frame(page.locator('.comparison-panel'));}
  if(chapter.id==='limits') await proofHeading('One complete Gemini sequence passed.');
  await overlay(chapter,i,['opening','closing'].includes(chapter.id),['hosted','benchmark','limits','closing'].includes(chapter.id));
  const wav=await readFile(path.join(root,`artifacts/film-audio/${chapter.id}.wav`));
  // Standard PCM WAV byteRate and data chunk, emitted by Windows System.Speech.
  const byteRate=wav.readUInt32LE(28);let cursor=12,dataBytes=0;
  while(cursor+8<=wav.length){const size=wav.readUInt32LE(cursor+4);if(wav.toString('ascii',cursor,cursor+4)==='data'){dataBytes=size;break;}cursor+=8+size+(size%2);}
  assert(dataBytes>0&&byteRate>0);
  const speechSeconds=dataBytes/byteRate;
  const start=(performance.now()-started)/1000;
  timing.push({id:chapter.id,start,speech_seconds:speechSeconds,text:chapter.text});
  await page.screenshot({path:path.join(output,`${String(i).padStart(2,'0')}-${chapter.id}.png`)});
  await page.waitForTimeout((speechSeconds+1.5)*1000);
  console.log(`Captured ${chapter.id}: ${speechSeconds.toFixed(1)}s narration`);
}
const video=page.video();await context.close();await video.saveAs(path.join(output,'latest-ui.webm'));await browser.close();
assert.deepEqual(errors,[]);
await writeFile(path.join(output,'timing.json'),JSON.stringify({timing,wall_seconds:(performance.now()-started)/1000,ui_errors:errors},null,2));
console.log('Recorded current interface and exact native replays; no model calls.');
