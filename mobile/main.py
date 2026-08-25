import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import flet as ft
import requests

# Пробуем использовать 'localhost' вместо '127.0.0.1'
SERVER_URL = "http://localhost:8000/api/checkin"

def main(page: ft.Page):
    page.title = "Учет времени"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    
    status_text = ft.Text(
        value="Нажмите кнопку, чтобы отметиться на работе", 
        size=16, 
        text_align=ft.TextAlign.CENTER
    )

    def on_checkin_click(e):
        status_text.value = "Отправка данных на сервер..."
        status_text.color = ft.colors.BLACK
        page.update()
        
        # Передаем базовые параметры
        payload = {
            "user_id": 1,
            "lat": 55.7558,
            "lon": 37.6173
        }
        
        try:
            # Отправляем POST-запрос на сервер
            response = requests.post(SERVER_URL, params=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status_text.value = f"🎉 {data['message']}\nID: {data['checkin_id']}"
                status_text.color = ft.colors.GREEN_700
            else:
                # Если сервер вернул ошибку (например, 400 из-за GPS)
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = response.text
                status_text.value = f"❌ Ошибка сервера ({response.status_code}):\n{error_detail}"
                status_text.color = ft.colors.RED_700
                
        except requests.exceptions.ConnectionError as err:
            # Выводим точную техническую причину, почему сеть заблокирована
            status_text.value = f"❌ Ошибка сети!\nСервер не ответил.\nТехнический лог: {str(err)[:60]}..."
            status_text.color = ft.colors.RED_700
            
        page.update()

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(name=ft.icons.LOCATION_ON_ROUNDED, size=50, color=ft.colors.BLUE),
                    ft.Text(value="Система КТУ и Табелей", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    status_text,
                    ft.ElevatedButton(
                        text="Я на работе", 
                        icon=ft.icons.GPS_FIXED,
                        on_click=on_checkin_click,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
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
