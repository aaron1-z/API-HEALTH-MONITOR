from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class MonitorTargetBase(SQLModel):
    name: str = Field(index=True)
    url: str
    interval_seconds: int = Field(default=60)
    is_active: bool = Field(default=True)

class MonitorTarget(MonitorTargetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship to results
    results: List["HealthCheckResult"] = Relationship(back_populates="target")

class MonitorTargetCreate(MonitorTargetBase):
    pass

class MonitorTargetRead(MonitorTargetBase):
    id: int
    last_status: Optional[str] = None
    last_checked: Optional[datetime] = None

class HealthCheckResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_id: int = Field(foreign_key="monitortarget.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    is_healthy: bool
    error_message: Optional[str] = None
    
    target: Optional[MonitorTarget] = Relationship(back_populates="results")
