import {encryptRecord,decryptRecord} from '/crypto.mjs';
const $=id=>document.getElementById(id),form=$('editor');
let token='',recordId='',busy=false,generation=0,dirty=false,readonly=false,hasEncrypted=false,records=[];
const passwordControls=['password','confirm'].map(id=>{
 const input=$(id),toggle=document.querySelector(`[data-password-toggle="${id}"]`),count=$(id+'-count');
 const update=()=>{count.textContent=`已输入 ${Array.from(input.value).length} 个字符`;};
 const hide=()=>{input.type='password';toggle.setAttribute('aria-pressed','false');toggle.setAttribute('aria-label','显示口令');toggle.title='显示口令';};
 input.addEventListener('input',update);
 toggle.addEventListener('click',()=>{const show=input.type==='password';const start=input.selectionStart,end=input.selectionEnd;input.type=show?'text':'password';toggle.setAttribute('aria-pressed',String(show));toggle.setAttribute('aria-label',show?'隐藏口令':'显示口令');toggle.title=show?'隐藏口令':'显示口令';input.focus();input.setSelectionRange(start,end);});
 return {reset(){input.value='';hide();update();},hide};
});
function clearPasswords(){passwordControls.forEach(control=>control.reset());}
window.addEventListener('blur',()=>passwordControls.forEach(control=>control.hide()));

