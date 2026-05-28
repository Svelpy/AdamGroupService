"""
Router para la Gestión Administrativa de Usuarios
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.models.user import User
from app.models.enums import Role, UserStatus
from app.schemas.user_schema import (
    UserResponse,
    UserUpdate,
    PaginatedResponse
)
from app.utils.dependencies import (
    get_current_user,
    get_current_admin,
    get_current_superadmin
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users Management"])


# Cuerpo para restablecer contraseñas administrativamente
class AdminResetPassword(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=100)


# Cuerpo para cambiar el estado administrativamente
class ChangeStatusBody(BaseModel):
    status: UserStatus


# Cuerpo para cambiar el rol administrativamente
class ChangeRoleBody(BaseModel):
    role: Role


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Registros por página"),
    q: Optional[str] = Query(None, description="Búsqueda de texto en nombre, apellido, email o username"),
    role: Optional[Role] = Query(None, description="Filtrar por rol"),
    status: Optional[UserStatus] = Query(None, description="Filtrar por estado del usuario"),
    current_admin: User = Depends(get_current_admin)
):
    """
    Lista usuarios con filtros y paginación (Solo Administradores).
    """
    result = await UserService.list_users(
        page=page,
        per_page=per_page,
        q=q,
        role=role,
        user_status=status
    )
    return result


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los detalles de un usuario por su ID.
    
    Un usuario común solo puede consultar su propio ID. Los administradores pueden consultar cualquiera.
    """
    # Si no es admin y quiere ver a otro usuario
    if str(current_user.id) != user_id and current_user.role not in [Role.ADMIN, Role.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver los detalles de este usuario"
        )
        
    return await UserService.get_user(user_id=user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Edita la información de un usuario (Acción Administrativa).
    
    Requiere que el actor posea una jerarquía estrictamente superior. 
    (No permite auto-modificación ni modificación entre rangos iguales/superiores).
    """
    return await UserService.update_user(
        user_id=user_id,
        update_data=update_data,
        actor=current_user
    )


@router.post("/{user_id}/avatar", response_model=UserResponse)
async def update_avatar(
    user_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la foto de perfil de un usuario (Acción Administrativa).
    
    Requiere que el actor posea una jerarquía estrictamente superior.
    """
    # Validar extensión básica
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo subido debe ser una imagen válida"
        )
        
    return await UserService.update_avatar(
        user_id=user_id,
        file=file,
        actor=current_user
    )


@router.patch("/{user_id}/status", response_model=UserResponse)
async def change_user_status(
    user_id: str,
    body: ChangeStatusBody,
    current_admin: User = Depends(get_current_admin)
):
    """
    Cambia el estado de cuenta de un usuario (Acción Administrativa).
    
    Requiere jerarquía estrictamente superior (impide autodesactivación y mismo nivel).
    """
    return await UserService.change_status(
        user_id=user_id,
        new_status=body.status,
        actor=current_admin
    )


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: str,
    body: ChangeRoleBody,
    current_superadmin: User = Depends(get_current_superadmin)
):
    """
    Cambia el rol de permisos de un usuario (Solo Superadministrador).
    
    Requiere jerarquía estrictamente superior.
    """
    return await UserService.change_role(
        user_id=user_id,
        new_role=body.role,
        actor=current_superadmin
    )


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    body: AdminResetPassword,
    current_admin: User = Depends(get_current_admin)
):
    """
    Restablece la contraseña de un usuario (Acción Administrativa).
    
    Requiere jerarquía estrictamente superior.
    """
    await UserService.reset_password(
        user_id=user_id,
        new_password=body.new_password,
        actor=current_admin
    )
    return {"detail": "Contraseña restablecida exitosamente"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """
    Elimina a un usuario (Acción Administrativa).
    
    - Si el actor es ADMIN → Borrado lógico (is_deleted = True).
    - Si el actor es SUPERADMIN → Borrado físico permanente de la BD.
    
    Requiere jerarquía estrictamente superior (impide auto-eliminación y mismo nivel).
    """
    await UserService.delete_user(user_id=user_id, actor=current_admin)
    return {"detail": "Usuario eliminado exitosamente"}
