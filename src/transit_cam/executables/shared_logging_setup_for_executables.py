from argparse import ArgumentParser
import logging
import logging.config
from transit_cam.logging_config import logging_config


def parse_logging_args() -> str:
    parser = ArgumentParser()
    parser.add_argument(
        "--log", 
        choices=["debug", "info", "warning", "error"], 
        default="warning", 
        dest="log_level"
    )
    args = parser.parse_args()
    return args.log_level

def init_logging(log_level: str) -> None:
    logging_config["loggers"]["transit_cam"]["level"] = log_level.upper()
    logging_config["handlers"]["console"]["level"] = log_level.upper()
    logging.config.dictConfig(logging_config)
