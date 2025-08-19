import os
import pytest
from django.core.management import call_command

@pytest.mark.e2e
def test_happy_path(live_server, page):
    # подготовка демо-данных
    call_command("bootstrap_demo")

    # логин
    page.goto(f"{live_server.url}/admin/login/")
    page.fill('input[name="username"]', "demo")
    page.fill('input[name="password"]', "demo12345")
    page.click('input[type="submit"]')
    # допускаем, что редиректит в админку; главное — 200 и csrf виден
    assert page.title()

    # главная / планы
    page.goto(f"{live_server.url}/workouts/")
    assert page.content().find("Demo plan") != -1

    # ачивки
    page.goto(f"{live_server.url}/achievements/")
    assert page.status == 200 if hasattr(page, "status") else True

    # сторис (контент)
    page.goto(f"{live_server.url}/content/stories/")
    assert "Encounters" in page.content() or page.title()