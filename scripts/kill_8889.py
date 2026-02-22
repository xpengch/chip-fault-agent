import os
import signal

# 端口8889的进程
pids = [13336, 14984]

for pid in pids:
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Terminated {pid}")
    except ProcessLookupError:
        print(f"Process {pid} not found")
    except Exception as e:
        try:
            os.system(f"taskkill //F //PID {pid}")
        except:
            print(f"Failed to kill {pid}: {e}")
