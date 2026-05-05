const { app, BrowserWindow, session } = require('electron');
const path = require('path');

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    title: 'CodeOptimizer',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      // Allow fetch calls to localhost FastAPI backend
      webSecurity: false,
    }
  });

  // Remove default menu bar
  win.setMenuBarVisibility(false);

  win.loadFile(path.join(__dirname, 'index.html'));

  win.on('closed', () => { win = null; });
}

app.on('ready', () => {
  // Allow loading CDN resources (marked.js, highlight.js) inside Electron
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com http://localhost:8000; connect-src 'self' http://localhost:8000"
        ]
      }
    });
  });

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (win === null) createWindow();
});
