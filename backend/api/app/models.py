from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base


class User(Base):
    """User Model for PostgreSQL Authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SensorReading(Base):
    """Sensor Reading Model for Gas Array Telemetry."""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    mq2 = Column(Float, nullable=False)
    mq4 = Column(Float, nullable=False)
    mq135 = Column(Float, nullable=False)
    mq3 = Column(Float, nullable=False)
    mq7 = Column(Float, nullable=False)
    mq9 = Column(Float, nullable=False)
    temp_cam = Column(Float, nullable=False)
    humedad_cam = Column(Float, nullable=False)
    temp_reactor = Column(Float, nullable=False)
    calidad_predicha = Column(String(50), nullable=True)
    confianza = Column(Float, nullable=True)


class SystemInfo(Base):
    """System Info Metadata Table."""
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
