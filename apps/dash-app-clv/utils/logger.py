import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import json
import psutil
import os
import time
from functools import wraps
import random
import gc
from pathlib import Path
from datetime import datetime
from databricks import sql
import sys
import pandas as pd

from utils.constants import (
    SERVER_HOSTNAME,
    HTTP_PATH,
    ACCESS_TOKEN,
)

'''
def log_and_raise(error_msg, logger, error_class=TM1PlotError):
    """
    Logs the error and raises a custom exception with error ID included.

    Args:
        error_msg (str): The error message
        logger (DashErrorLogger): Instance of the logger
        error_class (Exception): The exception class to raise
    """
    error_id = logger.error(error_msg)
    user_msg = f"[Error ID: {error_id}] {error_msg}" if error_id else error_msg
    raise error_class(user_msg)
    # add open and exit

'''
# LOG_TABLE_NAME
# DASH_APP_NAME --> defined on dash server


class JSONFormatter(logging.Formatter):
    """Formatter that adds a readable log summary above the JSON output."""

    def format(self, record):
        # Format log timestamp
        log_time = self.formatTime(record, self.datefmt)

        # Construct a human-readable log entry with bold log level
        readable_log_entry = (
            f"\n=== LOG ENTRY ===\n"
            f"Timestamp: {log_time}\n"
            f"Level: {record.levelname}\n"
            f"Message: {record.getMessage()}\n"
            f"Traceback: \n{getattr(record, 'traceback', 'N/A')}\n"
            f"--------------------------------------\n"
        )

        # Construct structured JSON entry
        log_entry = {
            "error_type": getattr(record, "error_type", ""),
            "error_message": getattr(record, "error_message", ""),
            "error_function": getattr(record, "error_function", ""),
            "error_locals": getattr(record, "error_locals", {}),
            "caller_function": getattr(record, "caller_function", ""),
            "caller_locals": getattr(record, "caller_locals", {}),
            "app_name": getattr(record, "app_name", record.name),
        }

        # Convert JSON log entry to formatted string
        json_log_entry = json.dumps(log_entry, indent=4, default=str)

        # Return combined readable log + JSON
        return readable_log_entry + json_log_entry


class StreamFormatter(logging.Formatter):
    """Formatter for console logs with readable format and bold log level."""

    BOLD = "\033[1m"
    RESET = "\033[0m"  # Reset formatting after bold text

    def format(self, record):
        log_time = self.formatTime(record, self.datefmt)

        log_entry = f"{self.BOLD}{log_time} - {record.name} - {record.levelname} - {record.getMessage()}{self.RESET}"

        if record.exc_info:
            log_entry += f"\n{self.formatException(record.exc_info)}\n"

        return log_entry


