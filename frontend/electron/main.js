import { app, BrowserWindow, shell, globalShortcut, ipcMain } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

app.commandLine.appendSwitch('no-sandbox')

let mainWindow
let spotlightWindow

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      plugins: true // Enables built-in PDF viewer for iframes
    },
    icon: path.join(__dirname, '../build/icon.png')
  })

  // In production, load the built index.html
  // In development, load the vite dev server url
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5555')
    // mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  // Open external links in default browser instead of app, EXCEPT for PDFs and internal navigation
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // If it's a local frontend route, allow it
    if (url.startsWith('file://') || url.startsWith('http://localhost:5555')) {
      return { action: 'allow' }
    }
    
    // If it's a PDF (either from our backend or arxiv), allow it to open in a new Electron window
    if (url.endsWith('.pdf') || url.includes('/api/uploads/') || url.includes('localhost:8000')) {
      return { 
        action: 'allow',
        overrideBrowserWindowOptions: {
          width: 1024,
          height: 800,
          titleBarStyle: 'default', // Normal title bar for PDF viewer
          webPreferences: {
            plugins: true // Important: enables PDF viewer in Electron
          }
        }
      }
    }

    // For all other external web pages (like github, arxiv abstract page), open in system browser
    if (url.startsWith('http')) {
      shell.openExternal(url)
      return { action: 'deny' }
    }
    
    return { action: 'allow' }
  })
}

function createSpotlightWindow() {
  spotlightWindow = new BrowserWindow({
    width: 800,
    height: 120, // Small height for input bar
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  if (process.env.NODE_ENV === 'development') {
    spotlightWindow.loadURL('http://localhost:5555/#/spotlight')
  } else {
    spotlightWindow.loadURL(`file://${path.join(__dirname, '../dist/index.html')}#/spotlight`)
  }

  spotlightWindow.on('blur', () => {
    if (!spotlightWindow.webContents.isDevToolsOpened()) {
      spotlightWindow.hide()
    }
  })
}

function toggleSpotlight() {
  if (spotlightWindow.isVisible()) {
    spotlightWindow.hide()
  } else {
    // Re-center before showing
    spotlightWindow.center()
    // Move it a bit up from center
    const bounds = spotlightWindow.getBounds()
    spotlightWindow.setBounds({
      ...bounds,
      y: Math.max(0, bounds.y - 200)
    })
    spotlightWindow.show()
    spotlightWindow.focus()
  }
}

app.whenReady().then(() => {
  createMainWindow()
  createSpotlightWindow()

  // Register global shortcut (Option+Space on Mac, Alt+Space on Windows)
  const ret = globalShortcut.register('Alt+Space', () => {
    toggleSpotlight()
  })

  if (!ret) {
    console.log('Registration of global shortcut failed')
  }

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
  })
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})

// IPC handlers for Spotlight
ipcMain.on('hide-spotlight', () => {
  if (spotlightWindow) spotlightWindow.hide()
})

ipcMain.on('refresh-main-window', (event, type) => {
  if (mainWindow) {
    mainWindow.webContents.send('refresh-data', type)
  }
})


