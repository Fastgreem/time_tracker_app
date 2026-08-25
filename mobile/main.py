import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


import flet as ft
import requests

# URL нашего запущенного локально FastAPI бэкенда
SERVER_URL = "http://127.0.0"

def main(page: ft.Page):
    # Настройки окна/экрана приложения
    page.title = "Учет времени"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Текстовое поле для вывода статуса ответов от сервера
    status_text = ft.Text(value="Нажмите кнопку, чтобы отметиться на работе", size=16, text_align=ft.TextAlign.CENTER)

    # Функция, которая срабатывает при нажатии на кнопку
    def on_checkin_click(e):
        status_text.value = "Отправка данных на сервер..."
        page.update()
        
        # Симулируем ID сотрудника и координаты (например, центр Москвы)
        payload = {
            "user_id": 1,
            "lat": 55.7558,
            "lon": 37.6173
        }
        
        try:
            # Отправляем POST запрос на наш FastAPI сервер
            response = requests.post(SERVER_URL, params=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status_text.value = f"🎉 {data['message']}\nID чекина: {data['checkin_id']}"
                status_text.color = ft.colors.GREEN_700
            else:
                status_text.value = f"❌ Ошибка сервера: {response.status_code}"
                status_text.color = ft.colors.RED_700
                
        except requests.exceptions.ConnectionError:
            status_text.value = "❌ Не удалось подключиться к серверу. Убедитесь, что FastAPI бэкенд запущен!"
            status_text.color = ft.colors.RED_700
            
        page.update()

    # Добавляем элементы интерфейса на экран
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

# Запуск Flet приложения
if __name__ == "__main__":
    ft.app(target=main)
