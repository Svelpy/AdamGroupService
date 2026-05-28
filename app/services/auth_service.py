"""
Servicio de Autenticación
Lógica de negocio para login, registro y gestión de tokens adaptada al proyecto
"""

from typing import Optional
from fastapi import HTTPException, status

from app.models.user import User
from app.models.enums import Role, UserStatus
from app.schemas.user_schema import (
    UserCreate,
    UserSelfRegister,
    UserLogin,
    TokenResponse
)
from app.utils.security import hash_password, verify_password, create_access_token


class AuthService:
    """Servicio de autenticación"""

    @staticmethod
    async def register_user(user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """
        Registrar un nuevo usuario (USO ADMINISTRATIVO)
        
        Args:
            user_data: Datos del usuario a crear (rol configurable)
            created_by: ID del usuario creador
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException 400: Si el email o username ya existe
        """
        # Verificar si el email ya existe
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Verificar si el username ya existe (si se proporciona)
        if user_data.username:
            existing_username = await User.find_one(User.username == user_data.username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El username ya está en uso"
                )
        
        # Crear nuevo usuario con rol administrativo asignado
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            name=user_data.name,
            lastname=user_data.lastname,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            status=UserStatus.ACTIVE,
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date,
            created_by=created_by,
            updated_by=created_by
        )
        
        await new_user.save()
        return new_user

    @staticmethod
    async def register_self(user_data: UserSelfRegister) -> User:
        """
        Autoregistro público de nuevos usuarios (USO PÚBLICO)
        
        Args:
            user_data: Datos del usuario a registrar (rol USER por defecto)
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException 400: Si el email o username ya existe
        """
        # Verificar si el email ya existe
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Verificar si el username ya existe (si se proporciona)
        if user_data.username:
            existing_username = await User.find_one(User.username == user_data.username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El username ya está en uso"
                )
        
        # Crear nuevo usuario (Rol USER y Estado ACTIVE por defecto)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            name=user_data.name,
            lastname=user_data.lastname,
            password_hash=hash_password(user_data.password),
            role=Role.USER,
            status=UserStatus.ACTIVE,
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date
        )
        
        await new_user.save()
        return new_user

    @staticmethod
    async def login(credentials: UserLogin) -> TokenResponse:
        """
        Autenticar usuario y generar token JWT
        
        Args:
            credentials: Email y contraseña
            
        Returns:
            Token de acceso y datos del usuario
            
        Raises:
            HTTPException 401: Si las credenciales son inválidas
            HTTPException 403: Si el usuario no está activo
        """
        # Buscar usuario por email (excluir eliminados)
        user = await User.find_one(User.email == credentials.email, User.is_deleted == False)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar contraseña
        if not user.password_hash or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el usuario esté activo
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Usuario inactivo o no verificado. Estado actual: {user.status.value}"
            )
        
        # Crear token JWT
        access_token = create_access_token(
            data={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role.value
            }
        )
        
        # Retorna el TokenResponse (el serializador de FastAPI se encargará del mapeo a UserResponse)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user
        )

    @staticmethod
    async def get_current_user_info(user: User) -> User:
        """
        Obtener información del usuario actual
        """
        return user

    @staticmethod
    async def change_password(
        user: User,
        current_password: str,
        new_password: str
    ) -> dict:
        """
        Cambiar contraseña del usuario
        
        Args:
            user: Usuario autenticado
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Mensaje de confirmación
            
        Raises:
            HTTPException 400: Si la contraseña actual es incorrecta
        """
        # Verificar contraseña actual
        if not user.password_hash or not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Actualizar contraseña
        user.password_hash = hash_password(new_password)
        await user.save()
        
        return {"detail": "Contraseña actualizada exitosamente"}


# Instancia global del servicio
auth_service = AuthService()
