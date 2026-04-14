import os
import logging
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv

import database
from database import get_db, Truck, SGILog

load_dotenv()

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AutoGATE_API")

# Initialize database
database.init_db()

app = FastAPI(
    title="AutoGATE MVP API",
    description="API para gestão de entrada e saída de veículos em pátio logístico",
    version="1.0.0"
)

# Pydantic Models
class TruckBase(BaseModel):
    id: str
    motorista: str
    cpf_motorista: str
    lote: str
    modelo_veiculo: str

class TruckCreate(TruckBase):
    pass

class TruckResponse(TruckBase):
    class Config:
        from_attributes = True

class SGILogResponse(BaseModel):
    log_id: int
    truck_id: str
    doca_id: str
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# API Routes
@app.post("/register", response_model=TruckResponse, status_code=status.HTTP_201_CREATED)
def register_truck(truck: TruckCreate, db: Session = Depends(get_db)):
    """
    Cadastra um novo caminhão no sistema.
    """
    db_truck = db.query(Truck).filter(Truck.id == truck.id).first()
    if db_truck:
        logger.warning(f"Attempt to register existing truck ID: {truck.id}")
        raise HTTPException(status_code=400, detail="Truck already registered")
    
    try:
        new_truck = Truck(**truck.model_dump())
        db.add(new_truck)
        db.commit()
        db.refresh(new_truck)
        logger.info(f"Truck registered: {truck.id} - {truck.motorista}")
        return new_truck
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering truck: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during registration")

@app.get("/truck/{truck_id}", response_model=TruckResponse)
def get_truck(truck_id: str, db: Session = Depends(get_db)):
    """
    Busca os dados de um caminhão pelo seu ID.
    """
    db_truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not db_truck:
        logger.warning(f"Truck ID not found: {truck_id}")
        raise HTTPException(status_code=404, detail="Truck not found")
    return db_truck

@app.get("/logs", response_model=List[SGILogResponse])
def get_logs(truck_id: Optional[str] = None, doca_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retorna o histórico de logs do SGI, com filtros opcionais.
    """
    query = db.query(SGILog)
    if truck_id:
        query = query.filter(SGILog.truck_id == truck_id)
    if doca_id:
        query = query.filter(SGILog.doca_id == doca_id)
    
    logs = query.order_by(SGILog.timestamp.desc()).all()
    return logs

@app.get("/health")
def health_check():
    """
    Endpoint para verificação de status do serviço.
    """
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
 
