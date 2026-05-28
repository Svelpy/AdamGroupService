"""
Servicio para lógica de negocio de Usuarios
Maneja CRUD, jerarquía de roles, avatares y gestión de estado
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, UploadFile, status
from datetime import datetime
import re
import math

from app.models.user import User
from app.models.enums import Role, UserStatus
from app.schemas.user_schema import UserUpdate
from app.services.cloudinary_service import cloudinary_service
from app.utils.security import hash_password


class UserService:

    # ─────────────────────────────────────────────
    # HELPERS INTERNOS
    # ─────────────────────────────────────────────

    # Mapa de jerarquía: menor número = mayor poder
    ROLE_HIERARCHY = {
        Role.SUPERADMIN: 0,
        Role.ADMIN: 1,
        Role.MANAGER: 2,
        Role.STAFF: 3,
        Role.USER: 4,
        Role.GUEST: 5,
    }

    @staticmethod
    def _check_hierarchy(actor: User, target: User):
        """
        Valida que el actor tenga jerarquía estricta sobre el target.
        Lanza HTTP 403 si el nivel del actor es >= al del target.
        """
        actor_level = UserService.ROLE_HIERARCHY.get(actor.role, 99)
        target_level = UserService.ROLE_HIERARCHY.get(target.role, 99)

        if actor_level >= target_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para gestionar a este usuario"
            )

    @staticmethod
    async def _get_active_user(user_id: str) -> User:
        """
        Obtiene un usuario por ID.
        Lanza 404 si no existe o fue eliminado lógicamente.
        """
        from bson import ObjectId

        try:
            user = await User.get(ObjectId(user_id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no existente"
            )

        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario eliminado lógicamente"
            )

        return user

    # ─────────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────────

    @staticmethod
    async def list_users(
        page: int = 1,
        per_page: int = 10,
        q: Optional[str] = None,
        role: Optional[Role] = None,
        user_status: Optional[UserStatus] = None,
    ) -> Dict[str, Any]:
        """Lista usuarios con paginación y filtros opcionales."""
        from beanie.operators import Or

        query = User.find(User.is_deleted == False)

        # Búsqueda por texto en email, username, name y lastname
        if q:
            safe_q = re.escape(q)
            regex = {"$regex": safe_q, "$options": "i"}
            query = query.find(Or(
                User.email == regex,
                User.username == regex,
                User.name == regex,
                User.lastname == regex,
                User.phone_number == regex
            ))

        if role:
            query = query.find(User.role == role)

        if user_status is not None:
            query = query.find(User.status == user_status)

        total_count = await query.count()
        skip = (page - 1) * per_page
        users = await query.skip(skip).limit(per_page).to_list()
        total_pages = math.ceil(total_count / per_page) if per_page > 0 else 0

        return {
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": users,
        }

    @staticmethod
    async def get_user(user_id: str) -> User:
        """Obtiene un usuario activo por ID."""
        return await UserService._get_active_user(user_id)

    @staticmethod
    async def update_user(user_id: str, update_data: UserUpdate, actor: User) -> User:
        """Actualiza datos textuales del usuario con validación de jerarquía y unicidad."""
        user = await UserService._get_active_user(user_id)
        
        # Validación estricta: Mismo rango y autogestión no están permitidos en rutas administrativas
        UserService._check_hierarchy(actor, user)

        # Validar unicidad de username
        if update_data.username is not None and update_data.username != user.username:
            existing = await User.find_one(User.username == update_data.username)
            if existing:
                raise HTTPException(status_code=400, detail="El username ya está en uso")

        # Validar unicidad de email
        if update_data.email is not None and update_data.email != user.email:
            existing_email = await User.find_one(User.email == update_data.email)
            if existing_email:
                raise HTTPException(status_code=400, detail="El email ya está en uso")

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)

        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def update_avatar(user_id: str, file: UploadFile, actor: User) -> User:
        """Actualiza el avatar del usuario subiendo la imagen a Cloudinary (ruta administrativa)."""
        user = await UserService._get_active_user(user_id)
        
        # Validación estricta: Mismo rango y autogestión no están permitidos en rutas administrativas
        UserService._check_hierarchy(actor, user)

        avatar_url = await cloudinary_service.upload_image(file, folder="avatars")
        user.avatar_url = avatar_url
        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def reset_password(user_id: str, new_password: str, actor: User) -> None:
        """Restablece la contraseña de un usuario (acción administrativa)."""
        user = await UserService._get_active_user(user_id)

        # Restablecer contraseña requiere jerarquía estricta
        UserService._check_hierarchy(actor, user)

        user.password_hash = hash_password(new_password)
        user.updated_by = str(actor.id)
        await user.save()

    @staticmethod
    async def change_status(user_id: str, new_status: UserStatus, actor: User) -> User:
        """
        Cambia el estado del usuario al nuevo estado especificado.
        Usa el enum UserStatus.
        """
        user = await UserService._get_active_user(user_id)

        # La jerarquía ya maneja si intento cambiar el estado de mi propia cuenta (mismo nivel -> falla)
        UserService._check_hierarchy(actor, user)

        user.status = new_status
        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def change_role(user_id: str, new_role: Role, actor: User) -> User:
        """Cambia el rol de un usuario."""
        if new_role == Role.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede asignar el rol SUPERADMIN"
            )

        user = await UserService._get_active_user(user_id)

        # La jerarquía ya maneja si intento cambiar mi propio rol (mismo nivel -> falla)
        UserService._check_hierarchy(actor, user)

        user.role = new_role
        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def delete_user(user_id: str, actor: User) -> None:
        """
        Elimina un usuario:
        - ADMIN → Soft delete (borrado lógico).
        - SUPERADMIN → Hard delete (borrado físico permanente).
        """
        user = await UserService._get_active_user(user_id)

        # La jerarquía ya maneja si intento eliminar mi propia cuenta (mismo nivel -> falla)
        UserService._check_hierarchy(actor, user)

        if actor.role == Role.ADMIN:
            # Soft delete
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            user.deleted_by = str(actor.id)
            user.updated_by = str(actor.id)
            await user.save()

        elif actor.role == Role.SUPERADMIN:
            # Hard delete físico
            await user.delete()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para eliminar usuarios"
            )


# Instancia global del servicio
user_service = UserService()
