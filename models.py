from sqlalchemy import Column, Integer, String
from db import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)