class DashLogger:
    # Constants for formatting
    MAX_TRACEBACK_FRAMES = 5
    TRUNCATION_MARKER = "..."
    FRAME_INDENT = "  "
    CODE_INDENT = "    "

    def __init__(self, logger_name=None, env=None, log_table_name=None):
        """
        Initialize the Dash Error Logger with Databricks logging support.
        """
        VALID_ENVIRONMENTS = {"dev", "prod"}
        LOG_SCHEMA_NAME = "test_logs"
        LOG_TABLE_NAME = "logs"
        APP_NAME = "triml"

        self.env = env if env else os.getenv("ENV", "prod").lower()
        if self.env not in VALID_ENVIRONMENTS:
            error_msg = (
                f"Invalid environment: {self.env}. Must be one of {VALID_ENVIRONMENTS}"
            )
            print(f"{error_msg}", file=sys.stderr)
            raise ValueError(error_msg)

        self.log_dir = self._setup_log_directory()
        """
        self.log_table_name = (
            log_table_name
            if log_table_name
            else os.getenv(
                "LOG_TABLE_NAME", f"{LOG_SCHEMA_NAME}.{LOG_TABLE_NAME}"
            ).lower()
        )
        """
        self._logger = logging.getLogger(
            logger_name or os.getenv("DASH_APP_NAME", APP_NAME).lower()
        )
        self._logger.setLevel(logging.DEBUG)
        self._handlers = {}

        # Initialize handlers
        self._init_handlers()

    def _setup_log_directory(self):
        LOG_DIR = "logs"
        base_dir = os.getenv("LOG_DIR", LOG_DIR)
        log_dir = Path(base_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir)

    def _init_handlers(self):
        """
        Initialize logging handlers based on the environment.
        logging levels: DEBUG < INFO < WARNING < ERROR < CRITICAL
        """

        # First clear all handlers
        self._logger.handlers.clear()

        # Create formatters
        json_formatter = JSONFormatter()
        stream_formatter = StreamFormatter()

        if self.env == "dev":
            self._add_stream_handler(logging.DEBUG, stream_formatter)
            self._add_file_handler(
                os.path.join(self.log_dir, "dev.log"), logging.DEBUG, json_formatter
            )

        elif self.env == "prod":
            self._add_stream_handler(logging.CRITICAL, stream_formatter)
            self._add_file_handler(
                os.path.join(self.log_dir, "prod.log"), logging.ERROR, json_formatter
            )
            # self._init_databricks_logging()

    def _add_stream_handler(self, level, formatter):
        """Add a stream handler."""
        if "stream" in self._handlers:
            return  # Avoid adding multiple stream handlers

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)

        self._logger.addHandler(stream_handler)
        self._handlers["stream"] = stream_handler  # Store it for tracking

    def _add_file_handler(self, log_file_path, level, formatter):
        """Add a Timed Rotating File Handler."""
        if "file" in self._handlers:
            return

        file_handler = TimedRotatingFileHandler(
            filename=log_file_path,
            when="W0",
            interval=1,
            backupCount=4,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)
        self._handlers["file"] = file_handler

    def _init_databricks_logging(self):
        """Initialize Databricks logging by checking credentials and setting up the table."""
        required_vars = {
            "server_hostname": SERVER_HOSTNAME,
            "http_path": HTTP_PATH,
            "access_token": ACCESS_TOKEN,
        }

        if not all(required_vars.values()):
            self._logger.warning("Missing Databricks connection variables.")
            return

        self.databricks_conn = required_vars
        self._initialize_table()

    def _initialize_table(self):
        """Ensure the Databricks Delta table exists."""

        query = f"""
        CREATE TABLE IF NOT EXISTS {self.log_table_name} (
            error_id BIGINT GENERATED ALWAYS AS IDENTITY,
            timestamp TIMESTAMP,
            app_name STRING,
            level STRING,
            message STRING,
            error_type STRING,
            error_message STRING,
            error_function STRING,
            error_locals STRING,
            traceback STRING,
            caller_function STRING,
            caller_locals STRING
        ) USING DELTA;
        """
        try:
            with sql.connect(**self.databricks_conn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    self._logger.info(
                        f"Initialized Databricks table: {self.log_table_name}"
                    )
        except Exception as e:
            self._logger.error("Error initializing Databricks table", exc_info=e)

    def _write_to_databricks(self, log_entry):
        """Write a log entry to the Databricks table and return the generated error_id."""

        try:
            with sql.connect(**self.databricks_conn) as connection:
                with connection.cursor() as cursor:

                    # Part 1: Prepare the data
                    sanitized_values = []
                    columns = []

                    # Loop through the log entry and prepare data for insertion
                    for key, value in log_entry.items():
                        if key != "error_id":  # Skip error_id as it's auto-generated!
                            columns.append(key)
                            if isinstance(value, (dict, list, set)):
                                sanitized_values.append(str(value))
                            elif isinstance(value, datetime):
                                sanitized_values.append(value.isoformat())
                            else:
                                sanitized_values.append(value)

                    # Join columns and create placeholders for SQL
                    columns_str = ", ".join(columns)
                    placeholders = ", ".join(["%s"] * len(sanitized_values))

                    # Part 2: Insert the data
                    insert_query = f"""
                    INSERT INTO {self.log_table_name} ({columns_str})
                    VALUES ({placeholders})
                    """
                    cursor.execute(insert_query, sanitized_values)
                    connection.commit()

                    # Part 3: Retrieve the error_id
                    select_query = f"""
                    SELECT error_id FROM {self.log_table_name}
                    WHERE timestamp = %s
                    AND level = %s
                    AND message = %s
                    AND app_name = %s
                    ORDER BY error_id DESC
                    LIMIT 1
                    """
                    cursor.execute(
                        select_query,
                        (
                            log_entry["timestamp"],
                            log_entry["level"],
                            log_entry["message"],
                            log_entry["app_name"],
                        ),
                    )
                    result = cursor.fetchone()
                    error_id = result[0] if result else None

                    return error_id

        except Exception as e:
            self._logger.error("Failed to write to Databricks", exc_info=e)
            raise

    def _truncate_string(self, text, max_length):
        """Safely truncate a string to max_length."""
        return (
            text
            if len(text) <= max_length
            else text[: max_length - len(self.TRUNCATION_MARKER)]
            + self.TRUNCATION_MARKER
        )

    def format_value(self, value, max_length=1000, depth=0, max_depth=5):
        """
        Format a value for error logging with simple, serializable output.
        Individual items are truncated if they exceed max_length.

        Args:
            value: Any Python object/value to format
            max_length: Maximum length for individual items
            depth: Current recursion depth (to prevent infinite recursion)
            max_depth: Maximum recursion depth allowed

        Returns:
            A formatted, serializable representation of the value
        """
        try:
            # Prevent infinite recursion
            if depth > max_depth:
                return "[MAX_DEPTH_REACHED]"

            # Handle None and primitive types
            if value is None or isinstance(value, (int, float, bool)):
                return value

            # Handle pandas DataFrame
            if str(type(value).__module__).startswith("pandas."):
                if isinstance(value, pd.DataFrame):
                    return {
                        "type": "DataFrame",
                        "shape": value.shape,
                        "columns": list(value.columns)[:5],
                        "preview": str(value.head(2).to_dict("records"))[:max_length],
                    }
                if isinstance(value, pd.Series):
                    return {
                        "type": "Series",
                        "length": len(value),
                        "preview": str(value.head(3).tolist())[:max_length],
                    }

            # Handle numpy arrays
            if str(type(value).__module__).startswith("numpy."):
                return {
                    "type": "ndarray",
                    "shape": value.shape if hasattr(value, "shape") else None,
                    "preview": (
                        str(value.flatten()[:3])[:max_length]
                        if hasattr(value, "flatten")
                        else str(value)[:max_length]
                    ),
                }

            # Handle strings
            if isinstance(value, str):
                if len(value) > max_length:
                    return value[: max_length - 3] + "..."
                return value

            # Handle lists, tuples, sets
            if isinstance(value, (list, tuple, set)):
                items = []
                collection_type = type(value).__name__

                for item in value:
                    formatted_item = self.format_value(
                        item,
                        max_length=max_length,  # Apply max_length to each item
                        depth=depth + 1,
                        max_depth=max_depth,
                    )
                    items.append(formatted_item)

                return {"type": collection_type, "length": len(value), "items": items}

            # Handle dictionaries
            if isinstance(value, dict):
                items = {}

                for k, v in value.items():
                    formatted_key = str(k)[:max_length]  # Limit key length
                    formatted_value = self.format_value(
                        v,
                        max_length=max_length,  # Apply max_length to each value
                        depth=depth + 1,
                        max_depth=max_depth,
                    )
                    items[formatted_key] = formatted_value

                return items

            # Handle objects with __dict__ attribute
            if hasattr(value, "__dict__"):
                return {
                    "type": type(value).__name__,
                    "attributes": self.format_value(
                        vars(value),
                        max_length=max_length,
                        depth=depth + 1,
                        max_depth=max_depth,
                    ),
                }

            # Handle other objects
            str_value = str(value)
            if len(str_value) > max_length:
                return f"{type(value).__name__}({str_value[:max_length-3]}...)"
            return f"{type(value).__name__}({str_value})"

        except Exception as e:
            self._logger.error("Error formatting value", exc_info=e)
            return f"Error formatting value: {type(value).__name__} - {str(e)}"

    def _format_error_traceback(self, tb, max_frames=None):
        """
        Format exception traceback for logging.

        Args:
            tb: Traceback object from the exception
            max_frames: Maximum number of frames to include (defaults to class constant)
        """
        if max_frames is None:
            max_frames = self.MAX_TRACEBACK_FRAMES

        try:
            frames = traceback.extract_tb(tb)
            frames = frames[-max_frames:]  # Take last N frames

            formatted_tb = []
            for frame in frames:
                formatted_tb.append(
                    f"{self.FRAME_INDENT}File '{frame.filename}', line {frame.lineno}, in {frame.name}"
                )
                if frame.line:
                    formatted_tb.append(f"{self.CODE_INDENT}{frame.line.strip()}")

            return (
                "\n".join(formatted_tb) if formatted_tb else "<no traceback available>"
            )

        except Exception as e:
            self._logger.error("Failed to format traceback", exc_info=e)
            return f"<error formatting traceback: {str(e)}>"

    def _get_error_contexts(self, error):
        """Extract caller and error contexts, keeping native types where possible."""
        try:
            tb = error.__traceback__

            # Extract caller frame (first frame in the traceback)
            caller_frame = tb.tb_frame
            caller_locals = {}
            for k, v in caller_frame.f_locals.items():
                if k.startswith("__"):
                    continue
                if isinstance(v, (logging.Logger, type(self))):
                    continue
                if "e" in k.lower() or isinstance(v, Exception):
                    continue

                # Use format_value but keep the returned structure
                caller_locals[k] = self.format_value(v)

            caller_context = {
                "function": caller_frame.f_code.co_name,
                "locals": caller_locals,
            }

            # Extract the deepest error frame where origin of error happens.
            while tb.tb_next is not None:
                tb = tb.tb_next
            error_frame = tb.tb_frame

            error_locals = {}
            for k, v in error_frame.f_locals.items():
                if k.startswith("__"):
                    continue
                if isinstance(v, (logging.Logger, type(self))):
                    continue
                if "e" in k.lower() or isinstance(v, Exception):
                    continue

                error_locals[k] = self.format_value(v)

            error_context = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_function": error_frame.f_code.co_name,
                "error_locals": error_locals,
                "traceback": self._format_error_traceback(error.__traceback__),
            }

            return caller_context, error_context

        except Exception as e:
            self._logger.error("Failed to extract error context", exc_info=e)
            return (
                {"function": "unknown", "locals": {}},  # Empty caller_context dict
                {
                    "error_type": "Unknown",
                    "error_message": "Failed to extract error context",
                    "error_function": "unknown",
                    "error_locals": {},
                    "traceback": "",
                },  # empty eror_context dict
            )

    def error(self, message, exc_info=None):
        """Log an error message with auto-generated error ID and send it to Databricks if configured."""
        log_entry = {
            "timestamp": datetime.now(),
            "level": "ERROR",
            "message": message,
            "error_type": "",
            "error_message": "",
            "error_function": "",
            "error_locals": {},
            "traceback": "",
            "caller_function": "",
            "caller_locals": {},
            "app_name": self._logger.name,
        }

        if isinstance(exc_info, BaseException):
            caller_context, error_context = self._get_error_contexts(exc_info)
            log_entry.update(error_context)
            log_entry["caller_function"] = caller_context["function"]
            log_entry["caller_locals"] = caller_context["locals"]

        # Write to Databricks first to get the error ID
        error_id = None
        """
        if self.env == "prod" and self.databricks_conn:
            try:
                error_id = self._write_to_databricks(log_entry)
            except Exception as e:
                self._logger.error(f"Failed to write to Databricks: {str(e)}")
        """
        # Include Error ID in message if available
        base_message = f"[Error ID: {error_id}] {message}" if error_id else message

        log_extra = {k: v for k, v in log_entry.items() if k != "message"}

        # Log the dictionary as extra metadata (this allows formatters to access it)
        self._logger.error(base_message, exc_info=exc_info, extra=log_extra)

        return error_id

    def info(self, message):
        """Log an informational message."""
        self._logger.info(message)

    def warning(self, message):
        """Log a warning message."""
        self._logger.warning(message)

    def critical(self, message):
        """Log a critical message."""
        self._logger.critical(message)

    def debug(self, message):
        """Log a debug message."""
        self._logger.debug(message)


