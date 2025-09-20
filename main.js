const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const sizeOf = require('image-size');

let mainWindow;
let pythonProcess;

app.whenReady().then(() => {
    mainWindow = new BrowserWindow({
        width: 450,
        height: 885,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
        autoHideMenuBar: true,
        resizable: true,
    });

    mainWindow.loadFile('index.html');

    const dev = true;

    if (dev==true) {
        pythonProcess = spawn('python', ['-u', 'app.py']);
    } else {
        const backendPath = path.join(__dirname, "dist", 'app.exe');
        pythonProcess = spawn(backendPath, ['app.exe']);
    }


    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python script exited with code ${code}`);
    });

    // Handle image selection
    ipcMain.handle('select-file', async () => {
        const result = await dialog.showOpenDialog(mainWindow, {
            properties: ['openFile'],
            filters: [
                { name: 'Images', extensions: ['jpg', 'png', 'gif', 'jpeg', 'json'] },
            ],
        });


        if (!result.canceled && result.filePaths.length > 0) {
            const filePath = result.filePaths[0];
            const fileExtension = path.extname(filePath).toLowerCase().slice(1);
            if (fileExtension=="json") {
                return [fileExtension, filePath];
            }

            const dimensions = sizeOf(filePath);
            const width = dimensions.width;
            const height = dimensions.height;

            function gcd(x, y) {
                return y === 0 ? x : gcd(y, x % y);
            }

            const greatestCommonDivisor = gcd(width, height);
            const widthRatio = width / greatestCommonDivisor;
            const heightRatio = height / greatestCommonDivisor;

            mainWindow.webContents.send('update-default-resolution', [widthRatio, heightRatio]);

            return [fileExtension, filePath];
        }
        return null;
    });

    pythonProcess.stdout.on('data', (output) => {
        let pythonOutput = output.toString().trim();
        const lstPythonOutput = pythonOutput.split('\n')
        console.error(lstPythonOutput);
        for (let i = 0; i < lstPythonOutput.length; i++) {
            let pythonData = lstPythonOutput[i];
            if (pythonData.includes('imagePreview')) {
                const data = pythonData.split('_');
                let imgData = data[1]
                mainWindow.webContents.send('update-image-preview', imgData);
            } else if (pythonData.includes('bannerPreview')) {
                const data = pythonData.split('bannerPreview');
                let bannerData = data[1].split('_')
                mainWindow.webContents.send('update-banner', bannerData);
            } else if (pythonData.includes('progressBar')) {
                const data = pythonData.split(':');
                let progressBarData = data[1]
                mainWindow.webContents.send('update-progress-bar', progressBarData);
            } else if (pythonData.includes('Generated')) {
                mainWindow.webContents.send('update-on-generated');
            } else if (pythonData.includes('RemoveSteps')) {
                mainWindow.webContents.send('remove-steps');
            } else if (pythonData.includes('StepsResult')) {
                const resultData = pythonData.split('|');
                mainWindow.webContents.send('final-result', resultData);
            } else if (pythonData.includes('Steps')) {
                const stepsData = pythonData.split('_');
                mainWindow.webContents.send('create-steps', stepsData);
                mainWindow.webContents.send('update-steps', stepsData);
            }
        }
    });

    ipcMain.on('send_data', async (event, data) => {
        try {
            pythonProcess.stdin.write(JSON.stringify(data) + '\n');

            pythonProcess.stderr.on('data', (error) => {
                console.error(`Python Error: ${error.toString()}`);
            });

            pythonProcess.on('close', (code) => {
                console.log(`Python process exited with code ${code}`);
            });
        } catch (error) {
            console.error('Failed to spawn Python process:', error.message);
        }
    });

    mainWindow.loadURL('file://' + __dirname + '/index.html');

    mainWindow.webContents.on('will-navigate', (event, url) => {
        if (url.startsWith('http')) {
            event.preventDefault();
            shell.openExternal(url);
        }
    });
});

app.on('will-quit', () => {
    pythonProcess.stdin.write('{"operation": "close"}' + '\n');
});
