from typing import Optional, Any
from app.models.base import BaseDocument
from pymongo import IndexModel, ASCENDING

class ErrorLog(BaseDocument):
    status: str = "error"
    message: str                        # Mensaje del error
    stack: str                          # Stack trace / traceback
    
    #Informacion de la peticion
    path: Optional[str] = None         
    method: Optional[str] = None       
    ip_address: Optional[str] = None    
    user_agent: Optional[str] = None    
    
    #Informacion del usuario
    user_id: Optional[str] = None 

    class Settings:
        name = "errors"
        indexes = [
            IndexModel(
                [("created_at", ASCENDING)],
                expireAfterSeconds=2592000
            )
        ]