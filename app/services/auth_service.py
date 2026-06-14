from app.utils.errors import AppException
from typing import Optional
from app import models
from app import schemas
from app.utils.security import hash_password, verify_password, create_access_token


class AuthService:

    @staticmethod
    async def register_self(user_data: schemas.user.UserSelfRegister) -> models.User:
        """
        Autoregistro público de nuevos usuarios
        
        Args:
            user_data: Datos del usuario a registrar (role = USER por defecto)
            
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
            raise AppException("El email ya está registrado.",400)
        
        # Verificar si el username ya existe
        if username!=None:
            existing_username = await models.User.find_one(models.User.username == username)
            if existing_username:
                raise AppException("El username ya está en uso.",400)
        
        # Crear nuevo usuario
        new_user = models.User(
            email=user_data.email,
            username=username,
            name=user_data.name,
            lastname=user_data.lastname,
            password_hash=hash_password(user_data.password),
            role=models.Role.USER,
            status=models.UserStatus.ACTIVE,
            email_verified=False,
            auth_provider=models.AuthProvider.LOCAL,
            avatar_url=None,
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date,
            created_by=None,
            updated_by=None
        )
        
        await new_user.save()
        return new_user

    @staticmethod
    async def login(credentials: schemas.user.UserLogin) -> schemas.user.TokenResponse:
        """
        Autenticar usuario y generar token JWT
        
        Args:
            credentials: Email y contraseña
            
        Returns:
            Token de acceso y datos del usuario
        """
        # Buscar usuario por email
        user = await models.User.find_one(models.User.email == credentials.email, models.User.is_deleted == False)
        
        if not user:
            raise AppException("Email o contraseña incorrectos.",401)
        
        # Verificar contraseña
        if not user.password_hash or not verify_password(credentials.password, user.password_hash):
            raise AppException("Email o contraseña incorrectos.",401)
        
        # Verificar que el usuario esté activo
        if user.status != models.UserStatus.ACTIVE:
            raise AppException("Usuario inactivo o no verificado.",403)
        # Crear token JWT
        access_token = create_access_token(
            data={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role.value
            }
        )
        
        # Retorna el TokenResponse (el serializador de FastAPI se encargará del mapeo a UserResponse)
        return schemas.user.TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    @staticmethod
    async def change_password(user: models.User,current_password: str,new_password: str) -> dict:
        """
        Cambiar contraseña del usuario
        
        Args:
            user: Usuario autenticado
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Mensaje de confirmación
        """
        # Verificar contraseña actual
        if not user.password_hash or not verify_password(current_password, user.password_hash):
            raise AppException("Contraseña actual incorrecta",401)
        
        # Actualizar contraseña
        user.password_hash = hash_password(new_password)
        await user.save()
        
        return {"detail": "Contraseña actualizada exitosamente"}

        


auth_service = AuthService()
