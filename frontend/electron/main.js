import { app, BrowserWindow, shell } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let mainWindow

function createWindow() {
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
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  // Open external links in default browser instead of app, EXCEPT for PDFs and internal navigation
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // If it's a local frontend route, allow it
    if (url.startsWith('file://') || url.startsWith('http://localhost:5173')) {
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

app.whenReady().then(() => {
  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})
