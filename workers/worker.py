import time
import requests
from db.db import SessionLocal
from sqlalchemy import func, update
from models.workflow_models import WorkflowStep
from workers.worker_executer import execute_step
import os
import uuid
from datetime import datetime, timedelta, timezone
from utils.basic_logging import get_logger
from config import API_BASE_URL, CLAIM_TIMEOUT_SECONDS, REQUEST_TIMEOUT, WORKER_ID

logger=get_logger(__name__)

def worker():
    while True:
        db=SessionLocal()
        try:
            stale_claim_threshold = datetime.now(timezone.utc) - timedelta(seconds=CLAIM_TIMEOUT_SECONDS)
            
            running_step=(
                 db.query(WorkflowStep)
                 .filter(WorkflowStep.status=="RUNNING",
                        (WorkflowStep.claimed_by == None) | (WorkflowStep.claimed_by < stale_claim_threshold),
                         WorkflowStep.next_retry_at <= datetime.now(timezone.utc))
                 .order_by(WorkflowStep.created_at, WorkflowStep.id)
                 .first()
            )

            logger.debug(f"Worker fetched step: {running_step.id if running_step else 'None'} with status: {running_step.status if running_step else 'N/A'}")
 
            if not running_step:
                 logger.warning("No running steps found. Worker is idle.")
                 time.sleep(2)
                 continue
            
            # Claim the step by setting the claimed_by timestamp
            claimed_running_step = (
                update(WorkflowStep)
                .where(
                    WorkflowStep.id == running_step.id,
                    (WorkflowStep.claimed_by == None) | (WorkflowStep.claimed_by < stale_claim_threshold),
                )
                .values(claimed_by=func.now())
            )
            result=db.execute(claimed_running_step)
            
            logger.info(f"Worker tried to claim step: {running_step.id if running_step else 'None'}. Rows affected: {result.rowcount}")

            if result.rowcount == 0:
                logger.warning(f"Worker failed to claim step: {running_step.id}. It may have been claimed by another worker.")
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

            logger.debug(f"Worker is executing step: {step.id} of type: {step.execution_type} with payload: {step.execution_payload}")

            # execute the step
            try:
                result=execute_step(step) 
            except Exception:
                logger.exception(f"Worker encountered an error while executing step: {step.id}")
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
                   # time.sleep(backoff_time)
                    retry_timeout=datetime.now(timezone.utc)+timedelta(seconds=backoff_time)
                    step.next_retry_at=retry_timeout
                    step.claimed_by=None  # Reset claimed_by to allow other workers to quickly pick it up for retry
                    db.commit()  # Update retry count in DB so that worker can retry the step
                    logger.info(f"Worker reset claim for step: {step.id} to allow retry. Current retry count: {step.retry_count} and claimed_by reset to: {step.claimed_by}")


            # For testing, we can fail step number 2 to see the workflow failure handling
            ''' 
            if running_step.step_number==2:
               requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/fail")
            else:
               requests.post(f"{API_BASE_URL}/workflows/{step.workflow_id}/steps/{step.id}/complete") 
            '''
              
        except Exception:
            logger.exception("Worker encountered an unexpected error")
            db.rollback()
    
        finally:
            db.close()

if __name__ == "__main__":
    logger.info(f"Worker started with ID: {WORKER_ID}")
    worker()
