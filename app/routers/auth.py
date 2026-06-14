from fastapi import APIRouter, Depends, Request, status
from app.middlewares.limiter import limiter
from app import models, schemas
from app.utils.dependencies import get_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.user.UserResponse)
async def register(user_data: schemas.user.UserSelfRegister):
    """
    Registro público de nuevos usuarios.
    
    Crea una cuenta con rol 'USER' y estado 'ACTIVE'.
    """
    return await AuthService.register_self(user_data)


@router.post("/login", response_model=schemas.user.TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: schemas.user.UserLogin):
    """
    Iniciar sesión con correo y contraseña.
    
    Emite un token JWT de acceso válido.
    """
    return await AuthService.login(credentials)


@router.get("/me", response_model=schemas.user.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Obtener la información del perfil del usuario autenticado.
    """
    return current_user


@router.post("/change-password")
async def change_password(
    data: schemas.user.ChangePasswordSchema,
    current_user: models.User = Depends(get_current_user)
):
    """
    Permite al usuario autenticado cambiar su contraseña de forma segura.
    """
    return await AuthService.change_password(
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password
    )


