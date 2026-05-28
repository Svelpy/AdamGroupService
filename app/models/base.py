from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from beanie import Document, before_event, Save, Replace, Update
from pydantic import Field

class BaseDocument(Document):
    """
    Modelo base que extiende Beanie Document.
    Incluye campos de auditoría automática.
    """
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None 
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None 
    
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None 

    class Settings:
        # NO usar is_root=True para permitir que cada modelo tenga su propia colección
        use_state_management = True  # Habilita hooks de ciclo de vida que esto es una clase base abstracta

    @before_event([Save, Replace, Update])
    def pre_save(self):
        """
        Hook que se ejecuta automáticamente antes de guardar/actualizar.
        Actualiza el campo updated_at y genera nueva revisión.
        """
        self.updated_at = datetime.utcnow()
        self.revision_id = uuid4()  # Genera nueva versión en cada cambio
