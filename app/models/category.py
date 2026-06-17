from typing import Optional
from pydantic import Field
from beanie import Indexed, PydanticObjectId
from pymongo import IndexModel, ASCENDING
from .base import BaseDocument

class Category(BaseDocument):
    # --- Datos de Identificación ---
    name: str = Field(..., min_length=2, max_length=100)
    slug: Indexed(str, unique=True)  # Único e indexado para URLs amigables (ej: 'blazers')
    description: Optional[str] = Field(None, max_length=500)
    
    # --- Estructura de Árbol (Recursividad) ---
    parent_id: Optional[PydanticObjectId] = None  # Si es None, es categoría raíz (ej: 'Mujer')
    
    # --- Activos Visuales ---
    image_url: Optional[str] = None   # Miniatura de la categoría para navegación visual
    icon_name: Optional[str] = None   # Nombre del icono (ej: 'shirt', 'mobile') para el frontend
    banner_url: Optional[str] = None  # Imagen de portada si la categoría tiene su propia landing
    
    # --- Configuración y Control ---
    is_active: bool = True
    display_order: int = Field(0, description="Orden de prioridad para ordenar en el menú")
    
    # --- SEO Metadata (Caso de éxito: El dolor de cabeza #1 en tiendas de producción) ---
    # Al incluir esto desde el día uno, evitas tener que parchar la base de datos después
    # para que Google indexe las páginas de categorías correctamente.
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    class Settings:
        name = "categories"
        indexes = [
            # Índice para buscar rápidamente categorías hijas de un padre
            IndexModel([("parent_id", ASCENDING)]),
            # Índice compuesto para ordenar de forma óptima el menú del frontend
            IndexModel([("parent_id", ASCENDING), ("display_order", ASCENDING)])
        ]
        
    def __repr__(self):
        return f"<Category {self.slug} (Parent: {self.parent_id})>"
    
    def __str__(self):
        return self.name