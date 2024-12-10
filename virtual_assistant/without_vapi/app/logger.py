import logging
import os
from logging.handlers import TimedRotatingFileHandler

from app.settings import settings


# Function to set up the logger
def setup_logger(log_dir: str, log_level: str, retention_days: int):
    # Create log directory if it does not exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logger configuration
    logger = logging.getLogger("helloservice.ai")
    logger.setLevel(logging._nameToLevel[log_level])

    # Formatter for the logs
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler for streaming logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with log rotation based on time (days)
    log_file = os.path.join(log_dir, "app.log")
    file_handler = TimedRotatingFileHandler(
        log_file, when="D", interval=1, backupCount=retention_days
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Setup logger with log directory and retention days
logger = setup_logger(
    log_dir="./logs",
    log_level=(logging.DEBUG if settings.DEBUG else settings.LOG_LEVEL),
    retention_days=7,
)
