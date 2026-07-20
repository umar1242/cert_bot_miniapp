"""
webapp/server.py
Встроенный aiohttp-сервер Mini App: отдаёт SPA (webapp/static/index.html)
и JSON API. Живёт в том же event loop, что и polling бота.

Теперь корень редиректит на /cert — планер удалён.
"""
import json
import logging
from pathlib import Path

from aiohttp import web

from config import settings
from db.base import AsyncSessionFactory
from webapp import cert_api, cert_attempt_api
from webapp.auth import validate_init_data

logger = logging.getLogger(__name__)

_STATIC = Path(__file__).parent / "static"
_CERT_APP_DIST = _STATIC / "cert-app"


# ---------------------------------------------------------------------------
# Авторизация запроса
# ---------------------------------------------------------------------------

def _user_id(request: web.Request) -> int | None:
    """user_id из проверенного initData (заголовок X-Init-Data) или dev-обход."""
    init_data = request.headers.get("X-Init-Data", "")
    user = validate_init_data(init_data, settings.BOT_TOKEN)
    if user:
        return int(user["id"])
    if settings.WEBAPP_DEV_USER_ID:
        return int(settings.WEBAPP_DEV_USER_ID)
    return None


def _require_user(handler):
    async def wrapper(request: web.Request):
        uid = _user_id(request)
        if uid is None:
            return web.json_response({"error": "unauthorized"}, status=401)
        request["user_id"] = uid
        return await handler(request)
    return wrapper


async def _body(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, Exception):
        return {}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def index(request: web.Request) -> web.Response:
    # Редирект на сертификат
    raise web.HTTPFound('/cert')


async def cert_index(request: web.Request) -> web.Response:
    index_file = _CERT_APP_DIST / "index.html"
    if not index_file.exists():
        return web.Response(
            text="Cert mini app не собран. Выполните: cd webapp/frontend-cert && npm install && npm run build",
            status=503,
        )
    return web.FileResponse(index_file)


def create_app() -> web.Application:
    app = web.Application()
    # Корень теперь перенаправляет на /cert
    app.router.add_get("/", index)
    app.router.add_get("/punnett", punnett_index)
    # Роуты сертификата
    cert_api.register_routes(app)
    cert_attempt_api.register_routes(app)
    app.router.add_get("/cert", cert_index)
    app.router.add_get("/cert/", cert_index)
    if (_CERT_APP_DIST / "assets").exists():
        app.router.add_static("/cert/assets/", _CERT_APP_DIST / "assets", name="cert-assets")
    app.router.add_static("/static/", _STATIC)
    return app


async def punnett_index(request: web.Request) -> web.Response:
    return web.FileResponse(_STATIC / "punnett" / "index.html")


async def start_webapp() -> web.AppRunner | None:
    """Поднимает сервер в текущем loop. Возвращает runner для cleanup (или None)."""
    if not settings.WEBAPP_ENABLED:
        logger.info("Mini App отключён (WEBAPP_ENABLED=false)")
        return None
    runner = web.AppRunner(create_app())
    await runner.setup()
    site = web.TCPSite(runner, settings.WEBAPP_HOST, settings.WEBAPP_PORT)
    await site.start()
    logger.info(
        "Mini App слушает http://%s:%s  (public: %s)",
        settings.WEBAPP_HOST, settings.WEBAPP_PORT, settings.WEBAPP_URL or "—",
    )
    return runner
