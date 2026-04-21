// Clean port script for Windows (PowerShell compatible)
// Kills processes on ports 3000-3002

const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function killPort(port) {
  try {
    // Windows command to find and kill process on port
    const { stdout } = await execPromise(`netstat -ano | findstr :${port}`);
    const lines = stdout.trim().split('\n');
    
    const pids = new Set();
    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      if (parts.length >= 5) {
        const pid = parts[parts.length - 1];
        if (pid && !isNaN(pid)) {
          pids.add(pid);
        }
      }
    }

    for (const pid of pids) {
      try {
        await execPromise(`taskkill /F /PID ${pid}`);
        console.log(`Killed process ${pid} on port ${port}`);
      } catch (err) {
        // Process might already be dead
      }
    }
  } catch (err) {
    // No process found on port, that's fine
  }
}

async function cleanPorts() {
  console.log('Cleaning ports 3000-3002...');
  await Promise.all([
    killPort(3000),
    killPort(3001),
    killPort(3002),
  ]);
  console.log('Port cleanup complete');
}

cleanPorts().catch(console.error);

