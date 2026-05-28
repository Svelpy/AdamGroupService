from fastapi import FastAPI,Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core import database as db_module

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup y shutdown"""
    # Startup
    logger.info("🚀 Iniciando Aplicación...")
    await connect_to_mongo()
    logger.info("✅ Aplicación lista!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando aplicación...")
    await close_mongo_connection()
    logger.info("👋 Aplicación cerrada")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    #Si estamos en modo debug se muestra la documentacion, si no no se muestra 
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Configurar Rate Limiting
# El limiter se define en app/utils/limiter.py para evitar importaciones circulares
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Configurar CORS — DEBUG=True usa DEV_ORIGINS, DEBUG=False usa ALLOWED_ORIGINS (ambos desde .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirige automáticamente a la documentación interactiva en desarrollo"""
    if settings.DEBUG:
        return RedirectResponse(url="/docs")
    return {"message": "Svelpy API", "status": "active"}


@app.get("/health", tags=["Health"])
async def health_check(response: Response):
    """
    Endpoint de salud operativa (Readiness Probe).
    Verifica que la base de datos responda antes de retornar 200.
    """
    health_status = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "disconnected"
    }
    
    try:
        # Pinguemos a la base de datos para verificar conexión real
        if db_module.mongodb_client is not None:
            await db_module.mongodb_client.admin.command('ping')
            health_status["database"] = "connected"
            return health_status
        else:
            raise Exception("Cliente de base de datos no inicializado")
            
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return health_status


# Registrar routers
from app.routers import auth, users

app.include_router(auth.router)
app.include_router(users.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
