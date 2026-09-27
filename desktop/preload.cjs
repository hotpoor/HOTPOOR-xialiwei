const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('archiveDesktop',Object.freeze({
  publish:id=>ipcRenderer.invoke('archive:publish',id),
  openPublished:id=>ipcRenderer.invoke('archive:open-published',id),
  settings:()=>ipcRenderer.invoke('archive:settings'),
  chooseToken:()=>ipcRenderer.invoke('archive:choose-token'),
  saveTokenPath:file=>ipcRenderer.invoke('archive:save-token-path',file)
}));
