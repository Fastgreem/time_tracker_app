import math
import time
import hmac
import hashlib
import warnings
import datetime
import traceback
from io import BytesIO
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import database
import models

# Импортируем openpyxl для генерации Excel
from openpyxl import Workbook

# Автоматически создаем таблицы в базе данных при старте
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Time Tracker API с выгрузкой в Excel")

# Настройки геозоны офиса
OFFICE_LAT = 55.7558
OFFICE_LON = 37.6173
ALLOWED_RADIUS_METERS = 50.0
QR_SECRET_KEY = b"SUPER_SECRET_OFFICE_KEY_123"

def get_current_qr_code() -> str:
    """Генерирует уникальный 6-значный код, меняющийся каждые 30 секунд"""
    time_window = int(time.time() // 30)
    msg = str(time_window).encode()
    sig = hmac.new(QR_SECRET_KEY, msg, hashlib.sha256).hexdigest()
    return str(int(sig, 16) % 1000000).zfill(6)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычисляет расстояние в метрах между двумя GPS-координатами"""
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

@app.get("/api/get_office_qr")
def get_office_qr():
    return {"current_qr": get_current_qr_code(), "expires_in_seconds": 30 - int(time.time() % 30)}


# --- БЛОК ГЕНЕРАЦИИ EXCEL ДЛЯ БУХГАЛТЕРИИ ---

@app.get("/api/admin/export_tabel")
def export_tabel_to_excel(db: Session = Depends(database.get_db)):
    """Генерирует табель учета рабочего времени в формате Excel"""
    try:
        # 1. Создаем простую книгу Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Табель"
        
        # Включаем принудительное отображение сетки
        ws.sheet_view.showGridLines = True
        
        # 2. Записываем простую шапку
        ws["A1"] = "ТАБЕЛЬ УЧЕТА РАБОЧЕГО ВРЕМЕНИ И КТУ"
        ws["A2"] = f"Выгружено: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        # 3. Заголовки столбцов
        headers = ["ID", "ФИО Сотрудника", "Должность", "Кол-во чекинов", "Базовый КТУ"]
        ws.append([])       # Пустая строка для отступа (Строка 3)
        ws.append(headers)  # Заголовки (Строка 4)

        # 4. Выгружаем сотрудников из базы данных
        users = db.query(models.User).all()
        
        for user in users:
            # Считаем только валидные успешные чекины сотрудника
            valid_checkins = db.query(models.CheckIn).filter(
                models.CheckIn.user_id == user.id,
                models.CheckIn.is_valid == True
            ).count()
            
            # Логика расчета базового КТУ
            ktu = 1.0 if valid_checkins > 0 else 0.0
            if user.role == "accountant":
                ktu = 1.2
                
            # Добавляем строку данных напрямую в таблицу
            ws.append([user.id, user.full_name, user.role, valid_checkins, ktu])

        # 5. Сохраняем книгу в поток байт памяти
        file_stream = BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        
        filename = f"tabel_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"
        
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        # Ловушка ошибок: если что-то пойдет не так, мы получим текстовый файл с ошибкой
        error_details = traceback.format_exc()
        error_stream = BytesIO(f"Критическая ошибка на сервере при генерации Excel:\n{error_details}".encode('utf-8'))
        error_stream.seek(0)
        return StreamingResponse(
            error_stream,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=server_error_log.txt"}
        )


# --- ЭНДПОИНТЫ АДМИНИСТРИРОВАНИЯ ---

@app.post("/api/admin/create_user")
def create_user(full_name: str, role: str = "employee", db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.full_name == full_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Сотрудник с таким ФИО уже зарегистрирован")
    new_user = models.User(full_name=full_name, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Сотрудник успешно создан!", "user_id": new_user.id}

@app.post("/api/admin/seed_test_data")
def seed_test_data(db: Session = Depends(database.get_db)):
    if db.query(models.User).count() > 0:
        return {"message": "База данных уже содержит пользователей"}
    test_users = [
        models.User(full_name="Иванов Иван Иванович", role="employee"),
        models.User(full_name="Петров Петр Петрович", role="employee"),
        models.User(full_name="Сидоров Алексей Владимирович", role="employee"),
        models.User(full_name="Смирнова Анна Сергеевна", role="accountant")
    ]
    db.add_all(test_users)
    db.commit()
    return {"message": "4 тестовых сотрудника успешно добавлены в базу!"}


# --- ЭНДПОИНТ ЧЕКИНА СМАРТФОНА ---

@app.post("/api/checkin")
def employee_checkin(user_id: int, lat: float, lon: float, qr_code: str, db: Session = Depends(database.get_db)):
    employee = db.query(models.User).filter(models.User.id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Ошибка: Сотрудник с таким ID не найден в системе!")
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Некорректные GPS-координаты")
    
    distance = calculate_distance(lat, lon, OFFICE_LAT, OFFICE_LON)
    is_gps_valid = distance <= ALLOWED_RADIUS_METERS
    
    expected_qr = get_current_qr_code()
    time_window_prev = int((time.time() - 30) // 30)
    sig_prev = hmac.new(QR_SECRET_KEY, str(time_window_prev).encode(), hashlib.sha256).hexdigest()
    expected_qr_prev = str(int(sig_prev, 16) % 1000000).zfill(6)
    
    is_qr_valid = (qr_code == expected_qr) or (qr_code == expected_qr_prev)
    total_valid = is_gps_valid and is_qr_valid
    
    new_checkin = models.CheckIn(
        user_id=user_id, latitude=lat, longitude=lon, is_valid=total_valid, verification_method="gps_and_qr"
    )
    db.add(new_checkin)
    db.commit()
    db.refresh(new_checkin)
    
    if not is_gps_valid:
        raise HTTPException(status_code=400, detail="Вы слишком далеко от офиса!")
    if not is_qr_valid:
        raise HTTPException(status_code=400, detail="Действие QR-кода истекло! Отсканируйте свежий код.")
    
    return {"message": f"Привет, {employee.full_name}! Чекин успешно пройден.", "checkin_id": new_checkin.id}
