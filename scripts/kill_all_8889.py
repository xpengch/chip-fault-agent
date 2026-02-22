import os
import signal

# 进程列表
pids = [15204, 13336, 14984]

for pid in pids:
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Terminated {pid}")
    except Exception as e:
        print(f"Failed to kill {pid}: {e}")

print("Done")
