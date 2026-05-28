"""
Router de Autenticación y Autogestión de Perfil
"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from slowapi import Limiter
from app.utils.limiter import limiter
from app.models.user import User
from app.schemas.user_schema import (
    UserSelfRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    ChangePasswordSchema,
    UserUpdate
)
from app.utils.dependencies import get_current_user
from app.services.user_service import UserService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(user_data: UserSelfRegister):
    """
    Registro público de nuevos usuarios.
    
    Crea una cuenta con rol 'USER' y estado 'ACTIVE'.
    """
    return await AuthService.register_self(user_data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    """
    Iniciar sesión con correo y contraseña.
    
    Emite un token JWT de acceso válido.
    """
    return await AuthService.login(credentials)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtener la información del perfil del usuario autenticado.
    """
    return await AuthService.get_current_user_info(current_user)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado cambiar su contraseña de forma segura.
    """
    return await AuthService.change_password(
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password
    )


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado actualizar sus propios datos personales.
    """
    return await UserService.update_profile(update_data=data, actor=current_user)


@router.post("/profile/avatar", response_model=UserResponse)
async def update_avatar_self(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado subir o actualizar su propia foto de perfil.
    """
    # Validar extensión básica
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo subido debe ser una imagen válida"
        )
        
    return await UserService.update_avatar_self(file=file, actor=current_user)
