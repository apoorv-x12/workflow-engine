import time
import requests
from db import SessionLocal
from sqlalchemy import func, update
from models import WorkflowStep
from worker_executer import execute_step
import os
from basic_logging import get_logger

logger=get_logger(__name__)

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

            logger.info(f"Worker fetched step: {running_step.id if running_step else 'None'} with status: {running_step.status if running_step else 'N/A'}")
 
            if not running_step:
                 logger.error("No running steps found. Worker is idle.")
                 time.sleep(2)
                 continue
            
            # Claim the step by setting the claimed_by timestamp
            claimed_running_step = (
                update(WorkflowStep)
                .where(WorkflowStep.id == running_step.id, (WorkflowStep.claimed_by == None) | (WorkflowStep.claimed_by < func.datetime('now',f'-{claim_timeout}')))  # Ensure we only claim if it's still unclaimed or claimed more than 5 minutes ago
                .values(claimed_by=func.now())
            )
            result=db.execute(claimed_running_step)
            
            logger.info(f"Worker tried to claim step: {running_step.id if running_step else 'None'}. Rows affected: {result.rowcount}")

            if result.rowcount == 0:
                logger.error(f"Worker failed to claim step: {running_step.id}. It may have been claimed by another worker.")
                db.rollback()
                continue

            logger.info(f"Worker claimed step: {running_step.id if running_step else 'None'}")
            db.commit()
            # os._exit(1)  # Exit the worker process after commiting for testing purposes. Remove this line for continuous processing in production.

            # Refetch step as DB is the source of truth as u will use step data
            step=(
                db.query(WorkflowStep)
                .filter(WorkflowStep.id==running_step.id)
                .first()
            )

            logger.info(f"Worker is executing step: {step.id} of type: {step.execution_type} with payload: {step.execution_payload}")

            # execute the step
            try:
                result=execute_step(step) 
            except Exception as e:
                logger.warning(f"Worker encountered an error while executing step: {step.id}. Error: {e}")
                result="RETRY"    
            # Mark the step as completed
            if result=='SUCCESS':
                logger.info(f"Worker completed step: {step.id} successfully. Notifying API.")
                requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/complete",timeout=REQUEST_TIMEOUT)
            elif result=='FAIL':
                logger.error(f"Worker failed step: {step.id}. Notifying API.")
                requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail",timeout=REQUEST_TIMEOUT)
            elif result=='RETRY':
                step.retry_count+=1
                if step.retry_count>step.max_retries:
                    logger.error(f"Worker exhausted max retries for step: {step.id}. Marking step as failed and notifying API.")
                    requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail",timeout=REQUEST_TIMEOUT)
                else:
                    # rety backoff
                    backoff_time=min(30, 2**step.retry_count)  # Cap the backoff time at 30 seconds

                    logger.warning(f"Worker will retry step: {step.id} after backoff time: {backoff_time} seconds")
                    time.sleep(backoff_time)

                    step.claimed_by=None  # Reset claimed_by to allow other workers to quickly pick it up for retry
                    db.commit()  # Update retry count in DB so that worker can retry the step


            # For testing, we can fail step number 2 to see the workflow failure handling
            ''' 
            if running_step.step_number==2:
               requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail")
            else:
               requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/complete") 
            '''
              
        except Exception as e:
            logger.error(f"Worker encountered an error: {e}")
            db.rollback()
    
        finally:
            db.close()

if __name__ == "__main__":
    worker()