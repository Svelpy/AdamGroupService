from typing import Optional, List
from datetime import datetime
from pydantic import Field
from beanie import Indexed, PydanticObjectId
from pymongo import IndexModel, ASCENDING, DESCENDING
from .base import BaseDocument

class Collection(BaseDocument):
    # --- Datos de Identificación ---
    name: str = Field(..., min_length=2, max_length=120)
    slug: Indexed(str, unique=True)  # URL única (ej: 'join-life', 'winter-campaign-26')
    description: Optional[str] = Field(None, max_length=1000)
    
    # --- Visuales Adaptativos (Caso de éxito: Optimización Mobile) ---
    # Zara maneja banners separados. Forzar al móvil a descargar banners gigantes de desktop
    # arruina el rendimiento y baja el puntaje en Google PageSpeed.
    banner_desktop_url: Optional[str] = None
    banner_mobile_url: Optional[str] = None
    thumbnail_url: Optional[str] = None      # Imagen miniatura para usar en listados o sliders
    
    # --- Relación de Productos (Muchos a Muchos) ---
    # Guardar una lista de ObjectIds de productos directamente es el estándar NoSQL
    # para colecciones de tamaño mediano (menos de 1,000 productos).
    product_ids: List[PydanticObjectId] = Field(default_factory=list)
    
    # --- Programación y Temporalidad (Caso de éxito: Automatización de Campañas) ---
    # Permite al equipo de marketing programar colecciones navideñas o de rebajas de verano.
    # El backend las habilitará automáticamente en las fechas seleccionadas.
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # --- Visibilidad y Curación ---
    is_active: bool = True
    is_featured: bool = False  # Si se destaca en la página de inicio (Home)
    display_order: int = Field(0, description="Orden de prioridad en carruseles o secciones")
    
    # --- SEO Metadata ---
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    class Settings:
        name = "collections"
        indexes = [
            # Índice para renderizar sliders activos en la página principal de forma óptima
            IndexModel([("is_active", ASCENDING), ("is_featured", ASCENDING), ("display_order", ASCENDING)]),
            # Índice para verificar la programación temporal en segundo plano
            IndexModel([("start_date", ASCENDING), ("end_date", ASCENDING)])
        ]
        
    def __repr__(self):
        return f"<Collection {self.slug} (Featured: {self.is_featured})>"
    
    def __str__(self):
        return self.name