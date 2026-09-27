import {decryptRecord} from './private-crypto.mjs';
const panel=document.querySelector('[data-private-record]');
if (panel) {
  const form=panel.querySelector('form'), input=panel.querySelector('input'), button=form.querySelector('button');
  const status=panel.querySelector('[role=status]'), content=panel.querySelector('[data-private-content]'), lock=panel.querySelector('[data-lock]');
  let generation=0;
  function clear() { generation++; input.value=''; content.replaceChildren(); content.hidden=true; lock.hidden=true; status.textContent='正文已锁定。'; }
  function display(text) {
    const fragment=document.createDocumentFragment();
    for (const block of text.split(/\n\s*\n/)) {
      const heading=block.match(/^(#{1,3}) (.+)$/);
      const element=document.createElement(heading?'h'+Math.min(heading[1].length+1,4):'p');
      element.textContent=heading?heading[2]:block;
      fragment.append(element);
    }
    content.replaceChildren(fragment); content.hidden=false; lock.hidden=false;
  }
  // Capture the entered key before clearing the form; never persist or send it.
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    const attempt=++generation;
    let secret=input.value; input.value=''; button.disabled=true;
    content.replaceChildren();content.hidden=true;lock.hidden=true;
    status.textContent='正在本机解密…';
    try {
      if (!crypto?.subtle) throw Error('Secure context required');
      const response=await fetch(panel.dataset.envelope,{credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer'});
      if (!response.ok) throw Error('Record unavailable');
      const text=await decryptRecord(await response.json(),secret,panel.dataset.privateRecord);
      if (attempt!==generation) return;
      display(text);status.textContent='已在当前页面解密。离开页面后会重新锁定。';
    } catch {
      if (attempt===generation) status.textContent='未能解密。请核对口令、网络连接及页面地址。';
    } finally { secret='';button.disabled=false; }
  });
  lock.addEventListener('click',clear);
  window.addEventListener('pagehide',clear);
}
