import logging
import os

import structlog


def shared_processors() -> list:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def get_renderer(*, debug: bool):
    if debug:
        return structlog.dev.ConsoleRenderer()
    return structlog.processors.JSONRenderer()


def configure_structlog(*, debug: bool) -> None:
    structlog.configure(
        processors=[
            *shared_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logging_config(*, debug: bool) -> dict:
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    renderer = get_renderer(debug=debug)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structlog": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": shared_processors(),
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    renderer,
                ],
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structlog",
            }
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "django.request": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "urllib3": {"level": "WARNING", "propagate": True},
            "chromadb": {"level": "WARNING", "propagate": True},
            "httpx": {"level": "WARNING", "propagate": True},
            "httpcore": {"level": "WARNING", "propagate": True},
        },
    }


def get_logger(name: str):
    return structlog.get_logger(name)
