import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String, default="employee")
    device_id = Column(String, unique=True, index=True, nullable=True)
    checkins = relationship("CheckIn", back_populates="employee")

class CheckIn(Base):
    __tablename__ = "checkins"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Временная метка в UTC, совместимая с Python 3.14+
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_valid = Column(Boolean, default=False)
    verification_method = Column(String, default="gps_and_qr")
    
    employee = relationship("User", back_populates="checkins")
