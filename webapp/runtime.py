"""
webapp/runtime.py
Живое состояние Mini App, которое может меняться в рантайме (URL туннеля).
Отделено от settings, чтобы роутеры/бот читали актуальный URL даже если он
получен уже после старта (serveo выдаёт его через пару секунд после подключения).
"""
from typing import Optional, Any, Dict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from config import settings

_state = {"url": "", "bot": None}


def set_webapp_url(url: str) -> None:
    _state["url"] = url or ""


def get_webapp_url() -> str:
    """Актуальный публичный URL: рантайм-туннель важнее статического из .env."""
    return _state["url"] or settings.WEBAPP_URL or ""


def set_bot(bot) -> None:
    """Сохраняет экземпляр aiogram Bot, чтобы webapp-хэндлеры могли слать сообщения в чат."""
    _state["bot"] = bot


def get_bot():
    return _state["bot"]


def build_webapp_url(path: str = "", base: Optional[str] = None, **query: Any) -> str:
    """Собирает корректный URL к Mini App, аккуратно обрабатывая уже существующие
    query-параметры в базовом URL.

    Примеры:
      build_webapp_url("/cert")
      build_webapp_url("cert", take=123)
      build_webapp_url()  # вернёт базовый URL без завершающего слеша

    Аргументы:
      path: добавляемый путь (с или без ведущего "/"). Если пустая строка — возвращается
            базовый URL без "лишнего" завершающего слеша в path.
      base: опционально можно передать базовый URL явно. Если не указан, берётся
            runtime.get_webapp_url().
      **query: дополнительные query-параметры, которые будут объединены с уже
               существующими в base (при конфликте — значения из **query перезапишут
               существующие).
    """
    base_url = base or get_webapp_url()
    if not base_url:
        return ""

    parts = urlsplit(base_url)
    scheme, netloc, base_path, base_query, fragment = parts

    # Нормализуем путь и добавляем новый
    add_path = (path or "")
    if add_path and not add_path.startswith("/"):
        add_path = "/" + add_path

    # Нормализация базового пути: убрать лишние слеши, но сохранить корень
    if base_path in ("", "/"):
        norm_base = base_path
    else:
        norm_base = base_path.rstrip("/")

    if not add_path:
        # Если не добавляем путь — возвращаем базовый URL без завершающего слеша
        new_path = "" if norm_base in ("", "/") else norm_base
    else:
        if norm_base in ("", "/"):
            new_path = add_path
        else:
            new_path = norm_base + add_path

    # Объединяем query-параметры (существующие + новые)
    existing_q = dict(parse_qsl(base_query, keep_blank_values=True))
    # Преобразуем входящие query значения в строки (urllib ожидает str)
    incoming_q: Dict[str, str] = {k: str(v) for k, v in query.items() if v is not None}
    merged = {**existing_q, **incoming_q}
    new_query = urlencode(merged, doseq=True)

    return urlunsplit((scheme, netloc, new_path, new_query, fragment))
