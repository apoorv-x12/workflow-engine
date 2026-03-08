# pylint: disable=import-error
from fastapi import FastAPI
from db.db import engine, Base
from routes.workflow_routes import router as workflow_router
from utils.basic_logging import get_logger

logger = get_logger(__name__)

app = FastAPI()

# Create tables once when app starts
@app.on_event("startup")
def startup():
    logger.debug("Creating database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    logger.debug("Health check performed successfully.")
    return {"status": "ok"}

app.include_router(workflow_router)
