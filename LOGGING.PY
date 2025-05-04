
# Logging system in Python with comments and design patterns

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import threading
import json
import os


# ========= ENUM: LogLevel =========
class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    ERROR = 3

    def is_greater_or_equal(self, other):
        return self.value >= other.value


# ========= CLASS: LogMessage =========
class LogMessage:
    def __init__(self, level: LogLevel, message: str, context=None):
        self.level = level
        self.message = message
        self.timestamp = datetime.now()
        self.context = context or {}

    def __str__(self):
        return f"[{self.level.name}] {self.timestamp} - {self.message}"


# ========= STRATEGY INTERFACE: LogFormatter =========
class LogFormatter(ABC):
    @abstractmethod
    def format(self, log_entry: LogMessage) -> str:
        pass


class SimpleLogFormatter(LogFormatter):
    def format(self, log_entry: LogMessage) -> str:
        return f"[{log_entry.level.name}] {log_entry.timestamp} - {log_entry.message}"


class JsonLogFormatter(LogFormatter):
    def format(self, log_entry: LogMessage) -> str:
        data = {
            "timestamp": str(log_entry.timestamp),
            "level": log_entry.level.name,
            "message": log_entry.message,
            "context": log_entry.context,
        }
        return json.dumps(data, indent=2)


# ========= STRATEGY INTERFACE: LogAppender =========
class LogAppender(ABC):
    def __init__(self, formatter: LogFormatter):
        self.formatter = formatter

    @abstractmethod
    def append(self, log_message: LogMessage):
        pass


class ConsoleAppender(LogAppender):
    def append(self, log_message: LogMessage):
        print(self.formatter.format(log_message))


class FileAppender(LogAppender):
    def __init__(self, formatter: LogFormatter, file_path: str):
        super().__init__(formatter)
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def append(self, log_message: LogMessage):
        with open(self.file_path, "a") as file:
            file.write(self.formatter.format(log_message) + "\n")


# ========= CHAIN OF RESPONSIBILITY: LogHandler =========
class LogHandler:
    def __init__(self, level: LogLevel, appender: LogAppender):
        self.level = level
        self.appender = appender
        self.next_handler = None

    def set_next(self, next_handler: 'LogHandler'):
        self.next_handler = next_handler

    def log(self, level: LogLevel, message: str, context=None):
        if level.is_greater_or_equal(self.level):
            log_msg = LogMessage(level, message, context)
            self.appender.append(log_msg)
        if self.next_handler:
            self.next_handler.log(level, message, context)


# ========= SINGLETON LOGGER =========
class Logger:
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, config_level: LogLevel, config_appender: LogAppender):
        self.config_level = config_level
        self.config_appender = config_appender

    @classmethod
    def get_instance(cls, config_level: LogLevel, config_appender: LogAppender):
        key = (config_level, type(config_appender).__name__)
        with cls._lock:
            if key not in cls._instances:
                cls._instances[key] = Logger(config_level, config_appender)
        return cls._instances[key]

    def log(self, level: LogLevel, message: str, context=None):
        if level.is_greater_or_equal(self.config_level):
            log_msg = LogMessage(level, message, context)
            self.config_appender.append(log_msg)

    def debug(self, message, context=None):
        self.log(LogLevel.DEBUG, message, context)

    def info(self, message, context=None):
        self.log(LogLevel.INFO, message, context)

    def error(self, message, context=None):
        self.log(LogLevel.ERROR, message, context)


# ========= MAIN =========
if __name__ == "__main__":
    # Example formatters and appenders
    simple_formatter = SimpleLogFormatter()
    json_formatter = JsonLogFormatter()

    console_appender = ConsoleAppender(formatter=simple_formatter)
    file_appender = FileAppender(formatter=json_formatter, file_path="./logs/app.log")

    # Chain of Responsibility
    error_logger = LogHandler(LogLevel.ERROR, console_appender)
    debug_logger = LogHandler(LogLevel.DEBUG, file_appender)
    info_logger = LogHandler(LogLevel.INFO, console_appender)

    info_logger.set_next(debug_logger)
    debug_logger.set_next(error_logger)

    # Usage of chained loggers
    print("=== Chain of Responsibility Logging ===")
    info_logger.log(LogLevel.INFO, "System started.")
    info_logger.log(LogLevel.DEBUG, "Debugging DB connection", {"db": "users"})
    info_logger.log(LogLevel.ERROR, "Unhandled exception", {"code": 500})

    # Singleton Logger
    print("\n=== Singleton Logger Usage ===")
    singleton_logger = Logger.get_instance(LogLevel.INFO, file_appender)
    singleton_logger.info("Singleton INFO log")
    singleton_logger.debug("Singleton DEBUG should not print")
    singleton_logger.error("Singleton ERROR log", {"module": "auth"})
