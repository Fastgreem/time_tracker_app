import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import flet as ft
import requests

SERVER_URL = "http://localhost:8000/api/checkin"

def main(page: ft.Page):
    page.title = "Учет времени"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    
    status_text = ft.Text(
        value="Введите 6-значный код с экрана на входе", 
        size=14, 
        text_align=ft.TextAlign.CENTER
    )
    
    # Поле для ввода одноразового кода (симуляция сканирования QR)
    qr_input = ft.TextField(
        label="Код из QR-кода",
        text_align=ft.TextAlign.CENTER,
        width=200,
        max_length=6,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    def on_checkin_click(e):
        if not qr_input.value or len(qr_input.value) != 6:
            status_text.value = "❌ Введите ровно 6 цифр кода!"
            status_text.color = ft.colors.RED_700
            page.update()
            return

        status_text.value = "Проверка данных..."
        status_text.color = ft.colors.BLACK
        page.update()
        
        # Параметры запроса (правильный GPS офиса + введенный код)
        payload = {
            "user_id": 1,
            "lat": 55.7558,
            "lon": 37.6173,
            "qr_code": qr_input.value
        }
        
        try:
            response = requests.post(SERVER_URL, params=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status_text.value = f"🎉 {data['message']}"
                status_text.color = ft.colors.GREEN_700
                qr_input.value = ""  # Очищаем поле при успехе
            else:
                try:
                    error_detail = response.json().get("detail", "Ошибка")
                except:
                    error_detail = response.text
                status_text.value = f"❌ Отклонено:\n{error_detail}"
                status_text.color = ft.colors.RED_700
                
        except requests.exceptions.ConnectionError:
            status_text.value = "❌ Сервер бэкенда недоступен!"
            status_text.color = ft.colors.RED_700
            
        page.update()

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(name=ft.icons.QR_CODE_SCANNER_ROUNDED, size=50, color=ft.colors.BLUE),
                    ft.Text(value="Двойной контроль", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    qr_input,
                    status_text,
                    ft.ElevatedButton(
                        text="Подтвердить чекин", 
                        icon=ft.icons.LOCK_OPEN_ROUNDED,
                        on_click=on_checkin_click,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            padding=30,
            border_radius=10,
            border=ft.border.all(1, ft.colors.BLACK12),
            bgcolor=ft.colors.SURFACE_VARIANT,
            width=350,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
