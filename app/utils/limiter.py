"""
Instancia compartida del rate limiter (SlowAPI).

Se define aquí para evitar importaciones circulares entre main.py y los routers.
main.py importa desde aquí para registrar el limiter en la app.
Los routers importan desde aquí para usar @limiter.limit(...) como decorador.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia singleton del limiter — clave por IP del cliente
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
