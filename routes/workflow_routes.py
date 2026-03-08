from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.db import SessionLocal
from models.workflow_models import Workflow, WorkflowStep
from utils.basic_logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class CreateWorkflowStepRequest(BaseModel):
    name: str
    execution_type: str
    execution_payload: dict

@router.post("/workflows")
def create_workflow():
    logger.debug("Creating a new workflow...")
    db = SessionLocal()
    try:
        workflow = Workflow(status="CREATED")
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        logger.info(
            f"Workflow created successfully with ID: {workflow.id} and status: {workflow.status}"
        )

        return {"id": workflow.id, "status": workflow.status}

    except Exception:
        logger.exception("Error occurred while creating workflow")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/start")
def start_workflow(workflow_id: int):
    logger.debug(f"Attempting to start workflow with ID: {workflow_id}")
    db: Session = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if not workflow:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.status != "CREATED":
            logger.warning(f"Workflow with ID: {workflow_id} cannot be started")
            raise HTTPException(status_code=400, detail="Workflow cannot be started")

        first_step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_number.asc())
            .first()
        )
        logger.debug(f"Retrieved first step with ID: {first_step.id if first_step else 'None'}")

        if not first_step:
            logger.warning(f"Workflow with ID: {workflow_id} cannot be started without steps")
            raise HTTPException(
                status_code=400, detail="Workflow cannot be started without steps"
            )

        if first_step.status != "CREATED":
            logger.warning(
                f"Workflow with ID: {workflow_id} cannot be started because the first step is not in CREATED state"
            )
            raise HTTPException(
                status_code=400,
                detail="Workflow cannot be started because the first step is not in CREATED state",
            )

        running_step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == workflow_id, WorkflowStep.status == "RUNNING")
            .first()
        )
        logger.debug(
            f"Retrieved running step with ID: {running_step.id if running_step else 'None'}"
        )

        if running_step:
            logger.warning(
                f"Workflow with ID: {workflow_id} cannot be started because another step is already in RUNNING state"
            )
            raise HTTPException(
                status_code=400,
                detail="Workflow cannot be started because another step is already in RUNNING state",
            )

        logger.debug(
            f"Starting workflow with ID: {workflow_id} by setting workflow status to RUNNING and first step status to RUNNING"
        )

        workflow.status = "RUNNING"
        first_step.status = "RUNNING"
        db.commit()
        db.refresh(workflow)

        logger.info(
            f"Workflow with ID: {workflow_id} started successfully with status: {workflow.status} and first step with ID: {first_step.id} set to RUNNING"
        )

        return {"workflow_id": workflow.id, "status": workflow.status}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while starting workflow with ID: {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/complete")
def complete_workflow(workflow_id: int):
    logger.debug(f"Attempting to complete workflow with ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if workflow is None:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.status != "RUNNING":
            logger.warning(
                f"Workflow with ID: {workflow_id} cannot be completed because it is not in RUNNING state"
            )
            raise HTTPException(status_code=400, detail="Workflow cannot be completed")

        logger.debug(f"Completing workflow with ID: {workflow_id}")
        workflow.status = "COMPLETED"
        db.commit()
        db.refresh(workflow)
        logger.info(
            f"Workflow with ID: {workflow_id} completed successfully with status: {workflow.status}"
        )

        return {"id": workflow.id, "status": workflow.status}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while completing workflow with ID: {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/fail")
def fail_workflow(workflow_id: int):
    logger.debug(f"Attempting to fail workflow with ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if workflow is None:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.status != "RUNNING":
            logger.warning(
                f"Workflow with ID: {workflow_id} cannot be failed because it is not in RUNNING state"
            )
            raise HTTPException(status_code=400, detail="Workflow cannot be failed")

        logger.debug(f"Failing workflow with ID: {workflow_id}")
        workflow.status = "FAILED"
        db.commit()
        db.refresh(workflow)
        logger.error(
            f"Workflow with ID: {workflow_id} failed successfully with status: {workflow.status}"
        )

        return {"id": workflow.id, "status": workflow.status}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while failing workflow with ID: {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/steps")
def create_workflow_step(workflow_id: int, body: CreateWorkflowStepRequest):
    logger.debug(f"Attempting to create workflow step for workflow with ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if workflow is None:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status != "CREATED":
            logger.warning(
                f"Workflow with ID: {workflow_id} is not in CREATED state. Cannot add steps."
            )
            raise HTTPException(
                status_code=400,
                detail="Workflow steps can only be added to workflows in CREATED state",
            )

        step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_number.desc())
            .first()
        )
        step_number = step.step_number + 1 if step else 1

        step = WorkflowStep(
            workflow_id=workflow_id,
            name=body.name,
            step_number=step_number,
            status="CREATED",
            execution_type=body.execution_type,
            execution_payload=body.execution_payload,
        )

        logger.debug(
            f"Creating workflow step with name: {step.name}, step_number: {step.step_number}, execution_type: {step.execution_type} for workflow with ID: {workflow_id}"
        )

        db.add(step)
        db.commit()
        db.refresh(step)

        logger.info(
            f"Workflow step created successfully with ID: {step.id}, name: {step.name}, step_number: {step.step_number}, execution_type: {step.execution_type}"
        )

        return {"id": step.id, "workflow_id": step.workflow_id, "step_status": step.status}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while creating workflow step for workflow ID: {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/steps/{step_id}/complete")
def complete_workflow_step(workflow_id: int, step_id: int):
    logger.debug(f"Attempting to complete workflow step for workflow with ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if not workflow:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status != "RUNNING":
            logger.warning(
                f"Workflow with ID: {workflow_id} is not in RUNNING state. Cannot complete steps."
            )
            raise HTTPException(
                status_code=400,
                detail="Workflow steps can only be completed for workflows in RUNNING state",
            )

        step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id)
            .first()
        )
        logger.debug(f"Retrieved workflow step with ID: {step_id}")

        if not step:
            logger.warning(f"Workflow step with ID: {step_id} not found")
            raise HTTPException(status_code=404, detail="Workflow step not found")
        if step.status != "RUNNING":
            logger.warning(f"Workflow step with ID: {step_id} is not in RUNNING state. Cannot complete.")
            raise HTTPException(
                status_code=400,
                detail="Workflow step cannot be completed because it is not in RUNNING state",
            )

        step.status = "COMPLETED"
        next_step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == workflow_id, WorkflowStep.step_number == step.step_number + 1)
            .first()
        )
        logger.debug(f"Retrieved next workflow step with ID: {next_step.id if next_step else None}")

        if next_step:
            logger.debug(f"Found next workflow step with ID: {next_step.id}")
            next_step.status = "RUNNING"
        else:
            logger.debug(f"No next workflow step found for workflow with ID: {workflow_id}")
            workflow.status = "COMPLETED"

        db.commit()
        db.refresh(step)
        db.refresh(workflow)

        logger.info(
            f"Workflow step with ID: {step_id} completed successfully. Workflow with ID: {workflow_id} status updated to: {workflow.status}"
        )

        return {
            "id": step.id,
            "workflow_id": step.workflow_id,
            "workflow_status": workflow.status,
            "step_status": step.status,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while completing step {step_id} for workflow {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/steps/{step_id}/fail")
def fail_workflow_step(workflow_id: int, step_id: int):
    logger.debug(f"Attempting to fail workflow step for workflow with ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if not workflow:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status != "RUNNING":
            logger.warning(f"Workflow with ID: {workflow_id} is not in RUNNING state. Cannot fail steps.")
            raise HTTPException(
                status_code=400,
                detail="Workflow steps can only be completed for workflows in RUNNING state",
            )

        step = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id)
            .first()
        )

        logger.debug(f"Retrieved workflow step with ID: {step_id}")

        if not step:
            logger.warning(f"Workflow step with ID: {step_id} not found")
            raise HTTPException(status_code=404, detail="Workflow step not found")
        if step.status != "RUNNING":
            logger.warning(f"Workflow step with ID: {step_id} is not in RUNNING state. Cannot fail.")
            raise HTTPException(
                status_code=400,
                detail="Workflow step cannot be FAILED because it is not in RUNNING state",
            )

        step.status = "FAILED"
        workflow.status = "FAILED"

        db.commit()
        db.refresh(step)
        db.refresh(workflow)
        logger.info(
            f"Workflow step with ID: {step_id} failed successfully. Workflow with ID: {workflow_id} also marked as FAILED."
        )

        return {
            "id": step.id,
            "workflow_id": step.workflow_id,
            "workflow_status": workflow.status,
            "step_status": step.status,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while failing step {step_id} for workflow {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/workflows")
def get_all_worflows():
    logger.debug("Attempting to retrieve all workflows")
    db = SessionLocal()
    try:
        workflows_db = db.query(Workflow).all()

        workflows = [{"id": w.id, "status": w.status} for w in workflows_db]

        return {"workflows": workflows}

    except Exception:
        logger.exception("Error occurred while retrieving workflows")
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: int):
    logger.debug(f"Attempting to retrieve workflow with ID: {workflow_id}")
    db = SessionLocal()
    try:
        workflow_db = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        logger.debug(f"Retrieved workflow with ID: {workflow_id}")

        if not workflow_db:
            logger.warning(f"Workflow with ID: {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")

        worflow_steps = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_number.asc())
            .all()
        )

        logger.debug(f"Retrieved workflow steps for workflow ID: {workflow_id}")

        steps = [
            {"id": s.id, "name": s.name, "step_number": s.step_number, "status": s.status}
            for s in worflow_steps
        ]

        return {"id": workflow_db.id, "status": workflow_db.status, "steps": steps}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        logger.exception(f"Error occurred while retrieving workflow with ID: {workflow_id}")
        db.rollback()
        raise
    finally:
        db.close()
