import subprocess
import multiprocessing

PROCESSES=10

def run_worker_process(worker_id):
    try:
        print(f"Starting worker process: {worker_id}")
        subprocess.run(["python", "worker.py"])
    except Exception as e:
        print(f"Error running worker process {worker_id}: {e}")

# For testing, we can run multiple worker processes to simulate
# write inside if __name__ == "__main__" to avoid issues with multiprocessing on Windows
if __name__ == "__main__":
    processes=[]
    for i in range(PROCESSES):
        p=multiprocessing.Process(target=run_worker_process, args=(i,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

