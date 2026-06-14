from beanie import Indexed
from pymongo import IndexModel, ASCENDING
from pydantic import EmailStr
from typing import Optional
from datetime import datetime
from .base import BaseDocument
from .enums import Role, AuthProvider, UserStatus

class User(BaseDocument):
    # --- Datos Básicos ---
    email: Indexed(EmailStr, unique=True)  # Email único e indexado
    name: str                              # Nombre(s) — obligatorio
    lastname: str                          # Apellido(s) — obligatorio
    
    username: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[datetime] = None 

    avatar_url: Optional[str] = None
    #Auth
    password_hash: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    provider_user_id: Optional[str] = None
    email_verified: bool = False
    #Autorizacion  
    role: Role = Role.USER
    status: UserStatus = UserStatus.PENDING_VERIFICATION

    class Settings:
        name = "users" 
        indexes = [IndexModel([("username",ASCENDING)],unique=True,partialFilterExpression={"username": {"$type": "string"}})]
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    def __str__(self):
        return self.email
  