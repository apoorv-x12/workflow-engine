import subprocess
import threading
import sys

THREADS=5

def run_worker_thread(worker_id):
    try:
        print(f"Starting worker process: {worker_id}")
        subprocess.run([sys.executable, "-m", "workers.worker"], check=True)
    except Exception as e:
        print(f"Error running worker process {worker_id}: {e}")

threads=[]
for i in range(THREADS):
    t=threading.Thread(target=run_worker_thread, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
