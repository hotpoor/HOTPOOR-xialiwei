const {app,BrowserWindow,ipcMain}=require('electron');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const readline=require('node:readline');
const {decrypt}=require('./encrypt-story.cjs');
const root=path.resolve(__dirname,'..'),id='test-ui-fixture';
const target=path.join(root,'content/encrypted',id+'.json');
const text='## 私密测试标题\n\n这是一段自动化测试内容。<script>window.injected=true</script> 🌱';
const secret='Test-only-long-passphrase-2026';
let backend,server,window;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function waitFor(fn){for(let n=0;n<100;n++){if(await fn())return;await delay(100);}throw Error('UI timeout: '+fn.toString());}
app.whenReady().then(async()=>{
 try{
  assert(!fs.existsSync(target),'Synthetic output already exists');
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'hotpoor-client-test-'));
  const draft=path.join(temp,'draft.md'),metadata=path.join(temp,'metadata.json'),state=path.join(temp,'state.json');
  fs.writeFileSync(draft,text);fs.writeFileSync(metadata,JSON.stringify({title:'加密测试',summary:'仅供验证',date:'2026-09-27',chapter:'dialogue'}));
  backend=spawn(process.env.ARCHIVE_TEST_PYTHON||'python',['-u','scripts/private-editor.py','--id',id,'--draft',draft,'--state',state,'--metadata',metadata],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
  const origin=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Editor timeout')),20000);readline.createInterface({input:backend.stdout}).on('line',line=>{if(line.startsWith('Local editor ready: ')){clearTimeout(timer);resolve(line.slice(20));}});backend.on('error',reject);});
  let publishCalls=0;
  ipcMain.handle('archive:settings',()=>({tokenPath:'C:/example/github.token',exists:true}));
  ipcMain.handle('archive:choose-token',()=>null);
  ipcMain.handle('archive:save-token-path',(_event,file)=>({ok:true,tokenPath:file,message:'测试位置已保存'}));
  ipcMain.handle('archive:publish',()=>{publishCalls++;return {ok:true,message:'模拟同步完成；未连接 GitHub。'};});
  window=new BrowserWindow({show:false,width:1100,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,preload:path.join(root,'desktop/preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  let saveBody='';
  window.webContents.session.webRequest.onBeforeRequest((details,callback)=>{if(details.url===origin+'/save')saveBody=Buffer.concat((details.uploadData||[]).map(x=>x.bytes||Buffer.alloc(0))).toString();callback({});});
  await window.loadURL(origin+'/');
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#body').value.length>0"));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#body').value"),text);
  await window.webContents.executeJavaScript(`document.querySelector('#password').value=${JSON.stringify(secret)};document.querySelector('#confirm').value=${JSON.stringify(secret)};document.querySelector('#editor').requestSubmit();`);
  await waitFor(()=>fs.existsSync(target));
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#body').value===''&&!document.querySelector('#publish').disabled"));
  const envelope=JSON.parse(fs.readFileSync(target,'utf8'));
  assert.equal(decrypt(envelope,secret),text);
  assert(!saveBody.includes(secret)&&!saveBody.includes('私密测试标题'));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#publish-panel').hidden"),false);
  await window.webContents.executeJavaScript("document.querySelector('#publish').click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#publish-status').textContent.includes('模拟同步完成')"));
  assert.equal(publishCalls,1);
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#token-path').value"),'C:/example/github.token');
  assert(await window.webContents.executeJavaScript("Number(document.querySelector('#public-count').textContent)+Number(document.querySelector('#encrypted-count').textContent)>1"));
  await window.webContents.executeJavaScript("document.querySelector('#body').value='unsaved';document.querySelector('#body').dispatchEvent(new Event('input'));document.querySelector('#new-record').click()");
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#body').value"),'unsaved');
  await window.webContents.executeJavaScript("document.querySelector('#clear').click();document.querySelector('#new-record').click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#title').value==='新的记录'&&!document.querySelector('#new-record').disabled"));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#publish').disabled"),true);
  await window.webContents.executeJavaScript("Array.from(document.querySelectorAll('.document-item')).find(b=>b.textContent.includes('加密测试')).click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#title').value==='加密测试'&&!document.querySelector('#new-record').disabled"));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#body').value"),'');
  await window.webContents.executeJavaScript("document.querySelector('#tab-public').click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#password-section').hidden&&!document.querySelector('#new-record').disabled"));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#body').readOnly"),false);
  await window.webContents.executeJavaScript("document.querySelector('#new-record').click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#title').value==='新的记录'&&!document.querySelector('#new-record').disabled"));
  await window.webContents.executeJavaScript("document.querySelector('#title').value='公开测试记录';document.querySelector('#body').value='## 公开测试\\n\\n这份虚构草稿只用于测试。';document.querySelector('#body').dispatchEvent(new Event('input'));document.querySelector('#editor').requestSubmit()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#status').textContent.includes('公开草稿已保存')"));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#password').required"),false);
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('#publish').disabled"),false);
  await window.webContents.executeJavaScript("document.querySelector('#publish').click()");
  await waitFor(()=>publishCalls===2);
  await waitFor(()=>window.webContents.executeJavaScript("!document.querySelector('#new-record').disabled"));
  await window.webContents.executeJavaScript("document.querySelector('#tab-encrypted').click()");
  await waitFor(()=>window.webContents.executeJavaScript("!document.querySelector('#password-section').hidden&&!document.querySelector('#new-record').disabled"));
  await window.webContents.executeJavaScript("document.querySelector('#tab-public').click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#password-section').hidden&&!document.querySelector('#new-record').disabled"));
  await window.webContents.executeJavaScript("Array.from(document.querySelectorAll('.document-item')).find(b=>b.textContent.includes('公开测试记录')).click()");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('#title').value==='公开测试记录'&&!document.querySelector('#new-record').disabled"));
  assert(await window.webContents.executeJavaScript("document.querySelector('#body').value.includes('虚构草稿')"));
  const bad=await fetch(origin+'/save',{method:'POST',headers:{Origin:'https://evil.invalid','Content-Type':'application/json'},body:'{}'});
  assert.equal(bad.status,403);
  assert.equal((await fetch(origin+'/draft')).status,403);
  fs.mkdirSync(path.join(root,'test-results'),{recursive:true});
  window.webContents.invalidate();
  await delay(500);
  fs.writeFileSync(path.join(root,'test-results/client-editor.png'),(await window.webContents.capturePage()).toPNG());
  server=http.createServer((req,res)=>{
   if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end(`<section data-private-record="${id}" data-envelope="/cipher.json"><form><input type="password"><button>解密</button></form><p role="status"></p><button data-lock hidden>锁定</button><div data-private-content hidden></div></section><script type="module" src="/assets/private-story.mjs"></script>`);}
   else if(req.url==='/cipher.json'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(envelope));}
   else if(['/assets/private-story.mjs','/assets/private-crypto.mjs'].includes(req.url)){res.setHeader('Content-Type','text/javascript');res.end(fs.readFileSync(path.join(root,req.url)));}
   else{res.writeHead(404);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  await window.loadURL('http://127.0.0.1:'+server.address().port+'/');
  await window.webContents.executeJavaScript("document.querySelector('input').value='wrong-password';document.querySelector('form').requestSubmit();");
  await waitFor(()=>window.webContents.executeJavaScript("document.querySelector('[role=status]').textContent.includes('未能解密')"));
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('[data-private-content]').textContent"),'');
  await window.webContents.executeJavaScript(`document.querySelector('input').value=${JSON.stringify(secret)};document.querySelector('form').requestSubmit();`);
  await waitFor(()=>window.webContents.executeJavaScript("!document.querySelector('[data-private-content]').hidden"));
  assert.equal(await window.webContents.executeJavaScript('Boolean(window.injected)'),false);
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('input').value"),'');
  assert.equal(await window.webContents.executeJavaScript('localStorage.length+sessionStorage.length'),0);
  await window.webContents.executeJavaScript("document.querySelector('[data-lock]').click()");
  assert.equal(await window.webContents.executeJavaScript("document.querySelector('[data-private-content]').textContent"),'');
  console.log('Client UI: public/encrypted tabs, public draft persistence, mocked publishing, encryption, CSRF, wrong password and re-lock passed.');
 }catch(error){console.error('Client verification failed:',error.message);process.exitCode=1;}
 finally{window?.destroy();backend?.kill();server?.close();if(fs.existsSync(target))fs.unlinkSync(target);app.exit(process.exitCode||0);}
});
