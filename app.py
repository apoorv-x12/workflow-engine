# pylint: disable=import-error
from fastapi import FastAPI
from db import engine, SessionLocal, Base
from models import Workflow
from sqlalchemy.orm import Session

app = FastAPI()
# Create tables once when app starts
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/workflows")
def create_workflow():
    db = SessionLocal()
    try:
        workflow = Workflow(status="CREATED")
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return {
            "id": workflow.id,
            "status": workflow.status
        }
    finally:        
        db.close()
@app.post("/workflows/{workflow_id}/start")
def start_workflow(workflow_id: int):
    db: Session = SessionLocal()
    try:
        workflow = (
            db.query(Workflow)
            .filter(Workflow.id==workflow_id)
            .first()
        )
        if not workflow:
            return {"error": "Workflow not found"}
        if workflow.status != "CREATED":
            return {"error": "Workflow cannot be started"}
        workflow.status = "RUNNING"
        db.commit()
        db.refresh(workflow)
        return {
            "id": workflow.id,
            "status": workflow.status
        }
    finally:
        db.close()    

@app.post("/workflows/{workflow_id}/complete")
def complete_workflow(workflow_id: int):
    db = SessionLocal()
    try:
        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == workflow_id)
            .first()
        )

        if workflow is None:
            return {"error": "Workflow not found"}

        if workflow.status != "RUNNING":
            return {"error": "Workflow cannot be completed"}

        workflow.status = "COMPLETED"
        db.commit()
        db.refresh(workflow)

        return {"id": workflow.id, "status": workflow.status}
    finally:
        db.close()

@app.post("/workflows/{workflow_id}/fail")
def fail_workflow(workflow_id: int):
    db = SessionLocal()
    try:
        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == workflow_id)
            .first()
        )

        if workflow is None:
            return {"error": "Workflow not found"}

        if workflow.status != "RUNNING":
            return {"error": "Workflow cannot be failed"}

        workflow.status = "FAILED"
        db.commit()
        db.refresh(workflow)

        return {"id": workflow.id, "status": workflow.status}
    finally:
        db.close()