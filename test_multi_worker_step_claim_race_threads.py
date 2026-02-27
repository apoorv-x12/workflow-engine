import subprocess
import threading

THREADS=10

def run_worker_thread(worker_id):
    print(f"Starting worker thread: {worker_id}")
    subprocess.run(["python", "worker.py"])

threads=[]
for i in range(THREADS):
    t=threading.Thread(target=run_worker_thread, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()