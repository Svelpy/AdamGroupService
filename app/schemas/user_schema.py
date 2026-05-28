"""
Schemas Pydantic para Usuario
Validación y serialización de datos de usuarios
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, TypeVar, Generic, List
from datetime import datetime
import re
from beanie import PydanticObjectId
from app.models.enums import Role, UserStatus, AuthProvider

# Generic type for pagination
T = TypeVar('T')


class UserBase(BaseModel):
    """Schema base para Usuario"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=80)
    lastname: str = Field(..., min_length=2, max_length=80)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone_number: Optional[str] = Field(None, pattern=r'^\+\d{5,15}$')
    birth_date: Optional[datetime] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'El username solo puede contener letras, números, guiones (-) y guiones bajos (_)'
            )
        return v

    @field_validator('name', 'lastname')
    @classmethod
    def validate_names(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s'-]+$", v):
            raise ValueError('Solo se permiten letras, espacios, guiones y apóstrofes')
        return v


# ---------------------------------------------------------------------------
# Mixin de contraseña reutilizable
# ---------------------------------------------------------------------------

class PasswordValidationMixin(BaseModel):
    """Mixin para validación de contraseñas"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


# ---------------------------------------------------------------------------
# Schemas de escritura (entrada de datos)
# ---------------------------------------------------------------------------

class UserSelfRegister(UserBase, PasswordValidationMixin):
    """
    Schema para auto-registro público (solo USER).
    No permite elegir rol — siempre se asigna Role.USER.
    """
    pass


class UserCreate(UserBase, PasswordValidationMixin):
    """
    Schema para crear usuario desde el panel administrativo.
    Permite asignar un rol específico.
    """
    role: Role = Role.USER


class UserUpdate(BaseModel):
    """
    Schema para actualizar datos del usuario (PATCH parcial).
    Todos los campos son opcionales.
    """
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=80)
    lastname: Optional[str] = Field(None, min_length=2, max_length=80)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone_number: Optional[str] = Field(None, pattern=r'^\+\d{5,15}$')
    birth_date: Optional[datetime] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'El username solo puede contener letras, números, guiones (-) y guiones bajos (_)'
            )
        return v

    @field_validator('name', 'lastname')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s'-]+$", v):
            raise ValueError('Solo se permiten letras, espacios, guiones y apóstrofes')
        return v


# ---------------------------------------------------------------------------
# Schemas de lectura (salida de datos)
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """
    Schema de respuesta de usuario (nunca incluye contraseña ni datos sensibles).
    Serializa directamente desde el documento Beanie usando from_attributes=True.
    """
    id: PydanticObjectId
    email: EmailStr
    name: str
    lastname: str
    username: Optional[str] = None
    role: Role
    status: UserStatus
    email_verified: bool
    auth_provider: AuthProvider
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "usuario@adamgroup.com.bo",
                "name": "María",
                "lastname": "García López",
                "username": "mariagarcia",
                "role": "USER",
                "status": "ACTIVE",
                "email_verified": True,
                "auth_provider": "LOCAL",
                "avatar_url": None,
                "phone_number": "+59170012345",
                "birth_date": "1990-01-01T00:00:00Z",
                "created_at": "2025-12-19T14:00:00Z",
                "updated_at": "2025-12-19T14:00:00Z",
                "created_by": None,
                "updated_by": None
            }
        }
    )


# ---------------------------------------------------------------------------
# Schemas de autenticación
# ---------------------------------------------------------------------------

class UserLogin(BaseModel):
    """Schema de entrada para login con email y contraseña"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema de respuesta al autenticarse exitosamente"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Schema de cambio de contraseña
# ---------------------------------------------------------------------------

class ChangePasswordSchema(BaseModel):
    """Schema para cambiar la contraseña del usuario autenticado"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


# ---------------------------------------------------------------------------
# Schema genérico de paginación
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico de respuesta paginada. Uso: PaginatedResponse[UserResponse]"""
    total: int          # Total de registros encontrados
    page: int           # Página actual (empieza en 1)
    per_page: int       # Registros por página
    total_pages: int    # Total de páginas
    data: List[T]       # Lista de objetos tipados
