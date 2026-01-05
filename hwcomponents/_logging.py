import logging
import queue
from typing import List, Union
from logging.handlers import QueueHandler

logging.basicConfig(
    format="%(levelname)-8s%(message)s",
)
if logging.getLogger().level == logging.NOTSET:
    logging.getLogger().setLevel(logging.INFO)

LOG_QUEUES = {}
NAME2LOGGER = {}


def queue_from_logger(logger: Union[logging.Logger, str]) -> List[str]:
    if isinstance(logger, str) and logger in LOG_QUEUES:
        return LOG_QUEUES[logger]
    for name, other_logger in NAME2LOGGER.items():
        if other_logger is logger and name in LOG_QUEUES:
            return LOG_QUEUES[name]
    raise ValueError(f"Logger {logger} not found")


def messages_from_logger(logger: Union[logging.Logger, str]) -> List[str]:
    return [m.getMessage() for m in queue_from_logger(logger).queue]


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False
    NAME2LOGGER[name] = logger
    if name not in LOG_QUEUES:
        LOG_QUEUES[name] = queue.Queue()
        logger.addHandler(QueueHandler(LOG_QUEUES[name]))
    return logger


def move_queue_from_one_logger_to_another(
    src: Union[logging.Logger, str], dest: Union[logging.Logger, str]
):
    src_queue = queue_from_logger(src)
    dest_queue = queue_from_logger(dest)
    if src_queue is dest_queue:
        return
    while not src_queue.empty():
        dest_queue.put(src_queue.get())


def pop_all_messages(logger: Union[logging.Logger, str]) -> List[str]:
    messages = messages_from_logger(logger)
    queue_from_logger(logger).queue.clear()
    return messages


def print_messages(logger: Union[logging.Logger, str]):
    for message in messages_from_logger(logger):
        print(message)


class ListLoggable:
    def __init__(self, name: str = None):
        self._init_logger(name)

    def _init_logger(self, name: str = None):
        if self.logger is not None:
            return
        if name is None:
            if hasattr(self, "__name__"):
                name = self.__name__
            else:
                name = self.__class__.__name__
        self.logger = get_logger(name)

    @property
    def logger(self) -> logging.Logger:
        if getattr(self, "_logger", None) is None:
            if hasattr(self, "__name__"):
                self._logger = get_logger(self.__name__)
            else:
                self._logger = get_logger(self.__class__.__name__)
            self._logger.setLevel(logging.INFO)
        return self._logger


def log_all_lines(logger_name, level, to_split):
    logger = logging.getLogger(logger_name)
    if isinstance(level, str):
        logfunc = getattr(logger, level)
        for s in to_split.splitlines():
            logfunc(s)
    else:
        for s in to_split.splitlines():
            logging.getLogger(logger_name).log(level, s)


def clear_logs():
    for name, queue in LOG_QUEUES.items():
        queue.queue.clear()
