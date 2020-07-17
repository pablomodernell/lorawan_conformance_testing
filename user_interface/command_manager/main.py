import logging
import request_processor

from logger_configurator import LoggerConfigurator

LoggerConfigurator(level="DEBUG")
logger = logging.getLogger(__name__)


def command_manager_main():
    print("Starting the Command Manager")
    logger.debug("Starting the Command Manager")
    req_processor_instance = request_processor.RequestProcessor()
    print("Request processor created and ready to start.")
    logger.debug("Request processor created and ready to start.")
    req_processor_instance.consume_start()


if __name__ == '__main__':
    command_manager_main()
