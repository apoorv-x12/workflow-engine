from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import relationship
from db import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    steps = relationship("WorkflowStep", back_populates="workflow")
    
class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    step_number = Column(Integer, nullable=False)
    workflow=relationship("Workflow", back_populates="steps")
    claimed_by = Column(DateTime(timezone=True), nullable=True)  # To track which worker claimed the step

    __table_args__ = (
        # Ensure that step_number is unique within the same workflow
        UniqueConstraint('workflow_id', 'step_number', name='uix_workflow_step_number'),
        # Ensure that name is unique within the same workflow
        UniqueConstraint('workflow_id', 'name', name='uix_workflow_step_name'),
    )
    