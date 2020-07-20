import logging
import downlink_scheduler_tool.downlink_scheduler as downlink_scheduler

from logger_configurator import LoggerConfigurator

LoggerConfigurator(level="INFO")
logger = logging.getLogger(__name__)

DB_CONFIG = {"database": "config_scheduler",
             "host": "postgres",
             "port": 5432,
             "user": "postgres",
             "password": "CushVenyayz0"}


def main():
    config_scheduler = downlink_scheduler.DownlinkScheduler(db_config=DB_CONFIG)
    config_scheduler.start_scheduler()


if __name__ == '__main__':
    main()
