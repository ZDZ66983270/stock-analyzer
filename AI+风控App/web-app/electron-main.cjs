const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let backendProcess;
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 860,
        backgroundColor: '#0f172a', // Matches index.css --bg-primary
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    // In development, load from Vite server. In production, load file.
    // We can detect dev mode by checking if we are running from a script with 'electron .'
    const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

    if (isDev) {
        console.log(`Loading frontend from http://localhost:${FRONTEND_PORT}`);
        // Add a small delay or retry to ensure Vite is up? 
        // 'concurrently' and 'wait-on' in package.json will handle the initial wait.
        mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function startBackend() {
    const backendPath = path.join(__dirname, 'backend');
    console.log('Starting Python Backend from:', backendPath);

    // Using 'python3' - ensure the user has this in their PATH.
    // In a packaged app, this would be the path to the bundled executable.
    backendProcess = spawn('python3', ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', `${BACKEND_PORT}`], {
        cwd: backendPath,
        shell: true, // Helpful for finding commands in path
    });

    backendProcess.stdout.on('data', (data) => {
        console.log(`[Backend]: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend Error]: ${data}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });
}

function killBackend() {
    if (backendProcess) {
        console.log('Stopping backend...');
        // On Windows, tree-kill might be needed. On Mac, kill() usually works for spawn/shell.
        backendProcess.kill();
        backendProcess = null;
    }
}

app.whenReady().then(() => {
    startBackend();
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('will-quit', () => {
    killBackend();
});
