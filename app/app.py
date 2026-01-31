import asyncio
import httpx
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, create_engine, SQLModel
from models import MonitorTarget, MonitorTargetCreate, MonitorTargetRead, HealthCheckResult

# Configuration
DATABASE_URL = "sqlite:///./database.db"
# For postgres, use: "postgresql://user:password@host/dbname"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Monitoring Service
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Monitor")

async def check_target(target: MonitorTarget, session: Session):
    logger.info(f"Checking {target.url}...")
    result = HealthCheckResult(target_id=target.id, is_healthy=False)
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            start_time = datetime.utcnow()
            response = await client.get(target.url)
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result.status_code = response.status_code
            result.latency_ms = latency
            
            # Validate HTTP status code (200-299 considered healthy)
            if 200 <= response.status_code < 300:
                result.is_healthy = True
            else:
                result.is_healthy = False
                result.error_message = f"Status {response.status_code}"
                
    except Exception as e:
        result.is_healthy = False
        result.error_message = str(e)
    
    session.add(result)
    session.commit()
    
    # Alerting: Log status changes (Hook for SNS/Email integrations)
    if not result.is_healthy:
        logger.error(f"ALERT: {target.name} ({target.url}) is DOWN! Error: {result.error_message}")
    else:
        logger.info(f"SUCCESS: {target.name} is UP. Latency: {result.latency_ms:.2f}ms")

async def monitoring_loop():
    while True:
        try:
            with Session(engine) as session:
                statement = select(MonitorTarget).where(MonitorTarget.is_active == True)
                targets = session.exec(statement).all()
                
                tasks = []
                for target in targets:
                    tasks.append(check_target(target, session))
                
                if tasks:
                    await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        await asyncio.sleep(60) # Polling Interval

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Start the monitoring loop in background
    task = asyncio.create_task(monitoring_loop())
    yield
    # Cleanup
    task.cancel()

app = FastAPI(lifespan=lifespan)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

# app.mount("/static", StaticFiles(directory="static"), name="static") # Uncomment if static files needed
templates = Jinja2Templates(directory="templates")

@app.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session)):
    targets = session.exec(select(MonitorTarget)).all()
    # Process targets for display
    display_data = []
    for t in targets:
        last_check = session.exec(select(HealthCheckResult).where(HealthCheckResult.target_id == t.id).order_by(HealthCheckResult.timestamp.desc()).limit(1)).first()
        status = "UNKNOWN"
        latency = "-"
        if last_check:
            status = "UP" if last_check.is_healthy else "DOWN"
            latency = f"{last_check.latency_ms:.0f}ms"
        
        display_data.append({
            "id": t.id,
            "name": t.name,
            "url": t.url,
            "interval": t.interval_seconds,
            "status": status,
            "latency": latency,
            "last_checked": last_check.timestamp if last_check else "-"
        })
    return templates.TemplateResponse("dashboard.html", {"request": request, "targets": display_data}) 

@app.get("/")
def read_root():
    return {"message": "API Health Monitor is running"}

@app.post("/targets", response_model=MonitorTargetRead)
def create_target(target: MonitorTargetCreate, session: Session = Depends(get_session)):
    db_target = MonitorTarget.from_orm(target)
    session.add(db_target)
    session.commit()
    session.refresh(db_target)
    return db_target

@app.get("/targets", response_model=List[MonitorTargetRead])
def read_targets(session: Session = Depends(get_session)):
    targets = session.exec(select(MonitorTarget)).all()
    # Enrich response with latest health metrics
    results = []
    for t in targets:
        # Get last result
        last_check = session.exec(select(HealthCheckResult).where(HealthCheckResult.target_id == t.id).order_by(HealthCheckResult.timestamp.desc()).limit(1)).first()
        read_obj = MonitorTargetRead.from_orm(t)
        if last_check:
            read_obj.last_checked = last_check.timestamp
            read_obj.last_status = "UP" if last_check.is_healthy else "DOWN"
        else:
            read_obj.last_status = "UNKNOWN"
        results.append(read_obj)
    return results

@app.delete("/targets/{target_id}")
def delete_target(target_id: int, session: Session = Depends(get_session)):
    target = session.get(MonitorTarget, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    session.delete(target)
    session.commit()
    return {"ok": True}

@app.get("/health")
def health_check():
    return {"status": "ok"}
