import os
import uuid

# db config
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workflow.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# worker config
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))  # seconds, can be overridden by environment variable if needed
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CLAIM_TIMEOUT_SECONDS = int(os.getenv("CLAIM_TIMEOUT_SECONDS", "15"))
WORKER_ID = f'{os.getpid()}-{uuid.uuid4()}'  # Unique identifier for the worker instance, useful for logging and debugging