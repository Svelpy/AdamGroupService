import logging

from app.core.config import settings


def setup_logging() -> None:
    """
    Configura el sistema de logging global.
    """
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
