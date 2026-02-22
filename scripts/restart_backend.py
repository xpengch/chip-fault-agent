import os
import signal
import subprocess
import time

# 找到并终止占用8889端口的进程
result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if ':8889' in line and 'LISTENING' in line:
        parts = line.split()
        if len(parts) >= 5:
            pid = int(parts[-1])
            print(f"Terminating process {pid}...")
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                os.system(f"taskkill //F //PID {pid}")

time.sleep(2)

# 启动后端服务
print("Starting backend server...")
subprocess.Popen([
    'python', '-m', 'uvicorn',
    'src.api.app:app',
    '--host', '0.0.0.0',
    '--port', '8889',
    '--reload'
], cwd=r'D:\ai_dir\chip_fault_agent')

print("Backend server started on port 8889")
