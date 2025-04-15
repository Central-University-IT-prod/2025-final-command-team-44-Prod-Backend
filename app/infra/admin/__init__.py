import os

from fastapi import Request
from app.infra.admin.views import AdminView
from jinja2 import pass_context
from sqladmin import Admin as SQLAdmin
from sqladmin.authentication import AuthenticationBackend


class AdminSettings:
    USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    PASSWORD = os.environ.get("ADMIN_PASSWORD", "qwerty")

    SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "SECRET_KEY")
    STATIC_URL = os.environ.get("ADMIN_STATIC_URL")


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        if username != AdminSettings.USERNAME or password != AdminSettings.PASSWORD:
            return False

        request.session.update({"token": AdminSettings.SECRET_KEY})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if token != AdminSettings.SECRET_KEY:
            return False
        return True


class Admin:
    def __init__(
        self,
        title="Admin",
        logo_url=None,
        favicon_url=None,
        middlewares=None,
        debug=False,
        templates_dir="templates",
        base_url="/admin",
    ):
        self.authentication_backend = AdminAuth(secret_key=AdminSettings.SECRET_KEY)
        self.title = title
        self.logo_url = logo_url
        self.favicon_url = favicon_url
        self.middlewares = middlewares
        self.debug = debug
        self.templates_dir = templates_dir
        self.base_url = base_url

    @staticmethod
    @pass_context
    def url_for(context: dict, name: str, /, **path_params) -> str:
        request: Request = context.get("request")
        url = str(request.url_for(name, **path_params))

        if "/admin/statics/" in url and AdminSettings.STATIC_URL:
            return AdminSettings.STATIC_URL + path_params["path"]

        return url

    def init(self, app, engine):
        admin = SQLAdmin(
            app,
            engine,
            base_url=self.base_url,
            title=self.title,
            logo_url=self.logo_url,
            middlewares=self.middlewares,
            debug=self.debug,
            templates_dir=self.templates_dir,
            authentication_backend=self.authentication_backend,
        )
        admin.templates.env.globals["url_for"] = Admin.url_for

        for view in AdminView.__subclasses__():
            admin.add_view(view)
