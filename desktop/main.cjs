const {app,BrowserWindow,ipcMain,dialog,shell}=require('electron');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const readline=require('node:readline');
const root=path.resolve(__dirname,'..');
let child,window,origin,busy=false,publishing=false;
const configPath=path.join(root,'.local','archive-client.json');
app.setName('HOTPOOR 记录');
if(!app.requestSingleInstanceLock())app.quit();
else {
 app.on('second-instance',()=>{if(window){window.show();window.focus();}});
 app.whenReady().then(async()=>{
  try {
   if(!fs.existsSync(configPath)) throw Error('尚未配置本机私密草稿目录。请先按客户端说明建立本地配置。');
   const config=JSON.parse(fs.readFileSync(configPath,'utf8'));
   const state=path.join(path.dirname(config.draft),'editor-state.json');
   const python=config.python||'python';
   const args=['-u','scripts/private-editor.py','--id',config.id,'--draft',config.draft,'--state',state,'--metadata',configPath];
   child=spawn(python,args,{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
   origin=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('本机编辑服务启动超时。')),20000);
    readline.createInterface({input:child.stdout}).on('line',line=>{
     const match=line.match(/^Local editor ready: (http:\/\/127\.0\.0\.1:\d+)$/);
     if(match){clearTimeout(timer);resolve(match[1]);}
    });
    child.once('error',()=>{clearTimeout(timer);reject(Error('无法启动本机 Python 环境。'));});
    child.once('exit',()=>{clearTimeout(timer);reject(Error('本机编辑服务已退出，请检查本地配置。'));});
   });
   window=new BrowserWindow({width:1150,height:900,minWidth:620,minHeight:650,title:'HOTPOOR 记录',backgroundColor:'#f7f5ee',
    webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true,spellcheck:false}});
   window.setMenu(null);
   window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
   window.webContents.on('will-prevent-unload',event=>{
    const choice=dialog.showMessageBoxSync(window,{type:'warning',buttons:['继续编辑','放弃未保存修改'],defaultId:0,cancelId:0,message:'有尚未加密保存的修改。'});
    if(choice===1)event.preventDefault();
   });
   window.webContents.on('will-navigate',(event,url)=>{if(url!==origin+'/')event.preventDefault();});
   const valid=event=>event.sender===window.webContents && event.senderFrame?.url===origin+'/';
   ipcMain.handle('archive:publish',async event=>{
    if(!valid(event)||publishing)throw Error('发布请求不可用。');
    publishing=true;busy=true;
    try {
     const result=await new Promise(resolve=>{
      let output='';
      const proc=spawn(python,['scripts/publish-record.py','--config',configPath,'--state',state],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
      proc.stdout.on('data',data=>{output+=data.toString('utf8');});
      proc.stderr.on('data',()=>{});
      proc.once('error',()=>resolve({ok:false,message:'本机发布程序未启动。'}));
      proc.once('close',()=>{try{resolve(JSON.parse(output.trim()));}catch{resolve({ok:false,message:'发布未完成，请检查本机配置与 Git 状态。'});}});
     });
     return result;
    }finally{publishing=false;busy=false;}
   });
   ipcMain.handle('archive:open-published',async event=>{
    if(!valid(event))return;
    await shell.openExternal('https://github.xialiwei.com/HOTPOOR-xialiwei/stories/'+encodeURIComponent(config.id)+'/');
   });
   window.on('close',event=>{
    if(busy){event.preventDefault();dialog.showMessageBox(window,{type:'info',message:'正在同步，请等待结果后再关闭。'});}
   });
   await window.loadURL(origin+'/');
  } catch(error){await dialog.showMessageBox({type:'error',title:'HOTPOOR 记录',message:error.message});app.quit();}
 });
}
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',()=>{if(child&&!child.killed)child.kill();});
