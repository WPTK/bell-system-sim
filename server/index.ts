import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Starting Bell System UNIX V7 Terminal Simulation...');
console.log('===============================================');

// Start the Python Bell System terminal simulation directly
const pythonProcess = spawn('python3', ['bell-system.py'], {
  cwd: path.join(__dirname, '..'),
  stdio: 'inherit'  // This allows the Python process to use the terminal directly
});

pythonProcess.on('error', (error) => {
  console.error('Failed to start Bell System terminal:', error.message);
  process.exit(1);
});

pythonProcess.on('close', (code) => {
  console.log(`Bell System terminal exited with code ${code ?? 0}`);
  process.exit(code ?? 0);
});