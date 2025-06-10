from fastapi import FastAPI
from app.api.routes import router
from app.core.logger import logger
import sys

logger.add(sys.stderr, level="DEBUG", backtrace=True, diagnose=True)

app = FastAPI(title="Tradient AI API")

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     raw = await request.body()
#     # Используем f-строки вместо плейсхолдеров
#     logger.error(f"Validation error on {request.method} {request.url.path}")
#     logger.error(f"Raw body: {raw!r}")
#     logger.error(f"Validation errors: {exc.errors()!r}")
#     return await request_validation_exception_handler(request, exc)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tradientai.tech"
        "https://7b41-81-19-137-222.ngrok-free.app",
        "http://localhost:3000",

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)



# @app.on_event("startup")
# async def list_routes():
#     from fastapi.routing import APIRoute
#     routes = [route.path for route in app.router.routes if isinstance(route, APIRoute)]
#     logger.info("Registered routes:\n" + "\n".join(routes))

logger = logger.bind(name="api")
logger.info("🌐 API backend запущен (Tradient AI)")
