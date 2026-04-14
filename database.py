import datetime
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autogate.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(String, primary_key=True, index=True)
    motorista = Column(String, nullable=False)
    cpf_motorista = Column(String, nullable=False)
    lote = Column(String, nullable=False)
    modelo_veiculo = Column(String, nullable=False)

    logs = relationship("SGILog", back_populates="truck")

class SGILog(Base):
    __tablename__ = "sgi_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    truck_id = Column(String, ForeignKey("trucks.id"), nullable=False)
    doca_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    truck = relationship("Truck", back_populates="logs")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
