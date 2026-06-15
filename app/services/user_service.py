from typing import Optional, Dict, Any
from fastapi import UploadFile
from datetime import datetime
from bson import ObjectId
from beanie.operators import Or
import re
import math

from app import models, schemas
from app.services.cloudinary_service import cloudinary_service
from app.utils.security import hash_password
from app.utils.errors import AppException


class UserService:

    # ─────────────────────────────────────────────
    # HELPERS INTERNOS
    # ─────────────────────────────────────────────

    # Mapa de jerarquía: menor número = mayor poder
    ROLE_HIERARCHY = {
        models.Role.SUPERADMIN: 0,
        models.Role.ADMIN: 1,
        models.Role.MANAGER: 2,
        models.Role.STAFF: 3,
        models.Role.USER: 4,
        models.Role.GUEST: 5,
    }

    @staticmethod
    def _check_hierarchy(actor: models.User, target: models.User):
        """
        Valida que el actor tenga jerarquía estricta sobre el target.
        """
        actor_level = UserService.ROLE_HIERARCHY.get(actor.role, 99)
        target_level = UserService.ROLE_HIERARCHY.get(target.role, 99)

        if actor_level >= target_level:
            raise AppException("No tienes permisos para gestionar a este usuario", 403)

    @staticmethod
    async def _get_active_user(user_id: str) -> models.User:
        """
        Obtiene un usuario por ID.
        """
        # Validar formato del ObjectId sin tocar la base de datos
        if not ObjectId.is_valid(user_id):
            raise AppException("Usuario no existente", 404)
        # Consultar la base de datos
        user = await models.User.get(ObjectId(user_id))
        # Validar si el usuario existe
        if not user:
            raise AppException("Usuario no existente", 404)
        # Validar si está eliminado lógicamente
        if user.is_deleted:
            raise AppException("Usuario eliminado", 404)
        return user

    # ─────────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────────
    @staticmethod
    async def register_user(user_data: schemas.user.UserCreate, created_by: Optional[str] = None) -> models.User:
        """
        Registrar un nuevo usuario
        
        Args:
            user_data: Datos del usuario a crear
            created_by: ID del usuario creador
            
        Returns:
            Usuario creado
        """
        username = None
        if user_data.username:
            cleaned_username = user_data.username.strip().lower()
            if cleaned_username != "":
                username = cleaned_username
        # Verificar si el email ya existe
        existing_user = await models.User.find_one(models.User.email == user_data.email)
        if existing_user:
            raise AppException("El email ya está registrado.",409)
        
        # Verificar si el username ya existe
        if username:
            existing_username = await models.User.find_one(models.User.username == username)
            if existing_username:
                raise AppException("El username ya está en uso.",409)
        
        # Crear nuevo usuario
        new_user = models.User(
            email=user_data.email,
            username=username,
            name=user_data.name,
            lastname=user_data.lastname,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            status=models.UserStatus.ACTIVE,
            email_verified=False,
            auth_provider=models.AuthProvider.LOCAL,
            avatar_url=None,
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date,
            created_by=created_by,
            updated_by=created_by
        )
        
        await new_user.save()
        return new_user

    @staticmethod
    async def list_users(
        page: int = 1,
        per_page: int = 10,
        q: Optional[str] = None,
        role: Optional[models.Role] = None,
        user_status: Optional[models.UserStatus] = None,
    ) -> Dict[str, Any]:
        """Lista usuarios con paginación y filtros opcionales."""
        

        query = models.User.find(models.User.is_deleted == False)

        # Búsqueda por texto en email, username, name y lastname
        if q:
            safe_q = re.escape(q)
            regex = {"$regex": safe_q, "$options": "i"}
            query = query.find(Or(
                models.User.email == regex,
                models.User.username == regex,
                models.User.name == regex,
                models.User.lastname == regex,
                models.User.phone_number == regex
            ))

        if role:
            query = query.find(models.User.role == role)

        if user_status is not None:
            query = query.find(models.User.status == user_status)

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
    async def get_user(user_id: str) -> models.User:
        """Obtiene un usuario activo por ID."""
        return await UserService._get_active_user(user_id)

    @staticmethod
    async def update_user(user_id: str, update_data: schemas.user.UserUpdate, actor: models.User) -> models.User:
        """Actualiza datos textuales del usuario con validación de jerarquía y unicidad."""
        user = await UserService._get_active_user(user_id)
        
        # Validación estricta: Mismo rango y autogestión no están permitidos en rutas administrativas
        UserService._check_hierarchy(actor, user)

        # Validar unicidad de username
        if update_data.username is not None and update_data.username != user.username:
            existing = await models.User.find_one(models.User.username == update_data.username)
            if existing:
                raise AppException("El username ya está en uso",409)

        # Validar unicidad de email
        if update_data.email is not None and update_data.email != user.email:
            existing_email = await models.User.find_one(models.User.email == update_data.email)
            if existing_email:
                raise AppException("El email ya está en uso",409)

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)

        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def update_avatar(user_id: str, file: UploadFile, actor: models.User) -> models.User:
        """Actualiza el avatar del usuario subiendo la imagen a Cloudinary"""
        user = await UserService._get_active_user(user_id)
        
        # Validación estricta: Mismo rango y autogestión no están permitidos en rutas administrativas
        UserService._check_hierarchy(actor, user)

        new_avatar_url = await cloudinary_service.upload_image(file, folder="avatars")
        old_avatar_url=user.avatar_url
        
        user.avatar_url = new_avatar_url
        user.updated_by = str(actor.id)
        await user.save()
        if old_avatar_url!=None:
            await cloudinary_service.delete_image(old_avatar_url)
        return user

    @staticmethod
    async def reset_password(user_id: str, new_password: str, actor: models.User) -> None:
        """Restablece la contraseña de un usuario"""
        user = await UserService._get_active_user(user_id)

        # Restablecer contraseña requiere jerarquía estricta
        UserService._check_hierarchy(actor, user)

        user.password_hash = hash_password(new_password)
        user.updated_by = str(actor.id)
        await user.save()

    @staticmethod
    async def change_status(user_id: str, new_status: models.UserStatus, actor: models.User) -> models.User:
        """
        Cambia el estado del usuario al nuevo estado especificado.
        """
        user = await UserService._get_active_user(user_id)

        # La jerarquía ya maneja si intento cambiar el estado de mi propia cuenta (mismo nivel -> falla)
        UserService._check_hierarchy(actor, user)

        user.status = new_status
        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def change_role(user_id: str, new_role: models.Role, actor: models.User) -> models.User:
        """Cambia el rol de un usuario."""
        if new_role == models.Role.SUPERADMIN:
            raise AppException("No se puede asignar el rol SUPERADMIN", 403)

        user = await UserService._get_active_user(user_id)
        UserService._check_hierarchy(actor, user)

        user.role = new_role
        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def delete_user(user_id: str, actor: models.User) -> None:
        """
        Elimina un usuario:
        - ADMIN → Soft delete (borrado lógico).
        - SUPERADMIN → Hard delete (borrado físico permanente).
        """
        user = await UserService._get_active_user(user_id)

        # La jerarquía ya maneja si intento eliminar mi propia cuenta (mismo nivel -> falla)
        UserService._check_hierarchy(actor, user)
        if actor.role == models.Role.SUPERADMIN:
            # Hard delete físico
            await user.delete()
        else:
            # Soft delete
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            user.deleted_by = str(actor.id)
            user.updated_by = str(actor.id)
            await user.save()
    
    @staticmethod
    async def update_profile(update_data: schemas.user.UserSelfUpdate, actor: models.User) -> models.User:
        """
        Actualiza el perfil del propio usuario autenticado (autogestión).

        """
        #Validar unicidad de username (si está cambiando)
        if update_data.username is not None and update_data.username != actor.username:
            existing = await models.User.find_one(models.User.username == update_data.username)
            if existing:
                raise AppException("El username ya está en uso", 409)
        #Validar unicidad de email (si está cambiando)
        if update_data.email is not None and update_data.email != actor.email:
            existing_email = await models.User.find_one(models.User.email == update_data.email)
            if existing_email:
                raise AppException("El email ya está en uso", 409)
        update_dict = update_data.model_dump(exclude_unset=True)
        #Aplicar los cambios al objeto del actor
        for key, value in update_dict.items():
            setattr(actor, key, value)
        actor.updated_by = str(actor.id)
        await actor.save()
        return actor

    @staticmethod
    async def update_avatar_self(file: UploadFile, actor: models.User) -> models.User:
        """
        Actualiza el avatar del propio usuario autenticado (autogestión).
        """
        new_avatar_url = await cloudinary_service.upload_image(file, folder="avatars")
        old_avatar_url = actor.avatar_url

        actor.avatar_url = new_avatar_url
        actor.updated_by = str(actor.id)
        await actor.save()


        if old_avatar_url is not None:
            await cloudinary_service.delete_image(old_avatar_url)
        return actor


# Instancia global del servicio
user_service = UserService()
