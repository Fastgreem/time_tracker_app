import math
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database
import models

# Автоматически создаем таблицы в базе данных при старте
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Time Tracker API")

# 📍 КОНФИГУРАЦИЯ ОФИСА: Координаты вашего рабочего места
OFFICE_LAT = 55.7558  # Широта офиса (например, центр Москвы)
OFFICE_LON = 37.6173  # Долгота офиса
ALLOWED_RADIUS_METERS = 50.0  # Радиус в метрах, внутри которого чекин разрешен

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Вычисляет расстояние в метрах между двумя GPS-координатами
    по формуле гаверсинусов.
    """
    R = 6371000.0  # Радиус Земли в метрах
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

@app.get("/")
def read_root():
    return {"status": "Server is running successfully!"}

@app.post("/api/checkin")
def employee_checkin(user_id: int, lat: float, lon: float, db: Session = Depends(database.get_db)):
    # 1. Валидация корректности самих GPS-координат
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Некорректные GPS-координаты")
    
    # 2. Расчет расстояния от сотрудника до офиса
    distance = calculate_distance(lat, lon, OFFICE_LAT, OFFICE_LON)
    
    # 3. Проверяем, входит ли сотрудник в разрешенный радиус
    is_valid_location = distance <= ALLOWED_RADIUS_METERS
    
    # 4. Записываем попытку чекина в базу данных (для истории и аудита админом)
    new_checkin = models.CheckIn(
        user_id=user_id, 
        latitude=lat, 
        longitude=lon, 
        is_valid=is_valid_location
    )
    db.add(new_checkin)
    db.commit()
    db.refresh(new_checkin)
    
    # 5. Если сотрудник слишком далеко — прерываем операцию и возвращаем ошибку
    if not is_valid_location:
        raise HTTPException(
            status_code=400, 
            detail=f"Вы слишком далеко! Расстояние: {round(distance, 1)} м. Разрешено: {ALLOWED_RADIUS_METERS} м."
        )
    
    # 6. Если всё хорошо — возвращаем успех
    return {
        "message": "Чекин успешно зафиксирован! Вы на рабочем месте.", 
        "checkin_id": new_checkin.id,
        "distance_meters": round(distance, 1),
        "time": new_checkin.timestamp
    }
