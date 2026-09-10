from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    before_sleep_log
)
import logging
import time

logger = logging.getLogger(__name__)

def is_rate_limit_error(exception):
    """Check if exception is a rate limit error (429 or ResourceExhausted)"""
    error_str = str(exception).lower()
    return "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str or "too many requests" in error_str

# Reusable decorator for AI calls
# Faster backoff to avoid long request blocks; retries up to 3 times
retry_ai_call = retry(
    retry=retry_if_exception(is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=5, max=30),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