function setBusy(value){busy=value;for(const id of ['body','title','summary','password','confirm'])$(id).readOnly=value||readonly;for(const id of ['save','load-encrypted','clear'])$(id).disabled=value||(readonly&&id!=='clear');$('publish').disabled=value||readonly||!hasEncrypted;$('new-record').disabled=value;}
function clear(){generation++;dirty=false;$('body').value='';clearPasswords();}
for(const id of ['body','title','summary']) $(id).addEventListener('input',()=>{dirty=true;});
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
async function api(route,body){const r=await fetch(route,{method:body?'POST':'GET',headers:{'X-Editor-Token':token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store',credentials:'same-origin'});if(!r.ok)throw Error('本地服务请求失败');return r.json();}
function applyDocument(doc){
 clear();recordId=doc.id;readonly=doc.readonly;hasEncrypted=doc.has_encrypted;
 $('title').value=doc.metadata.title;$('summary').value=doc.metadata.summary;$('body').value=doc.text;
 $('status').textContent=readonly?'公开文章预览。此处以只读方式显示。':hasEncrypted?'已有密文，输入口令后可解密编辑。':'本地草稿已载入，可编辑后加密保存。';
 $('publish-status').textContent='';setBusy(busy);renderList();
}
function renderList(){
 const query=$('document-search').value.toLocaleLowerCase(),list=$('document-list');list.replaceChildren();
 const visible=records.filter(record=>record.title.toLocaleLowerCase().includes(query));
 $('document-count').textContent=`${visible.length} 篇文档`;
 for(const record of visible){const button=document.createElement('button');button.type='button';button.className='document-item';button.setAttribute('aria-current',String(record.id===recordId));button.textContent=record.title;const detail=document.createElement('small');detail.textContent=record.date+' · '+record.status;button.append(detail);button.addEventListener('click',()=>switchDocument(record.id));list.append(button);}
}
async function refreshList(){records=(await api('/records')).records;renderList();}
async function switchDocument(id){
 if(busy||id===recordId)return;
 if(dirty){$('status').textContent='请先加密保存当前修改，再切换文档。也可点击“清空屏幕”放弃修改。';return;}
 setBusy(true);
 try{applyDocument(await api('/select',{id}));}catch{$('status').textContent='未能打开文档，请稍后重试。';}finally{setBusy(false);}
}
$('document-search').addEventListener('input',renderList);
$('new-record').addEventListener('click',async()=>{
 if(busy)return;if(dirty){$('status').textContent='请先加密保存当前修改，再新建记录。';return;}
 setBusy(true);try{applyDocument(await api('/new',{}));await refreshList();$('title').focus();}catch{$('status').textContent='新建失败，请检查本机目录。';}finally{setBusy(false);}
});
try{const init=await fetch('/session',{cache:'no-store'}).then(r=>r.json());token=init.token;applyDocument(await api('/draft'));await refreshList();if(window.archiveDesktop){$('publish-panel').hidden=false;}}catch{$('status').textContent='无法载入本地草稿，请确认本机编辑服务仍在运行。';$('save').disabled=true;}
if(window.archiveDesktop?.settings){
 $('settings-panel').hidden=false;
 try{const settings=await window.archiveDesktop.settings();$('token-path').value=settings.tokenPath;$('settings-status').textContent=settings.exists?'已找到凭证文件。':'未找到凭证文件，请选择或修改位置。';}catch{$('settings-status').textContent='设置入口需要重新打开客户端后使用。';}
 $('choose-token').addEventListener('click',async()=>{if(busy)return;try{const file=await window.archiveDesktop.chooseToken();if(file){$('token-path').value=file;$('settings-status').textContent='已选择，请点击保存位置。';}}catch{$('settings-status').textContent='未能选择文件。';}});
 $('save-token-path').addEventListener('click',async()=>{if(busy)return;try{const result=await window.archiveDesktop.saveTokenPath($('token-path').value);$('settings-status').textContent=result.message;if(result.ok)$('token-path').value=result.tokenPath;}catch{$('settings-status').textContent='位置未保存，请检查文件路径。';}});
}
form.addEventListener('submit',async e=>{e.preventDefault();if(busy||readonly)return;
 if($('password').value!==$('confirm').value){$('status').textContent='两次口令不同，请重新确认。';return;}
 if(!$('body').value.trim()){ $('status').textContent='请先填写正文。';return; }
 setBusy(true);const attempt=++generation;
 let password=$('password').value,text=$('body').value;
 $('status').textContent='正在本机加密并核对…';
 try{const envelope=await encryptRecord(text,password,recordId);if(await decryptRecord(envelope,password,recordId)!==text)throw Error('核对失败');
  if(attempt!==generation)return;
  await api('/save',{envelope,metadata:{title:$('title').value,summary:$('summary').value}});hasEncrypted=true;clear();await refreshList();$('publish').disabled=false;$('status').textContent='密文已保存，正文和口令框已清空。可以同步到 GitHub；口令没有发送或保存。';
 }catch{$('status').textContent='未完成保存。请确认口令不少于 12 个字符、本机服务仍在运行，然后重试。';}
 finally{password='';text='';setBusy(false);}
});
$('load-encrypted').addEventListener('click',async()=>{if(busy||readonly)return;setBusy(true);let password=$('password').value;
 try{const envelope=await api('/envelope');$('body').value=await decryptRecord(envelope,password,recordId);$('status').textContent='已在本机解密，可继续编辑。';}catch{$('status').textContent='未能解密，请确认已保存过密文，并输入对应口令。';}
 finally{password='';clearPasswords();setBusy(false);}
});
$('clear').addEventListener('click',()=>{clear();$('status').textContent='屏幕已清空，本地原始草稿和已保存密文未删除。';});
window.addEventListener('pagehide',clear);
$('publish').addEventListener('click',async()=>{if(busy||!window.archiveDesktop)return;if(dirty){$('publish-status').textContent='有尚未加密保存的修改，请先保存后再同步。';return;}setBusy(true);$('publish').disabled=true;$('save').disabled=true;$('publish-status').textContent='正在核对、同步并等待网页发布…';try{const result=await window.archiveDesktop.publish(recordId);$('publish-status').textContent=result.message;}catch{$('publish-status').textContent='发布未完成。密文仍保存在本机。';}finally{setBusy(false);}});
$('open-published').addEventListener('click',()=>window.archiveDesktop?.openPublished(recordId));
