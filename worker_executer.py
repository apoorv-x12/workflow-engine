from time import time
import requests

REQUEST_TIMEOUT=10

def execute_step(step):
    print(f"Executing step {step.id} of type {step.execution_type} with payload {step.execution_payload}")
    # Here you would have logic to execute the step based on its type and payload
    if step.execution_type == "SLEEP":
        duration = step.execution_payload.get("duration")
        if not duration:
            print("No duration specified for SLEEP step. Failing step.")
            return "FAIL"
        
        print(f"Sleeping for {duration} seconds...")
        time.sleep(duration)
        return "SUCCESS"  # Indicate success
    
    elif step.execution_type == "HTTP":
        url = step.execution_payload.get("url")
        method = step.execution_payload.get("method", "GET").upper()
        headers = step.execution_payload.get("headers", {})
        data = step.execution_payload.get("data", {})

        if not url:
            print("No URL specified for HTTP step. Failing step.")
            return "FAIL"
        
        response = requests.request(method, url, headers=headers, data=data, timeout=REQUEST_TIMEOUT)
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"HTTP request successful with status code {response.status_code}")
            return "SUCCESS"
        elif response.status_code >= 400 and response.status_code < 500:
            print(f"HTTP request failed with status code {response.status_code}")
            return "FAIL"
        elif response.status_code >= 500:
            print(f"HTTP request encountered server error with status code {response.status_code}")
            raise Exception(f"Server error: {response.status_code}")
           
    else:
        raise Exception(f"Unknown execution type: {step.execution_type}")