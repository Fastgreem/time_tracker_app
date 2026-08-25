import math
import time
import hmac
import hashlib
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database
import models

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Time Tracker API")

OFFICE_LAT = 55.7558
OFFICE_LON = 37.6173
ALLOWED_RADIUS_METERS = 50.0

# Секретный ключ для генерации динамических QR-кодов (знают только сервер и экран в офисе)
QR_SECRET_KEY = b"SUPER_SECRET_OFFICE_KEY_123"

def get_current_qr_code() -> str:
    """
    Генерирует уникальный 6-значный код, меняющийся каждые 30 секунд (алгоритм TOTP)
    """
    time_window = int(time.time() // 30)
    msg = str(time_window).encode()
    sig = hmac.new(QR_SECRET_KEY, msg, hashlib.sha256).hexdigest()
    # Берем 6 цифр из хэша
    return str(int(sig, 16) % 1000000).zfill(6)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@app.get("/")
def read_root():
    return {"status": "Server is running successfully!"}

# Эндпоинт для офисного экрана/планшета, который показывает текущий QR-код
@app.get("/api/get_office_qr")
def get_office_qr():
    return {"current_qr": get_current_qr_code(), "expires_in_seconds": 30 - int(time.time() % 30)}

@app.post("/api/checkin")
def employee_checkin(user_id: int, lat: float, lon: float, qr_code: str, db: Session = Depends(database.get_db)):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Некорректные GPS-координаты")
    
    # 1. Проверка GPS
    distance = calculate_distance(lat, lon, OFFICE_LAT, OFFICE_LON)
    is_gps_valid = distance <= ALLOWED_RADIUS_METERS
    
    # 2. Проверка Динамического QR-кода
    expected_qr = get_current_qr_code()
    # Разрешаем также код из предыдущего 30-секундного окна (на случай, если сотрудник нажал кнопку ровно в момент смены кода)
    time_window_prev = int((time.time() - 30) // 30)
    sig_prev = hmac.new(QR_SECRET_KEY, str(time_window_prev).encode(), hashlib.sha256).hexdigest()
    expected_qr_prev = str(int(sig_prev, 16) % 1000000).zfill(6)
    
    is_qr_valid = (qr_code == expected_qr) or (qr_code == expected_qr_prev)
    
    # Итоговая валидность — должен совпасть и GPS, и QR-код
    total_valid = is_gps_valid and is_qr_valid
    
    new_checkin = models.CheckIn(
        user_id=user_id, 
        latitude=lat, 
        longitude=lon, 
        is_valid=total_valid,
        verification_method="gps_and_qr"
    )
    db.add(new_checkin)
    db.commit()
    db.refresh(new_checkin)
    
    if not is_gps_valid:
        raise HTTPException(status_code=400, detail="Вы слишком далеко от офиса!")
        
    if not is_qr_valid:
        raise HTTPException(status_code=400, detail="Действие QR-кода истекло или код неверный! Отсканируйте заново.")
    
    return {
        "message": "Авторизация успешна! Двойной контроль (GPS + QR) пройден.", 
        "checkin_id": new_checkin.id
    }
