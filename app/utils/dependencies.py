"""
Dependencies para FastAPI
Funciones reutilizables para autenticación y autorización
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from bson import ObjectId

from app.models.user import User
from app.utils.security import decode_access_token

# Esquema de autenticación Bearer
# auto_error=False permite que el header sea opcional (para endpoints públicos)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Obtener usuario actual desde el token JWT
    
    Dependency para endpoints protegidos
    
    Raises:
        HTTPException 401: Si el token es inválido o el usuario no existe
    """
    # Verificar que se proporcionó el token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Decodificar token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener user_id del payload
    user_id: str = payload.get("user_id")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuario en la base de datos
    try:
        user = await User.get(ObjectId(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user is None or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o no verificado"
        )
    
    return user


from app.models.enums import Role, UserStatus

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Verificar que el usuario actual sea ADMIN o SUPERADMIN
    """
    if current_user.role not in [Role.ADMIN, Role.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    
    return current_user


async def get_current_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """
    Verificar que el usuario actual sea SUPERADMIN
    """
    if current_user.role != Role.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el SUPERADMIN puede realizar esta acción"
        )
    
    return current_user



async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Obtener usuario actual si existe, sino retornar None
    
    Útil para endpoints que funcionan con o sin autenticación
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
