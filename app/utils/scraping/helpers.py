"""
Scraping helper functions and decorators.
"""

import time
import random
import logging
import functools
from typing import Any, Callable, Dict, Optional, Tuple, Type
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 2.0, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """Decorator for retrying functions with exponential backoff"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    delay = base_delay * (2 ** (retries - 1)) + random.uniform(0, 1)
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {delay:.2f}s due to: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter for API/web requests"""
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = Lock()

    def __call__(self, func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                while self.calls and now - self.calls[0] > self.time_window:
                    self.calls.popleft()
                
                if len(self.calls) >= self.max_calls:
                    wait_time = self.time_window - (now - self.calls[0])
                    if wait_time > 0:
                        logger.info(f"Rate limit reached. Waiting {wait_time:.2f}s")
                        time.sleep(wait_time)
                
                self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
