import time
import requests
from db import SessionLocal
from sqlalchemy import func, update
from models import WorkflowStep
from worker_executer import execute_step

API_BASE_URL = "http://localhost:8000"
claim_timeout= '15 seconds'  # Define a timeout for claiming steps
REQUEST_TIMEOUT=10

def worker():
    while True:
        db=SessionLocal()
        try:
           
            running_step=(
                 db.query(WorkflowStep)
                 .filter(WorkflowStep.status=="RUNNING",
                        (WorkflowStep.claimed_by == None) | (WorkflowStep.claimed_by < func.datetime('now',f'-{claim_timeout}')))  # Only fetch steps that are not claimed by any worker or claimed more than 5 minutes ago
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
                .where(WorkflowStep.id == running_step.id, (WorkflowStep.claimed_by == None) | (WorkflowStep.claimed_by < func.datetime('now',f'-{claim_timeout}')))  # Ensure we only claim if it's still unclaimed or claimed more than 5 minutes ago
                .values(claimed_by=func.now())
            )
            result=db.execute(claimed_running_step)
            print(f"Worker tried to claim step: {running_step.id if running_step else 'None'}. Rows affected: {result.rowcount}")

            if result.rowcount == 0:
                print(f"Worker failed to claim step: {running_step.id}. It may have been claimed by another worker.")
                db.rollback()
                continue

            print(f"Worker claimed step: {running_step.id if running_step else 'None'}")
            db.commit()
            
            # Refetch step as DB is the source of truth as u will use step data
            step=(
                db.query(WorkflowStep)
                .filter(WorkflowStep.id==running_step.id)
                .first()
            )

            # execute the step
            try:
                result=execute_step(step) 
            except Exception as e:
                result="RETRY"    
            # Mark the step as completed
            if result=='SUCCESS':
                requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/complete",timeout=REQUEST_TIMEOUT)
            elif result=='FAIL':
                requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail",timeout=REQUEST_TIMEOUT)
            elif result=='RETRY':
                step.retry_count+=1
                if step.retry_count>step.max_retries:
                    requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail",timeout=REQUEST_TIMEOUT)
                else:
                    step.claimed_by=None  # Reset claimed_by to allow other workers to quickly pick it up for retry
                    db.commit()  # Update retry count in DB so that worker can retry the step
            print(f"Worker tried processing step: {step.id} with result: {result}")

            # For testing, we can fail step number 2 to see the workflow failure handling
            ''' 
            if running_step.step_number==2:
               requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail")
            else:
               requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/complete") 
            '''
              
        except Exception as e:
            print(f"Worker encountered an error: {e}")
            db.rollback()
    
        finally:
            db.close()

if __name__ == "__main__":
    worker()