from time import time
import requests
from basic_logging import get_logger

logger = get_logger(__name__)

REQUEST_TIMEOUT=10

def execute_step(step):
    logger.info(f"Executing step {step.id} of type {step.execution_type} with payload {step.execution_payload}")
    # Here you would have logic to execute the step based on its type and payload
    if step.execution_type.upper() == "SLEEP":
        logger.info(f"Step {step.id} is a SLEEP step.")
        
        duration = step.execution_payload.get("duration")
        if not duration:
            logger.error("No duration specified for SLEEP step. Failing step.")
            return "FAIL"
        
        logger.info(f"Sleeping for {duration} seconds...")
        time.sleep(duration)
        return "SUCCESS"  # Indicate success
    
    elif step.execution_type.upper() == "HTTP":
        logger.info(f"Step {step.id} is an HTTP step.")

        url = step.execution_payload.get("url")
        method = step.execution_payload.get("method", "GET").upper()
        headers = step.execution_payload.get("headers", {})
        data = step.execution_payload.get("data", {})

        if not url:
            logger.error("No URL specified for HTTP step. Failing step.")
            return "FAIL"
        
        # Make the HTTP request idempotent 
        headers['Idempotency-Key'] = f"{step.workflow_id}-{step.id}"
        response = requests.request(method, url, headers=headers, data=data, timeout=REQUEST_TIMEOUT)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"HTTP request successful with status code {response.status_code}")
            return "SUCCESS"
        elif response.status_code >= 400 and response.status_code < 500:
            logger.error(f"HTTP request failed with status code {response.status_code}")
            return "FAIL"
        elif response.status_code >= 500:
            logger.warning(f"HTTP request encountered server error with status code {response.status_code}")
            raise Exception(f"Server error: {response.status_code}")
           
    else:
        logger.warning(f"Unknown execution type: {step.execution_type}")
        raise Exception(f"Unknown execution type: {step.execution_type}")