import logging
import logging.handlers
import json
from pathlib import Path
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger

from core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    
    log_path = Path(settings.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.value))
    
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=settings.MAX_LOG_SIZE,
        backupCount=settings.BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)
