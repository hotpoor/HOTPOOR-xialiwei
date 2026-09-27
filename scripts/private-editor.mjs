import {encryptRecord,decryptRecord} from '/crypto.mjs';
const $=id=>document.getElementById(id),form=$('editor');
let token='',recordId='',busy=false,generation=0,dirty=false;
function setBusy(value){busy=value;for(const id of ['body','title','summary','password','confirm'])$(id).readOnly=value;for(const id of ['save','load-encrypted','clear'])$(id).disabled=value;}
function clear(){generation++;dirty=false;$('body').value='';$('password').value='';$('confirm').value='';}
for(const id of ['body','title','summary']) $(id).addEventListener('input',()=>{dirty=true;});
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
async function api(route,body){const r=await fetch(route,{method:body?'POST':'GET',headers:{'X-Editor-Token':token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store',credentials:'same-origin'});if(!r.ok)throw Error('本地服务请求失败');return r.json();}
try{const init=await fetch('/session',{cache:'no-store'}).then(r=>r.json());token=init.token;recordId=init.id;$('title').value=init.metadata.title;$('summary').value=init.metadata.summary;const draft=await api('/draft');$('body').value=draft.text;$('status').textContent=draft.has_encrypted?'已有密文。输入对应口令，点击“解密已保存版本”继续编辑。':'本地草稿已载入。你可以编辑，输入口令后加密保存。';if(window.archiveDesktop){$('publish-panel').hidden=false;$('publish').disabled=!draft.has_encrypted;}}catch{$('status').textContent='无法载入本地草稿，请确认本机编辑服务仍在运行。';$('save').disabled=true;}
form.addEventListener('submit',async e=>{e.preventDefault();if(busy)return;
 if($('password').value!==$('confirm').value){$('status').textContent='两次口令不同，请重新确认。';return;}
 if(!$('body').value.trim()){ $('status').textContent='请先填写正文。';return; }
 setBusy(true);const attempt=++generation;
 let password=$('password').value,text=$('body').value;
 $('status').textContent='正在本机加密并核对…';
 try{const envelope=await encryptRecord(text,password,recordId);if(await decryptRecord(envelope,password,recordId)!==text)throw Error('核对失败');
  if(attempt!==generation)return;
  await api('/save',{envelope,metadata:{title:$('title').value,summary:$('summary').value}});clear();$('publish').disabled=false;$('status').textContent='密文已保存，正文和口令框已清空。可以同步到 GitHub；口令没有发送或保存。';
 }catch{$('status').textContent='未完成保存。请确认口令不少于 12 个字符、本机服务仍在运行，然后重试。';}
 finally{password='';text='';setBusy(false);}
});
$('load-encrypted').addEventListener('click',async()=>{if(busy)return;setBusy(true);let password=$('password').value;
 try{const envelope=await api('/envelope');$('body').value=await decryptRecord(envelope,password,recordId);$('status').textContent='已在本机解密，可继续编辑。';}catch{$('status').textContent='未能解密，请确认已保存过密文，并输入对应口令。';}
 finally{password='';$('password').value='';$('confirm').value='';setBusy(false);}
});
$('clear').addEventListener('click',()=>{clear();$('status').textContent='屏幕已清空，本地原始草稿和已保存密文未删除。';});
window.addEventListener('pagehide',clear);
$('publish').addEventListener('click',async()=>{if(busy||!window.archiveDesktop)return;if(dirty){$('publish-status').textContent='有尚未加密保存的修改，请先保存后再同步。';return;}setBusy(true);$('publish').disabled=true;$('save').disabled=true;$('publish-status').textContent='正在核对、同步并等待网页发布…';try{const result=await window.archiveDesktop.publish();$('publish-status').textContent=result.message;}catch{$('publish-status').textContent='发布未完成。密文仍保存在本机。';}finally{setBusy(false);$('publish').disabled=false;}});
$('open-published').addEventListener('click',()=>window.archiveDesktop?.openPublished());
