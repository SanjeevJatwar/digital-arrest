const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('hud', {
  onEvent(callback) {
    ipcRenderer.on('stream:event', (_event, payload) => callback(payload));
  },
  onStatus(callback) {
    ipcRenderer.on('app:status', (_event, payload) => callback(payload));
  },
  setPointerPassthrough(enabled) {
    ipcRenderer.send('hud:pointer', enabled);
  },
  setRealCapture(enabled) {
    ipcRenderer.send('hud:capture', enabled);
  }
});