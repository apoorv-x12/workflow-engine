from time import time
import requests
from utils.basic_logging import get_logger

logger = get_logger(__name__)

REQUEST_TIMEOUT=10

def execute_step(step):
    logger.debug(f"Executing step {step.id} of type {step.execution_type} with payload {step.execution_payload}")
    # Here you would have logic to execute the step based on its type and payload
    if step.execution_type.upper() == "SLEEP":
        logger.debug(f"Step {step.id} is a SLEEP step.")
        
        duration = step.execution_payload.get("duration")
        if not duration:
            logger.debug(f"Step {step.id} missing required 'duration' for SLEEP execution")
            return "FAIL"
        
        time.sleep(duration)
        return "SUCCESS"  # Indicate success
    
    elif step.execution_type.upper() == "HTTP":
        logger.debug(f"Step {step.id} is an HTTP step.")

        url = step.execution_payload.get("url")
        method = step.execution_payload.get("method", "GET").upper()
        headers = step.execution_payload.get("headers", {})
        data = step.execution_payload.get("data", {})

        logger.debug(f"HTTP step {step.id} details - URL: {url}, Method: {method}, Headers: {headers}, Data: {data}")

        if not url:
            logger.debug(f"Step {step.id} missing required 'url' for HTTP execution")
            return "FAIL"
        
        # Make the HTTP request idempotent 
        headers['Idempotency-Key'] = f"{step.workflow_id}-{step.id}"
        response = requests.request(method, url, headers=headers, data=data, timeout=REQUEST_TIMEOUT)
        
        if response.status_code >= 200 and response.status_code < 300:
            return "SUCCESS"
        elif response.status_code >= 400 and response.status_code < 500:
            return "FAIL"
        elif response.status_code >= 500:
            logger.debug(f"HTTP request encountered server error with status code {response.status_code}")
            raise Exception(f"Server error: {response.status_code}")
           
    else:
        logger.debug(f"Unknown execution type: {step.execution_type}")
        raise Exception(f"Unknown execution type: {step.execution_type}")
