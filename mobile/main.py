import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import flet as ft
import requests

# URL локального сервера FastAPI. При деплое здесь будет реальный IP сервера.
SERVER_URL = "http://localhost:8000"

def main(page: ft.Page):
    page.title = "Николь-Плаза: Учет времени"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 390  # Размеры экрана под стандартный смартфон
    page.window_height = 700
    page.window_resizable = False

    # --- ПЕРЕМЕННЫЕ ХРАНЕНИЯ СЕССИИ ---
    user_id_ref = {"value": None}
    user_name_ref = {"value": ""}

    # Элементы интерфейса, которые нужно обновлять динамически
    status_text = ft.Text(value="Загрузка системы...", size=14, text_align=ft.TextAlign.CENTER)
    welcome_text = ft.Text(value="", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

    # --- ОЧИСТКА ЭКРАНА И ПЕРЕКЛЮЧЕНИЕ ВИДОВ ---
    def show_screen(view_content):
        page.clean()
        page.add(
            ft.Container(
                content=view_content,
                padding=25,
                border_radius=12,
                border=ft.border.all(1, ft.colors.BLACK12),
                bgcolor=ft.colors.SURFACE_VARIANT,
                width=350,
            )
        )
        page.update()

    # --- ЛОГИКА ЭКРАНА 1: АВТОРИЗАЦИЯ ПО ID ---
    def build_auth_screen():
        id_input = ft.TextField(
            label="Личный ID сотрудника",
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=220
        )
        auth_status = ft.Text(value="Введите ID, выданный администратором", size=12, text_align=ft.TextAlign.CENTER)

        def on_login_click(e):
            if not id_input.value:
                auth_status.value = "❌ Поле не может быть пустым!"
                auth_status.color = ft.colors.RED_700
                page.update()
                return

            auth_status.value = "Проверка ID на сервере..."
            auth_status.color = ft.colors.BLACK
            page.update()

            try:
                # Стучимся на новый специальный эндпоинт проверки ID
                response = requests.get(f"{SERVER_URL}/api/auth/check_id", params={"user_id": int(id_input.value)}, timeout=4)
                
                if response.status_code == 200:
                    data = response.json()
                    user_id_ref["value"] = data["user_id"]
                    user_name_ref["value"] = data["full_name"]
                    
                    # Сохраняем ID локально в память телефона
                    page.client_storage.set("saved_user_id", data["user_id"])
                    
                    # Переходим в рабочую зону
                    build_work_screen()
                elif response.status_code == 404:
                    auth_status.value = "❌ Сотрудник с таким ID не найден в админке!"
                    auth_status.color = ft.colors.RED_700
                else:
                    auth_status.value = "❌ Ошибка сервера. Попробуйте позже."
                    auth_status.color = ft.colors.RED_700
            except Exception:
                auth_status.value = "❌ Ошибка связи с сервером бэкенда!"
                auth_status.color = ft.colors.RED_700
            page.update()

        return ft.Column(
            controls=[
                ft.Icon(name=ft.icons.ACCOUNT_CIRCLE_ROUNDED, size=60, color=ft.colors.BLUE_700),
                ft.Text(value="Авторизация", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                id_input,
                auth_status,
                ft.ElevatedButton(
                    text="Войти в систему",
                    icon=ft.icons.LOGIN_ROUNDED,
                    on_click=on_login_click,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )
    # --- ЛОГИКА ЭКРАНА 2: РАБОЧАЯ ЗОНА СМЕНЫ (ВХОД / ВЫХОД) ---
    def build_work_screen():
        # Считываем сохраненный ID
        current_uid = user_id_ref["value"] or page.client_storage.get("saved_user_id")
        
        # Переключатель типа действия: IN (Вход) или OUT (Выход)
        action_selector = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="IN", label="🟢 Открыть смену (Вход)"),
                    ft.Radio(value="OUT", label="🔴 Закрыть смену (Выход)"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            ),
            value="IN"  # По умолчанию выбран Вход
        )

        qr_input = ft.TextField(
            label="Код безопасности (6 цифр)",
            text_align=ft.TextAlign.CENTER,
            width=220,
            max_length=6,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        status_text.value = "Выберите действие и введите код"
        status_text.color = ft.colors.BLACK54

        def on_send_checkin(e):
            if not qr_input.value or len(qr_input.value) != 6:
                status_text.value = "❌ Введите ровно 6 цифр одноразового кода!"
                status_text.color = ft.colors.RED_700
                page.update()
                return

            status_text.value = "Передача данных контроля присутствия..."
            status_text.color = ft.colors.BLACK
            page.update()

            # Имитируем идеальные GPS-координаты объекта Николь-Плаза
            payload = {
                "user_id": current_uid,
                "lat": 55.7558,
                "lon": 37.6173,
                "qr_code": qr_input.value,
                "action_type": action_selector.value
            }

            try:
                response = requests.post(f"{SERVER_URL}/api/checkin", params=payload, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status_text.value = f"🎉 Успешно!\n{data['message']}"
                    status_text.color = ft.colors.GREEN_700
                    qr_input.value = ""  # Стираем использованный одноразовый код
                else:
                    try:
                        error_detail = response.json().get("detail", "Ошибка")
                    except:
                        error_detail = response.text
                    status_text.value = f"❌ Отклонено сервером:\n{error_detail}"
                    status_text.color = ft.colors.RED_700
            except Exception:
                status_text.value = "❌ Ошибка сети! Проверьте запуск сервера FastAPI."
                status_text.color = ft.colors.RED_700
            page.update()

        def on_logout(e):
            # Логика выхода из аккаунта: стираем локальную память телефона
            page.client_storage.remove("saved_user_id")
            user_id_ref["value"] = None
            show_screen(build_auth_screen())

        work_layout = ft.Column(
            controls=[
                ft.Icon(name=ft.icons.TIMER_OUTLINED, size=50, color=ft.colors.BLUE_700),
                ft.Text(value=f"Сотрудник ID: {current_uid}", size=16, weight=ft.FontWeight.W_500),
                ft.Divider(),
                action_selector,
                ft.Text(value="Скан динамического QR-кода:", size=12, color=ft.colors.BLACK45),
                qr_input,
                status_text,
                ft.ElevatedButton(
                    text="Отправить отметку времени",
                    icon=ft.icons.SEND_ROUNDED,
                    on_click=on_send_checkin,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.TextButton(
                    text="Выйти из аккаунта (Сброс ID)",
                    icon=ft.icons.LOGOUT_ROUNDED,
                    on_click=on_logout,
                    style=ft.ButtonStyle(color=ft.colors.RED_400)
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )
        show_screen(work_layout)

    # --- ТОЧКА ВХОДА ПРИ ЗАПУСКЕ ПРИЛОЖЕНИЯ ---
    # Проверяем, авторизован ли уже телефон (есть ли сохраненный ID в памяти устройства)
    saved_id = page.client_storage.get("saved_user_id")
    if saved_id is not None:
        user_id_ref["value"] = saved_id
        build_work_screen()
    else:
        show_screen(build_auth_screen())

if __name__ == "__main__":
    ft.app(target=main)
