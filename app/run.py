import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.api import router
from app.bot import process_update, run_bot_webhook
from app.config import RESET, TELEGRAM_BOT_TOKEN
from app.infra.admin import Admin
from app.infra.database.session import engine, run_database
from app.services.event_checker import EventChecker
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse


async def on_startup(_):
    await run_database(RESET)

    if TELEGRAM_BOT_TOKEN:
        await run_bot_webhook()

    checker = EventChecker()
    await checker.start()

    yield

    checker.scheduler.shutdown()


app = FastAPI(lifespan=on_startup)
app.add_api_route(
    "/webhook", endpoint=process_update, methods=["post"], include_in_schema=False
)
app.include_router(router)

admin = Admin(base_url="/api/admin")
admin.init(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    message = exc._errors[0].get("ctx", {}).get("error") or "Ошибка в данных запроса"
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({"status": "error", "message": str(message)}),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"status": "error", "message": exc.detail}),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, forwarded_allow_ips="*")
