const { app, BrowserWindow, globalShortcut, ipcMain, session } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const WebSocket = require('ws');

let mainWindow = null;
let backendProcess = null;
let bridgeSocket = null;
let reconnectTimer = null;
let shuttingDown = false;
let clickThrough = true;
let realCaptureEnabled = process.env.DIGITAL_ARREST_ENABLE_REAL_CAPTURE === '1';
let mediaPermissionState = 'unrequested';
const bridgePort = process.env.DIGITAL_ARREST_PORT || '8765';

function sendToRenderer(channel, payload) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, payload);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    frame: false,
    transparent: true,
    resizable: true,
    hasShadow: false,
    alwaysOnTop: true,
    backgroundColor: '#05080f',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.setAlwaysOnTop(true, 'screen-saver');
  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  mainWindow.setIgnoreMouseEvents(clickThrough, { forward: true });
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  mainWindow.webContents.on('did-finish-load', () => {
    sendToRenderer('app:status', {
      type: 'window',
      state: 'ready'
    });
    broadcastCaptureState();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function setClickThrough(enabled) {
  clickThrough = enabled;

  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.setIgnoreMouseEvents(enabled, { forward: true });
    sendToRenderer('app:status', {
      type: 'overlay-pointer',
      state: enabled ? 'pass-through' : 'interactive'
    });
  }
}

function broadcastCaptureState() {
  sendToRenderer('app:status', {
    type: 'capture-mode',
    state: realCaptureEnabled ? 'real' : 'synthetic'
  });
}

function broadcastMediaPermissionState(state) {
  mediaPermissionState = state;
  sendToRenderer('app:status', {
    type: 'media-permission',
    state
  });
}

function configureMediaPermissions() {
  session.defaultSession.setPermissionCheckHandler((_webContents, permission) => {
    return permission === 'camera' || permission === 'microphone';
  });

  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    const allowed = permission === 'camera' || permission === 'microphone';
    if (allowed) {
      broadcastMediaPermissionState('granted');
    }

    callback(allowed);
  });
}

function toggleClickThrough() {
  setClickThrough(!clickThrough);
}

function connectBridge() {
  if (shuttingDown || bridgeSocket) {
    return;
  }

  bridgeSocket = new WebSocket(`ws://127.0.0.1:${bridgePort}/ws`);

  bridgeSocket.on('open', () => {
    sendToRenderer('app:status', {
      type: 'bridge',
      state: 'connected'
    });
  });

  bridgeSocket.on('message', (raw) => {
    const text = raw.toString();

    try {
      sendToRenderer('stream:event', JSON.parse(text));
    } catch {
      sendToRenderer('stream:event', {
        type: 'log',
        message: text
      });
    }
  });

  bridgeSocket.on('close', () => {
    bridgeSocket = null;
    sendToRenderer('app:status', {
      type: 'bridge',
      state: 'disconnected'
    });

    if (!shuttingDown) {
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectBridge, 1000);
    }
  });

  bridgeSocket.on('error', () => {
    // Reconnect is handled by the close event.
  });
}

function startBackend() {
  const pythonExecutable = process.env.PYTHON_EXECUTABLE || process.env.PYTHON || 'python';
  const scriptPath = path.join(__dirname, '..', 'python', 'main.py');

  backendProcess = spawn(pythonExecutable, [scriptPath], {
    cwd: path.join(__dirname, '..', 'python'),
    env: {
      ...process.env,
      DIGITAL_ARREST_ENABLE_REAL_CAPTURE: realCaptureEnabled ? '1' : '0',
      PYTHONUNBUFFERED: '1'
    },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  backendProcess.stdout.setEncoding('utf8');
  backendProcess.stdout.on('data', (chunk) => {
    const lines = chunk.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);

    for (const line of lines) {
      if (line === 'BACKEND_READY') {
        connectBridge();
      } else {
        sendToRenderer('app:status', {
          type: 'backend-log',
          message: line
        });
      }
    }
  });

  backendProcess.stderr.setEncoding('utf8');
  backendProcess.stderr.on('data', (chunk) => {
    sendToRenderer('app:status', {
      type: 'backend-error',
      message: chunk.toString().trim()
    });
  });

  backendProcess.on('exit', (code) => {
    sendToRenderer('app:status', {
      type: 'backend-exit',
      code
    });
  });
}

function restartBackendWithCapture(enabled) {
  realCaptureEnabled = enabled;
  broadcastCaptureState();

  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }

  if (bridgeSocket) {
    bridgeSocket.close();
    bridgeSocket = null;
  }

  clearTimeout(reconnectTimer);
  startBackend();
}

ipcMain.on('hud:pointer', (_event, enabled) => {
  setClickThrough(!enabled);
});

ipcMain.on('hud:capture', (_event, enabled) => {
  restartBackendWithCapture(Boolean(enabled));
});

app.whenReady().then(() => {
  configureMediaPermissions();
  createWindow();
  globalShortcut.register('CommandOrControl+Shift+H', toggleClickThrough);
  broadcastCaptureState();
  broadcastMediaPermissionState(mediaPermissionState);
  startBackend();
});

app.on('before-quit', () => {
  shuttingDown = true;
  clearTimeout(reconnectTimer);
  globalShortcut.unregisterAll();

  if (bridgeSocket) {
    bridgeSocket.close();
    bridgeSocket = null;
  }

  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});

app.on('window-all-closed', () => {
  app.quit();
});