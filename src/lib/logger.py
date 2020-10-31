import logging

from lib.config import Config

config = Config()


logger = logging.getLogger(config.logger_name)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(config.logging_level)

# Get formatter
formatter = Config.formatter
# Set formatter
handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(handler)
