import logging

from lib.config import Config

logger = logging.getLogger(Config.logger_name)
logger.setLevel(Config.log_level)

for handler in Config.logg_handlers:
    # Get formatter
    formatter = Config.formatter
    # Set formatter
    handler.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(handler)

logger.debug(f'Loaded these handlers: {Config.logg_handlers}')
