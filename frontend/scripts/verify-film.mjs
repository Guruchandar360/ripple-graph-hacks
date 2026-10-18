// Decode the delivered MP4 in a real Chromium media element; never call a model.
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root=path.resolve('..');
const expected=JSON.parse(await readFile(path.join(root,'demo/video.json'),'utf8'));
const media=process.env.FILM_URL || 'http://127.0.0.1:8104/showcase/ripple-demo.mp4';
const browser=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required','--disable-gpu']});
const page=await browser.newPage({viewport:{width:1920,height:1080}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const responses=[];
page.on('response',r=>{if(r.url().includes('.mp4'))responses.push({status:r.status(),range:r.headers()['content-range']??null});});
await page.goto(media,{waitUntil:'domcontentloaded'});
const video=page.locator('video');
await video.waitFor();
await page.waitForFunction(()=>document.querySelector('video')?.readyState>=2,{timeout:60000});
const dimensions=await video.evaluate(el=>({width:el.videoWidth,height:el.videoHeight,duration:el.duration}));
assert.equal(dimensions.width,1920);assert.equal(dimensions.height,1080);
assert(Math.abs(dimensions.duration-expected.duration_seconds)<.2);
await video.evaluate(el=>{el.muted=false;return el.play();});
await page.waitForFunction(()=>{const el=document.querySelector('video');return el&&el.currentTime>1&&el.webkitVideoDecodedByteCount>0;},null,{timeout:60000});
const playback=await video.evaluate(el=>({time:el.currentTime,videoBytes:el.webkitVideoDecodedByteCount,audioBytes:el.webkitAudioDecodedByteCount,error:el.error?.message??null}));
assert(playback.time>1 && playback.videoBytes>0);
assert.equal(playback.audioBytes,0,'The submission video must contain no decoded audio');
assert.equal(playback.error,null);
await video.evaluate(el=>{el.pause();el.currentTime=20;});
try {
  await page.waitForFunction(()=>{const el=document.querySelector('video');return el&&!el.seeking&&el.readyState>=2&&Math.abs(el.currentTime-20)<.2;},null,{timeout:60000});
} catch(error) {
  console.log(JSON.stringify({responses,mediaState:await video.evaluate(el=>({time:el.currentTime,seeking:el.seeking,readyState:el.readyState,error:el.error?.message,buffered:Array.from({length:el.buffered.length},(_,i)=>[el.buffered.start(i),el.buffered.end(i)]),seekable:Array.from({length:el.seekable.length},(_,i)=>[el.seekable.start(i),el.seekable.end(i)])}))}));
  await page.screenshot({path:path.join(root,'artifacts/submission-film/playback-diagnostic.png')});
  await browser.close();
  throw error;
}
await page.waitForTimeout(350); // Allow the decoded seek frame to paint.
await page.screenshot({path:path.join(root,'artifacts/submission-film/browser-playback.png')});
assert.deepEqual(errors,[]);
await writeFile(path.join(root,'artifacts/submission-film/browser-check.json'),JSON.stringify({passed:true,media,...dimensions,playback,sha256:expected.sha256,scope:'Actual Chromium video playback, no decoded audio; selected captioned frame visually inspected.'},null,2));
await browser.close();
console.log(`Chromium played silent captioned ${dimensions.width}x${dimensions.height} MP4; duration ${dimensions.duration}s.`);
