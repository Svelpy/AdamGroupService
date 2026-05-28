"""
Utilidades de seguridad: JWT y hashing de contraseñas
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Contexto para hashing de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


import hashlib

def hash_password(password: str) -> str:
    """
    Hash de contraseña usando SHA-256 + bcrypt.
    
    1. Pre-hasheamos con SHA-256 para obtener un string de longitud fija (64 chars).
    2. Hasheamos eso con Bcrypt.
    
    Esto evita el límite de 72 bytes de Bcrypt y permite contraseñas de cualquier longitud.
    """
    # Pre-hash para seguridad y compatibilidad de longitud
    password_safe = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password_safe)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar contraseña contra hash (con pre-hash SHA-256)
    """
    # Aplicar el mismo pre-hashing antes de verificar
    password_safe = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(password_safe, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear token JWT de acceso
    
    Args:
        data: Datos a incluir en el token (user_id, email, role)
        expires_delta: Tiempo de expiración personalizado
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodificar y verificar token JWT
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Payload del token si es válido, None si no es válido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validar fortaleza de contraseña
    
    Args:
        password: Contraseña a validar
        
    Returns:
        (es_válida, mensaje_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    # Puedes agregar más validaciones aquí:
    # - Al menos una mayúscula
    # - Al menos un número
    # - Al menos un carácter especial
    
    return True, ""
