import logging
import downlink_scheduler_tool.downlink_scheduler as downlink_scheduler

from logger_configurator import LoggerConfigurator

LoggerConfigurator(level="INFO")
logger = logging.getLogger(__name__)


def main():
    config_scheduler = downlink_scheduler.DownlinkScheduler()
    config_scheduler.start_scheduler()


if __name__ == '__main__':
    main()
