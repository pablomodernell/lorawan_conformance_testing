import sys
import logging

DEFAULT_LOG_FORMAT = '%(asctime)s %(name)-12s %(funcName)20s %(levelname)-8s %(message)s'
LEVEL_VALUES = ['WARN', 'ERROR', 'DEBUG', 'INFO', 'WARNING', 'CRITICAL', 'NOTSET']


class LoggerConfigurator(object):
    singleton_instance = None
    logging_level = None

    class Singleton:
        def __init__(self, level, log_format):

            LoggerConfigurator.logging_level = level

            root_logger = logging.getLogger("")

            if level.upper() in LEVEL_VALUES:
                effective_log_level = level.upper()
            else:
                effective_log_level = logging.NOTSET

            root_logger.setLevel(effective_log_level)
            formatter = logging.Formatter(log_format)

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

    def __init__(self, level="INFO", log_format=DEFAULT_LOG_FORMAT):

        if LoggerConfigurator.singleton_instance is not None:
            logging.getLogger().debug("Logging module already configured.")
            return

        LoggerConfigurator.singleton_instance = LoggerConfigurator.Singleton(level, log_format)
