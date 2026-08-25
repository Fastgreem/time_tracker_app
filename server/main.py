from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database
import models

# Автоматически создаем базу данных sql_app.db при старте
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Time Tracker API")

@app.get("/")
def read_root():
    return {"status": "Server is running successfully!"}

@app.post("/api/checkin")
def employee_checkin(user_id: int, lat: float, lon: float, db: Session = Depends(database.get_db)):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid GPS coordinates")
    
    new_checkin = models.CheckIn(user_id=user_id, latitude=lat, longitude=lon, is_valid=True)
    db.add(new_checkin)
    db.commit()
    db.refresh(new_checkin)
    
    return {
        "message": "Чекин успешно зафиксирован!", 
        "checkin_id": new_checkin.id,
        "time": new_checkin.timestamp
    }
