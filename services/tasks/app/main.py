from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_db, init_db

from app.admin.routes import admin_router
from app.tasks.routes import router as tasks_router
from app.questions.routes import router as questions_router
from app.submissions.routes import router as submissions_router
from app.sandbox.routes import router as sandbox_router
from app.reviews.routes import router as reviews_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    init_db()
    yield
    # Shutdown
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

app.include_router(admin_router)
app.include_router(tasks_router)
app.include_router(questions_router)
app.include_router(submissions_router)
app.include_router(sandbox_router)
app.include_router(reviews_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
