#!/usr/bin/env python3
"""
Auto-retry utilities for failed operations
Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

import time
import logging
from typing import Callable, Any, Optional, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""

    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_DELAY = 1.0  # seconds
    DEFAULT_BACKOFF_FACTOR = 2.0  # exponential backoff
    DEFAULT_MAX_DELAY = 30.0  # seconds


def retry_operation(
    max_attempts: int = RetryConfig.DEFAULT_MAX_ATTEMPTS,
    delay: float = RetryConfig.DEFAULT_DELAY,
    backoff_factor: float = RetryConfig.DEFAULT_BACKOFF_FACTOR,
    max_delay: float = RetryConfig.DEFAULT_MAX_DELAY,
    exceptions: Tuple = (Exception,),
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None
):
    """
    Decorator for automatic retry of failed operations

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries (default: 30.0)
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Callback function called on each retry (receives attempt number, exception)
        on_failure: Callback function called when all retries exhausted

    Returns:
        Decorated function with retry logic

    Example:
        @retry_operation(max_attempts=3, delay=1.0)
        def process_file(filename):
            # This will retry up to 3 times if it fails
            return do_something(filename)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    # Attempt the operation
                    result = func(*args, **kwargs)

                    # Success!
                    if attempt > 1:
                        logger.info(
                            f"✓ {func.__name__} succeeded on attempt {attempt}/{max_attempts}"
                        )

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        # Final attempt failed
                        logger.error(
                            f"✗ {func.__name__} failed after {max_attempts} attempts: {e}"
                        )

                        if on_failure:
                            on_failure(func.__name__, last_exception, attempt)

                        raise

                    # Not the last attempt, retry
                    logger.warning(
                        f"⚠ {func.__name__} failed on attempt {attempt}/{max_attempts}: {e}"
                    )
                    logger.info(f"  Retrying in {current_delay:.1f} seconds...")

                    if on_retry:
                        on_retry(attempt, last_exception)

                    time.sleep(current_delay)

                    # Exponential backoff
                    current_delay = min(current_delay * backoff_factor, max_delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


class RetryableOperation:
    """
    Context manager for retryable operations with manual control
    """

    def __init__(
        self,
        operation_name: str,
        max_attempts: int = RetryConfig.DEFAULT_MAX_ATTEMPTS,
        delay: float = RetryConfig.DEFAULT_DELAY,
        backoff_factor: float = RetryConfig.DEFAULT_BACKOFF_FACTOR
    ):
        """
        Initialize retryable operation

        Args:
            operation_name: Name of the operation for logging
            max_attempts: Maximum retry attempts
            delay: Initial delay between retries
            backoff_factor: Backoff multiplier
        """
        self.operation_name = operation_name
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.current_attempt = 0
        self.current_delay = delay

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            self.current_attempt = attempt

            try:
                result = func(*args, **kwargs)

                if attempt > 1:
                    logger.info(
                        f"✓ {self.operation_name} succeeded on attempt {attempt}/{self.max_attempts}"
                    )

                return result

            except Exception as e:
                last_exception = e

                if attempt == self.max_attempts:
                    logger.error(
                        f"✗ {self.operation_name} failed after {self.max_attempts} attempts: {e}"
                    )
                    raise

                logger.warning(
                    f"⚠ {self.operation_name} failed on attempt {attempt}/{self.max_attempts}: {e}"
                )
                logger.info(f"  Retrying in {self.current_delay:.1f} seconds...")

                time.sleep(self.current_delay)
                self.current_delay *= self.backoff_factor

        raise last_exception

    def __enter__(self):
        """Enter context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        return False


def retry_with_fallback(
    primary_func: Callable,
    fallback_func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0
) -> Any:
    """
    Try primary function with retries, fall back to alternative if all fail

    Args:
        primary_func: Primary function to try
        fallback_func: Fallback function if primary fails
        max_attempts: Max attempts for primary function
        delay: Delay between retries

    Returns:
        Result from primary or fallback function

    Example:
        result = retry_with_fallback(
            lambda: convert_with_ocr(pdf),
            lambda: convert_without_ocr(pdf),
            max_attempts=3
        )
    """
    current_delay = delay

    for attempt in range(1, max_attempts + 1):
        try:
            result = primary_func()
            if attempt > 1:
                logger.info(f"✓ Primary function succeeded on attempt {attempt}")
            return result

        except Exception as e:
            if attempt == max_attempts:
                logger.warning(
                    f"⚠ Primary function failed after {max_attempts} attempts, trying fallback"
                )

                try:
                    result = fallback_func()
                    logger.info("✓ Fallback function succeeded")
                    return result

                except Exception as fallback_error:
                    logger.error(f"✗ Fallback function also failed: {fallback_error}")
                    raise

            logger.warning(f"⚠ Attempt {attempt} failed: {e}")
            time.sleep(current_delay)
            current_delay *= 2


# Convenience decorators with preset configurations

def retry_io_operation(func: Callable) -> Callable:
    """Retry decorator optimized for I/O operations"""
    return retry_operation(
        max_attempts=3,
        delay=0.5,
        backoff_factor=2.0,
        exceptions=(IOError, OSError)
    )(func)


def retry_network_operation(func: Callable) -> Callable:
    """Retry decorator optimized for network operations"""
    return retry_operation(
        max_attempts=5,
        delay=2.0,
        backoff_factor=2.0,
        max_delay=30.0,
        exceptions=(ConnectionError, TimeoutError)
    )(func)


def retry_conversion_operation(func: Callable) -> Callable:
    """Retry decorator optimized for PDF conversion"""
    return retry_operation(
        max_attempts=3,
        delay=1.0,
        backoff_factor=1.5,
        exceptions=(RuntimeError, ValueError, Exception)
    )(func)


# Global retry statistics
class RetryStatistics:
    """Track retry statistics"""

    def __init__(self):
        self.total_operations = 0
        self.total_retries = 0
        self.total_failures = 0
        self.operations = {}

    def record_retry(self, operation_name: str):
        """Record a retry"""
        self.total_retries += 1
        if operation_name not in self.operations:
            self.operations[operation_name] = {'retries': 0, 'failures': 0}
        self.operations[operation_name]['retries'] += 1

    def record_failure(self, operation_name: str):
        """Record a failure"""
        self.total_failures += 1
        if operation_name not in self.operations:
            self.operations[operation_name] = {'retries': 0, 'failures': 0}
        self.operations[operation_name]['failures'] += 1

    def get_stats(self) -> dict:
        """Get statistics"""
        return {
            'total_operations': self.total_operations,
            'total_retries': self.total_retries,
            'total_failures': self.total_failures,
            'by_operation': self.operations
        }

    def reset(self):
        """Reset statistics"""
        self.total_operations = 0
        self.total_retries = 0
        self.total_failures = 0
        self.operations = {}


# Global statistics instance
_retry_stats = RetryStatistics()


def get_retry_stats() -> RetryStatistics:
    """Get global retry statistics"""
    return _retry_stats
