const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('archiveDesktop',Object.freeze({
  publish:()=>ipcRenderer.invoke('archive:publish'),
  openPublished:()=>ipcRenderer.invoke('archive:open-published')
}));
