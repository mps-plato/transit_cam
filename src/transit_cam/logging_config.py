import logging

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": '%(asctime)s - %(name)s - %(levelname)s | %(message)s'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": logging.INFO,
            "formatter": "default"
        }
    },
    "loggers": {
        "transit_cam": {
            "level": logging.INFO,
            "handlers": ["console"],
        }
    },
}
