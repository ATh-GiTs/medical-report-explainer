import sys
import os
from loguru import logger
from app.core.config import settings

# ─── Remove default logger ────────────────────────────────
logger.remove()

# ─── Create log directory if not exists ───────────────────
os.makedirs(settings.log_dir, exist_ok=True)

# ─── Console Logger (clean & colorful) ───────────────────
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
           "<level>{message}</level>",
    level=settings.log_level,
)

# ─── File Logger (full details for debugging) ─────────────
logger.add(
    f"{settings.log_dir}/app.log",
    rotation="10 MB",       # New file every 10MB
    retention="7 days",     # Keep logs for 7 days
    compression="zip",      # Compress old logs
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    level="DEBUG",
)

# ─── Export ───────────────────────────────────────────────
__all__ = ["logger"]
