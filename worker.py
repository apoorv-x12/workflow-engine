import time
import requests
from db import SessionLocal
from models import WorkflowStep

API_BASE_URL = "http://localhost:8000"

def worker():
    while True:
        db=SessionLocal()
        try:
           
           running_step=(
                db.query(WorkflowStep)
                .filter(WorkflowStep.status=="RUNNING")
                .order_by(WorkflowStep.created_at, WorkflowStep.id)
                .first()
           )

           if not running_step:
                time.sleep(2)
                continue
           else:
               # execute the step
               time.sleep(3)  # Simulate step execution time

               # Mark the step as completed
               requests.post(f"{API_BASE_URL}/workflows/{running_step.workflow_id}/steps/{running_step.id}/complete")
               
        except Exception as e:
            print(f"Worker encountered an error: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    worker()