class PerformanceLogger:
    """
    Performance logger to track execution metrics of functions.
    Focuses on the most important production metrics without adding significant overhead.
    When env "dev" is selected gives more detailed info.
    """

    def __init__(
        self,
        sampling_rate=1.0,  # for example 0.1 means log performance only 1 in 10 calls of the wrapped function.
        duration_threshold_ms=100,
        memory_threshold_mb=10,
        env="prod",
    ):
        self.logger = logging.getLogger("performance")
        self.sampling_rate = sampling_rate
        self.duration_threshold_ms = duration_threshold_ms
        self.memory_threshold_mb = memory_threshold_mb
        self.env = env.lower()
        self._setup_logger()

    def _setup_logger(self):
        """
        Configure logger with daily rotation at midnight, keeping 1 week of logs.
        Add only file formatter.
        """
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # create log dir if not exist
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        base_filename = "performance"
        rotating_handler = TimedRotatingFileHandler(
            filename=f"{logs_dir}/{base_filename}.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )

        rotating_handler.suffix = "%Y-%m-%d.log"
        rotating_handler.namer = lambda name: name.replace(".log", "")

        rotating_handler.setFormatter(formatter)
        self.logger.addHandler(rotating_handler)
        self.logger.setLevel(logging.INFO)

    def __call__(self, func):
        """Decorator to track function performance"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            if random.random() > self.sampling_rate:
                return func(*args, **kwargs)

            metrics, result = self._measure_execution(func, *args, **kwargs)

            if self._should_log_metrics(metrics):
                self._log_metrics(metrics)

            return result

        return wrapper

    def _measure_execution(self, func, *args, **kwargs):
        """Measure execution metrics of the function with additional dev metrics"""
        metrics = {
            "function": func.__name__,
        }

        gc.collect()
        process = psutil.Process(os.getpid())
        start_time = time.perf_counter()
        start_memory = process.memory_info()

        # Get CPU times if in dev environment
        if self.env == "dev":
            start_cpu = process.cpu_times()

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            metrics["error"] = str(e)
            raise

        gc.collect()
        end_time = time.perf_counter()
        end_memory = process.memory_info()

        # Basic metrics
        duration = end_time - start_time
        memory_delta = {
            "rss": (end_memory.rss - start_memory.rss) / (1024 * 1024),
            "vms": (end_memory.vms - start_memory.vms) / (1024 * 1024),
        }

        metrics.update(
            {
                "duration_ms": duration * 1000,
                "memory_delta_mb": memory_delta["rss"],  # Keep original metric
                "success": success,
            }
        )

        # Add detailed metrics for dev environment
        if self.env == "dev":
            end_cpu = process.cpu_times()
            cpu_usage = {
                "user": end_cpu.user - start_cpu.user,
                "system": end_cpu.system - start_cpu.system,
            }

            try:
                peak_memory = process.memory_info().peak_memory_info().rss / (
                    1024 * 1024
                )
            except Exception:
                peak_memory = None

            metrics.update(
                {
                    "detailed_memory": {
                        "rss_delta": memory_delta["rss"],
                        "vms_delta": memory_delta["vms"],
                        "peak_memory": peak_memory,
                    },
                    "cpu_usage": cpu_usage,
                }
            )

        return metrics, result

    def _should_log_metrics(self, metrics):
        """
        Determine if metrics should be logged based on thresholds.
        Note the OR operator!

        """
        return (
            metrics["duration_ms"] > self.duration_threshold_ms
            or abs(metrics["memory_delta_mb"]) > self.memory_threshold_mb
            or not metrics["success"]
        )

    def _log_metrics(self, metrics):
        """Log the performance metrics with detailed format for dev environment"""
        if self.env == "dev" and "detailed_memory" in metrics:
            # Format peak memory string separately
            peak_memory_str = (
                f"{metrics['detailed_memory']['peak_memory']:.2f}MB"
                if metrics["detailed_memory"]["peak_memory"]
                else "N/A"
            )

            # Detailed dev logging
            detailed_msg = (
                f"Performance metrics for {metrics['function']}:\n"
                f"Duration: {metrics['duration_ms']/1000:.3f}s\n"
                f"Memory RSS Δ: {metrics['detailed_memory']['rss_delta']:.2f}MB\n"
                f"Memory VMS Δ: {metrics['detailed_memory']['vms_delta']:.2f}MB\n"
                f"Peak Memory: {peak_memory_str}\n"
                f"CPU User: {metrics['cpu_usage']['user']:.2f}s\n"
                f"CPU System: {metrics['cpu_usage']['system']:.2f}s"
            )
            self.logger.info(detailed_msg)
        else:
            # Standard production logging
            self.logger.info(json.dumps(metrics, default=str))


# Create singleton instance
dash_logger = DashLogger(env="prod")
# perf_logger = PerformanceLogger(env="prod")
