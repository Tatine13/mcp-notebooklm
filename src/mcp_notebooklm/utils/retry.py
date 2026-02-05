"""Retry logic and error handling utilities."""

import asyncio
from functools import wraps
from typing import Callable, Any, Optional
from loguru import logger

from .exceptions import RateLimitError, TimeoutError


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
        
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(RateLimitError,))
        async def fetch_data():
            # Might raise RateLimitError
            return await api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__} - {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e, current_delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback error: {callback_error}")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            # Should never reach here
            raise RuntimeError(f"Unexpected exit from retry loop in {func.__name__}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__} - {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e, current_delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback error: {callback_error}")
                    
                    asyncio.run(asyncio.sleep(current_delay))
                    current_delay *= backoff
                    attempt += 1
            
            raise RuntimeError(f"Unexpected exit from retry loop in {func.__name__}")
        
        # Return appropriate wrapper based on whether func is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def rate_limit_retry(max_attempts: int = 5, base_delay: float = 2.0):
    """
    Specialized retry for rate limit errors with longer delays.
    
    Args:
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds (increases with each retry)
    """
    return retry(
        max_attempts=max_attempts,
        delay=base_delay,
        backoff=2.0,
        exceptions=(RateLimitError,),
    )


def timeout_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Specialized retry for timeout errors.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Delay between retries
    """
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=1.5,
        exceptions=(TimeoutError, asyncio.TimeoutError),
    )


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    
    States:
        - CLOSED: Normal operation
        - OPEN: Failing, reject requests
        - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._failures = 0
        self._last_failure_time = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._half_open_calls = 0
    
    @property
    def state(self) -> str:
        """Get current circuit state."""
        if self._state == "OPEN":
            # Check if we should try half-open
            if self._last_failure_time:
                elapsed = asyncio.get_event_loop().time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = "HALF_OPEN"
                    self._half_open_calls = 0
                    logger.info("Circuit breaker entering HALF_OPEN state")
        
        return self._state
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        state = self.state
        
        if state == "CLOSED":
            return True
        elif state == "OPEN":
            return False
        elif state == "HALF_OPEN":
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        
        return True
    
    def record_success(self):
        """Record a successful execution."""
        if self._state == "HALF_OPEN":
            # If enough successes in half-open, close the circuit
            self._state = "CLOSED"
            self._failures = 0
            self._half_open_calls = 0
            logger.info("Circuit breaker CLOSED (recovered)")
        elif self._state == "CLOSED":
            self._failures = 0
    
    def record_failure(self):
        """Record a failed execution."""
        self._failures += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        
        if self._state == "HALF_OPEN":
            # Back to open
            self._state = "OPEN"
            logger.warning("Circuit breaker OPEN (half-open test failed)")
        elif self._state == "CLOSED" and self._failures >= self.failure_threshold:
            self._state = "OPEN"
            logger.warning(f"Circuit breaker OPEN after {self._failures} failures")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Raises:
            RuntimeError: If circuit is OPEN
        """
        if not self.can_execute():
            raise RuntimeError("Circuit breaker is OPEN - too many failures")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


# Global circuit breakers for different services
_notebooklm_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)


def get_notebooklm_circuit() -> CircuitBreaker:
    """Get the global NotebookLM circuit breaker."""
    return _notebooklm_circuit
