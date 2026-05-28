"""
Configuración de la aplicación
Variables de entorno y configuraciones globales
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación usando variables de entorno"""
    
    # App
    APP_NAME: str = "Proyect_Service_API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = """API para gestionar usuarios"""
    DEBUG: bool = False

    
    # MongoDB Atlas
    MONGODB_URL: str
    MONGODB_DB_NAME: str 
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES_DEBUG: int = 1440  # 1 día para desarrollo
    ACCESS_TOKEN_EXPIRE_MINUTES_PROD: int = 180    # 3 horas para producción
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """
        Retorna el tiempo de expiración del token según el modo DEBUG

        """
        if self.DEBUG:
            return self.ACCESS_TOKEN_EXPIRE_MINUTES_DEBUG
        return self.ACCESS_TOKEN_EXPIRE_MINUTES_PROD
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_FOLDER_NAME: str
    
    # CORS — Orígenes de desarrollo (DEBUG=True)
    DEV_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175"
    # CORS — Orígenes de producción (DEBUG=False)
    ALLOWED_ORIGINS: str = None #Definido solo en .env

    @property
    def CORS_ORIGINS_LIST(self) -> list:
        """
        Retorna la lista de orígenes CORS según el modo:

        """
        if self.DEBUG:
            return [o.strip() for o in self.DEV_ORIGINS.split(",") if o.strip()]

        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia singleton de Settings
settings = Settings()
