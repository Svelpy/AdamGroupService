import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from PIL import Image
import io

# Configurar Cloudinary globalmente al importar
cloudinary.config( 
  cloud_name = settings.CLOUDINARY_CLOUD_NAME, 
  api_key = settings.CLOUDINARY_API_KEY, 
  api_secret = settings.CLOUDINARY_API_SECRET,
  secure = True
)

class CloudinaryService:
    @staticmethod
    async def upload_image(file: UploadFile, folder: str = "avatars") -> str:
        """
        Sube una imagen a Cloudinary y retorna la URL segura.
        
        Args:
            file: El archivo UploadFile de FastAPI.
            folder: La carpeta en Cloudinary donde guardar (default: 'avatars').
            
        Returns:
            str: URL segura de la imagen subida.
            
        Raises:
            HTTPException: Si el archivo no es imagen o hay error de subida.
        """
        
        # 1. Validar Content-Type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen (jpg, png, etc.)"
            )
        
        # 1.5 Bloquear SVG explícitamente (riesgo de XSS)
        if file.content_type == "image/svg+xml" or file.filename.lower().endswith('.svg'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los archivos SVG no están permitidos por seguridad"
            )
            
        # 2. Leer archivo
        content = await file.read()
        
        # 3. Validar tamaño (Max 5MB)
        if len(content) > 5 * 1024 * 1024:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La imagen no puede pesar más de 5MB"
            )
        
        # 4. Validar dimensiones (Max 4K: 4096x4096)
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            
            if width > 4096 or height > 4096:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La imagen es demasiado grande ({width}x{height}px). Máximo 4096x4096px"
                )
        except HTTPException:
            raise  # Re-lanzar nuestras propias excepciones
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no es una imagen válida"
            )
            
        try:
            # 4. Subir a Cloudinary
            # Se usa el contenido en bytes directamente
            response = cloudinary.uploader.upload(
                content, 
                folder=f"{settings.CLOUDINARY_FOLDER_NAME}/{folder}",
                resource_type="image"
            )
            
            return response.get("secure_url")
            
        except Exception as e:
            print(f"Error subiendo a Cloudinary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al subir la imagen al servidor"
            )
        finally:
            await file.seek(0) # Resetear puntero por si acaso

cloudinary_service = CloudinaryService()
