"""
Unit tests for retry functionality
Author: Conrad Vaslin - xAI Finance Tutor
"""

import pytest
import time
from src.retry_utils import (
    retry_operation, RetryableOperation, retry_with_fallback,
    retry_io_operation, get_retry_stats
)


class TestRetryUtils:
    """Test retry functionality"""

    def test_successful_first_attempt(self):
        """Test operation succeeds on first attempt"""
        call_count = 0

        @retry_operation(max_attempts=3)
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = always_succeeds()

        assert result == "success"
        assert call_count == 1

    def test_succeeds_after_retry(self):
        """Test operation succeeds after retrying"""
        call_count = 0

        @retry_operation(max_attempts=3, delay=0.1)
        def succeeds_on_second_attempt():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = succeeds_on_second_attempt()

        assert result == "success"
        assert call_count == 2

    def test_exhausts_retries(self):
        """Test all retries are exhausted"""
        call_count = 0

        @retry_operation(max_attempts=3, delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError, match="Permanent failure"):
            always_fails()

        assert call_count == 3

    def test_exponential_backoff(self):
        """Test exponential backoff timing"""
        attempts = []

        @retry_operation(max_attempts=3, delay=0.1, backoff_factor=2.0)
        def track_timing():
            attempts.append(time.time())
            if len(attempts) < 3:
                raise ValueError("Retry")
            return "done"

        track_timing()

        # Check delays increase
        if len(attempts) >= 3:
            delay1 = attempts[1] - attempts[0]
            delay2 = attempts[2] - attempts[1]
            # Second delay should be roughly 2x first delay
            assert delay2 > delay1

    def test_specific_exceptions(self):
        """Test catching only specific exceptions"""
        call_count = 0

        @retry_operation(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test")

        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count == 3

        # Reset
        call_count = 0

        @retry_operation(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Test")

        # TypeError should not be retried
        with pytest.raises(TypeError):
            raises_type_error()

        assert call_count == 1

    def test_on_retry_callback(self):
        """Test on_retry callback is called"""
        retry_calls = []

        def log_retry(attempt, exception):
            retry_calls.append((attempt, str(exception)))

        @retry_operation(max_attempts=3, delay=0.1, on_retry=log_retry)
        def fails_twice():
            if len(retry_calls) < 2:
                raise ValueError("Fail")
            return "success"

        result = fails_twice()

        assert result == "success"
        assert len(retry_calls) == 2

    def test_on_failure_callback(self):
        """Test on_failure callback is called"""
        failure_info = []

        def log_failure(func_name, exception, attempts):
            failure_info.append((func_name, str(exception), attempts))

        @retry_operation(max_attempts=2, delay=0.1, on_failure=log_failure)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fails()

        assert len(failure_info) == 1
        assert failure_info[0][0] == "always_fails"
        assert failure_info[0][2] == 2

    def test_retryable_operation_context(self):
        """Test RetryableOperation context manager"""
        call_count = 0

        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry")
            return "success"

        op = RetryableOperation("test_operation", max_attempts=3, delay=0.1)
        result = op.execute(test_func)

        assert result == "success"
        assert call_count == 2

    def test_retry_with_fallback_success(self):
        """Test retry_with_fallback uses primary"""
        primary_calls = 0
        fallback_calls = 0

        def primary():
            nonlocal primary_calls
            primary_calls += 1
            return "primary"

        def fallback():
            nonlocal fallback_calls
            fallback_calls += 1
            return "fallback"

        result = retry_with_fallback(primary, fallback, max_attempts=2, delay=0.1)

        assert result == "primary"
        assert primary_calls == 1
        assert fallback_calls == 0

    def test_retry_with_fallback_uses_fallback(self):
        """Test retry_with_fallback uses fallback after primary fails"""
        primary_calls = 0
        fallback_calls = 0

        def primary():
            nonlocal primary_calls
            primary_calls += 1
            raise ValueError("Primary fails")

        def fallback():
            nonlocal fallback_calls
            fallback_calls += 1
            return "fallback"

        result = retry_with_fallback(primary, fallback, max_attempts=2, delay=0.1)

        assert result == "fallback"
        assert primary_calls == 2
        assert fallback_calls == 1

    def test_retry_io_operation_decorator(self):
        """Test retry_io_operation decorator"""
        call_count = 0

        @retry_io_operation
        def io_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise IOError("IO Error")
            return "success"

        result = io_operation()

        assert result == "success"
        assert call_count == 2

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        delays = []

        @retry_operation(
            max_attempts=5,
            delay=1.0,
            backoff_factor=10.0,
            max_delay=2.0
        )
        def track_delays():
            delays.append(time.time())
            if len(delays) < 5:
                raise ValueError("Retry")
            return "done"

        track_delays()

        # Check that later delays don't exceed max_delay
        if len(delays) >= 4:
            last_delay = delays[-1] - delays[-2]
            assert last_delay <= 2.5  # Some tolerance for timing

    def test_preserves_function_metadata(self):
        """Test decorator preserves function metadata"""

        @retry_operation(max_attempts=3)
        def my_function():
            """My docstring"""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring"
