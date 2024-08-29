import logging


def setup_logging(is_debug_mode=False):
    level = logging.DEBUG if is_debug_mode else logging.INFO
    log_format = "%(asctime)s [%(funcName)-15s] %(levelname)-7s %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(level=level, format=log_format, datefmt=date_format)

    health_check_filter = EndpointFilter(path="/health")
    for access_logger in ("uvicorn.access", "gunicorn.access"):
        logging.getLogger(access_logger).addFilter(health_check_filter)


class EndpointFilter(logging.Filter):
    """
    Filters out log records for requests to a specific path, such as health checks.
    """

    def __init__(self, path):
        super().__init__()
        self.path = path

    def filter(self, record):
        return self.path not in record.getMessage()