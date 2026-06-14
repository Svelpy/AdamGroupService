from fastapi import APIRouter, Depends, UploadFile, File, status, Query
from typing import Optional

from app import models, schemas
from app.utils.dependencies import (
    get_current_user,
    get_current_admin,
    get_current_superadmin
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users Management"])





@router.get("", response_model=schemas.user.PaginatedResponse[schemas.user.UserResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Registros por página"),
    q: Optional[str] = Query(None, description="Búsqueda de texto en nombre, apellido, email o username"),
    role: Optional[models.Role] = Query(None, description="Filtrar por rol"),
    status: Optional[models.UserStatus] = Query(None, description="Filtrar por estado del usuario"),
    current_admin: models.User = Depends(get_current_admin)
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


@router.get("/{user_id}", response_model=schemas.user.UserResponse)
async def get_user(
    user_id: str,
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Obtiene los detalles de un usuario por su ID.(Solo Administradores).
    """
       
    return await UserService.get_user(user_id=user_id)


@router.patch("/{user_id}", response_model=schemas.user.UserResponse)
async def update_user(
    user_id: str,
    update_data: schemas.user.UserUpdate,
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Edita la información de un usuario (Acción Administrativa).
    """
    return await UserService.update_user(
        user_id=user_id,
        update_data=update_data,
        actor=current_admin
    )


@router.post("/{user_id}/avatar", response_model=schemas.user.UserResponse)
async def update_avatar(
    user_id: str,
    file: UploadFile = File(...),
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Actualiza la foto de perfil de un usuario (Acción Administrativa).
    """

    return await UserService.update_avatar(
        user_id=user_id,
        file=file,
        actor=current_admin
    )


@router.patch("/{user_id}/status", response_model=schemas.user.UserResponse)
async def change_user_status(
    user_id: str,
    body: schemas.user.ChangeStatusBody,
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Cambia el estado de cuenta de un usuario (Acción Administrativa).
    """
    return await UserService.change_status(
        user_id=user_id,
        new_status=body.status,
        actor=current_admin
    )


@router.patch("/{user_id}/role", response_model=schemas.user.UserResponse)
async def change_user_role(
    user_id: str,
    body: schemas.user.ChangeRoleBody,
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Cambia el rol de permisos de un usuario (Acción Administrativa).
    
    """
    return await UserService.change_role(
        user_id=user_id,
        new_role=body.role,
        actor=current_admin
    )


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    body: schemas.user.AdminResetPassword,
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Restablece la contraseña de un usuario (Acción Administrativa).
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
    current_admin: models.User = Depends(get_current_admin)
):
    """
    Elimina a un usuario (Acción Administrativa).
    """
    await UserService.delete_user(user_id=user_id, actor=current_admin)
    return {"detail": "Usuario eliminado exitosamente"}


@router.patch("/profile", response_model=schemas.user.UserResponse)
async def update_profile(
    data: schemas.user.UserUpdate,
    current_user: models.User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado actualizar sus propios datos personales.
    """
    return await UserService.update_profile(update_data=data, actor=current_user)


@router.post("/profile/avatar", response_model=schemas.user.UserResponse)
async def update_avatar_self(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado subir o actualizar su propia foto de perfil.
    """
    return await UserService.update_avatar_self(file=file, actor=current_user)
