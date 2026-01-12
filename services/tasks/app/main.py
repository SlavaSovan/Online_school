from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

# from app.auth.routes import router as auth_router


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url=settings.API_PREFIX,
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.CORS_ORIGINS,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
