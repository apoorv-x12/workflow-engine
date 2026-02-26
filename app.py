# pylint: disable=import-error
from fastapi import FastAPI, HTTPException
from db import engine, SessionLocal, Base
from models import Workflow, WorkflowStep
from sqlalchemy.orm import Session
from pydantic import BaseModel

class CreateWorkflowStepRequest(BaseModel):
    name: str

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
    except Exception:
        db.rollback()
        raise 
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
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != "CREATED":
            raise HTTPException(status_code=400, detail="Workflow cannot be started")
        
        first_step=db.query(WorkflowStep).filter(WorkflowStep.workflow_id==workflow_id).order_by(WorkflowStep.step_number.asc()).first()
        # steps=workflow.steps - use this shortcut for all steps of the workflow, but it will make an additional query to fetch steps if not already loaded
        if not first_step:
            raise HTTPException(status_code=400, detail="Workflow cannot be started without steps")
        
        if first_step.status != "CREATED":
            raise HTTPException(status_code=400, detail="Workflow cannot be started because the first step is not in CREATED state")
        
        running_step=db.query(WorkflowStep).filter(WorkflowStep.workflow_id==workflow_id, WorkflowStep.status=="RUNNING").first()
        if running_step:    
            raise HTTPException(status_code=400, detail="Workflow cannot be started because another step is already in RUNNING state")
        
        workflow.status = "RUNNING"
        first_step.status = "RUNNING"
        db.commit()
        db.refresh(workflow)
        
        return {
            "workflow_id": workflow.id,
            "status": workflow.status,
        }
    except Exception:
        db.rollback()
        raise 
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
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.status != "RUNNING":
            raise HTTPException(status_code=400, detail="Workflow cannot be completed")

        workflow.status = "COMPLETED"
        db.commit()
        db.refresh(workflow)

        return {"id": workflow.id, "status": workflow.status}
    except Exception:
        db.rollback()
        raise 
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
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.status != "RUNNING":
            raise HTTPException(status_code=400, detail="Workflow cannot be failed")

        workflow.status = "FAILED"
        db.commit()
        db.refresh(workflow)

        return {"id": workflow.id, "status": workflow.status}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.post("/workflows/{workflow_id}/steps")
def create_workflow_step(workflow_id: int, body: CreateWorkflowStepRequest):
    db = SessionLocal()
    try:
        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == workflow_id)
            .first()
        )

        if workflow is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status != "CREATED":
            raise HTTPException(status_code=400, detail="Workflow steps can only be added to workflows in CREATED state")
        
        step = db.query(WorkflowStep).filter(WorkflowStep.workflow_id==workflow_id).order_by(WorkflowStep.step_number.desc()).first()
        step_number = step.step_number + 1 if step else 1

        step = WorkflowStep(
            workflow_id=workflow_id,
            name=body.name,
            step_number=step_number,
            status="CREATED"
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        
        return {
            "id": step.id,  
            "workflow_id": step.workflow_id,
            "step_status": step.status
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.post("/workflows/{workflow_id}/steps/{step_id}/complete")
def complete_workflow_step(workflow_id: int, step_id: int):
    db = SessionLocal()
    try:
        workflow=(
           db.query(Workflow)
           .filter(Workflow.id==workflow_id)
           .first()
        )

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status != "RUNNING":
            raise HTTPException(status_code=400, detail="Workflow steps can only be completed for workflows in RUNNING state")
        
        step=(
            db.query(WorkflowStep)
            .filter(WorkflowStep.id==step_id, WorkflowStep.workflow_id==workflow_id)
            .first()
        )
        if not step:
            raise HTTPException(status_code=404, detail="Workflow step not found")
        if step.status != "RUNNING":
            raise HTTPException(status_code=400, detail="Workflow step cannot be completed because it is not in RUNNING state")
      
        step.status = "COMPLETED"
        next_step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id==workflow_id, WorkflowStep.step_number==step.step_number+1)
            .first()
        )
        
        if next_step:
            next_step.status = "RUNNING"
        else:
            workflow.status = "COMPLETED"

        db.commit()
        db.refresh(step)
        db.refresh(workflow)

        return {
            "id": step.id,
            "workflow_id": step.workflow_id,
            "workflow_status": workflow.status,
            "step_status": step.status
        }
    
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.post("/workflows/{workflow_id}/steps/{step_id}/fail")
def fail_workflow_step(workflow_id: int, step_id: int):
    db = SessionLocal()
    try:
        workflow=(
           db.query(Workflow)
           .filter(Workflow.id==workflow_id)
           .first()
        )

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status != "RUNNING":
            raise HTTPException(status_code=400, detail="Workflow steps can only be completed for workflows in RUNNING state")
        
        step=(
            db.query(WorkflowStep)
            .filter(WorkflowStep.id==step_id, WorkflowStep.workflow_id==workflow_id)
            .first()
        )
        if not step:
            raise HTTPException(status_code=404, detail="Workflow step not found")
        if step.status != "RUNNING":
            raise HTTPException(status_code=400, detail="Workflow step cannot be FAILED because it is not in RUNNING state")
      
        step.status = "FAILED"
        workflow.status = "FAILED"

        db.commit()
        db.refresh(step)
        db.refresh(workflow)

        return {
            "id": step.id,
            "workflow_id": step.workflow_id,
            "workflow_status": workflow.status,
            "step_status": step.status
        }
    
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.get('/workflows')
def get_all_worflows():
    db=SessionLocal()
    try:
        workflows_db=(
            db.query(Workflow)
            .all()
        )

        workflows=[
            {'id':w.id,'status':w.status}
            for w in workflows_db
        ]

        return {
         'workflows' : workflows
        }

    except Exception:
        db.rollback()
        raise  
    finally:
        db.close()

@app.get('/workflows/{workflow_id}')
def get_workflow(workflow_id: int):
    db=SessionLocal()
    try:
        workflow_db=(
            db.query(Workflow)
            .filter(Workflow.id==workflow_id)
            .first()
        )
        if not workflow_db:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        worflow_steps=(
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id==workflow_id)
            .order_by(WorkflowStep.step_number.asc())
            .all()
        )

        steps=[
            {
                'id':s.id,
                'name':s.name,
                'step_number':s.step_number,
                'status':s.status
            }
            for s in worflow_steps
        ]

        return {
            'id': workflow_db.id,
            'status': workflow_db.status,
            'steps': steps
        }
    except Exception:
        db.rollback()
        raise 
    finally:
        db.close()