from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.auth.routes import router as auth_router
from app.core.database import close_db, init_db
from app.users.routes import (
    permissions_router,
    roles_router,
    users_router,
)
from app.auth.blacklist import token_blacklist


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    init_db()
    await token_blacklist.connect()
    yield
    # Shutdown
    await token_blacklist.close()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url=settings.API_PREFIX,
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Auth Service API",
        routes=app.routes,
    )

    token_url = "/auth/login/swagger"

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {"password": {"tokenUrl": token_url, "scopes": {}}},
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
