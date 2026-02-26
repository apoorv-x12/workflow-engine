import time
import requests
from db import SessionLocal
from sqlalchemy import func, update
from models import WorkflowStep

API_BASE_URL = "http://localhost:8000"

def worker():
    while True:
        db=SessionLocal()
        try:
           
            running_step=(
                 db.query(WorkflowStep)
                 .filter(WorkflowStep.status=="RUNNING", WorkflowStep.claimed_by==None)  # Only fetch steps that are not claimed by any worker
                 .order_by(WorkflowStep.created_at, WorkflowStep.id)
                 .first()
            )
            print(f"Worker fetched step: {running_step.id if running_step else 'None'} with status: {running_step.status if running_step else 'N/A'}")
 
            if not running_step:
                 print("No running steps found. Worker is idle.")
                 time.sleep(2)
                 continue
            
            # Claim the step by setting the claimed_by timestamp
            claimed_running_step = (
                update(WorkflowStep)
                .where(WorkflowStep.id == running_step.id, WorkflowStep.claimed_by == None)  # Ensure we only claim if it's still unclaimed
                .values(claimed_by=func.now())
            )
            result=db.execute(claimed_running_step)
            print(f"Worker claimed step: {running_step.id if running_step else 'None'}. Rows affected: {result.rowcount}")

            if result.rowcount == 0:
                print(f"Worker failed to claim step: {running_step.id}. It may have been claimed by another worker.")
                db.rollback()
                continue
            db.commit()

            # execute the step
            time.sleep(3)  # Simulate step execution tim        
            # Mark the step as completed
            requests.post(f"{API_BASE_URL}/workflows/{running_step.workflow_id}/steps/{running_step.id}/complete")
            print(f"Worker completed step: {running_step.id}")
            
            # For testing, we can fail step number 2 to see the workflow failure handling
            ''' 
            if running_step.step_number==2:
               requests.post(f"{API_BASE_URL}/workflows/{running_step.workflow_id}/steps/{running_step.id}/fail")
            else:
               requests.post(f"{API_BASE_URL}/workflows/{running_step.workflow_id}/steps/{running_step.id}/complete") 
            '''
              
        except Exception as e:
            print(f"Worker encountered an error: {e}")
            db.rollback()
            raise
        finally:
            db.close()

if __name__ == "__main__":
    worker()