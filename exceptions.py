"""
Custom exception classes for Job Market AI Analyzer
Provides better error handling and debugging
"""
from typing import Optional


class JobMarketAnalyzerError(Exception):
    """Base exception for Job Market Analyzer"""
    pass


class CVProcessingError(JobMarketAnalyzerError):
    """Raised when CV processing fails"""
    pass


class JobScrapingError(JobMarketAnalyzerError):
    """Raised when job scraping fails"""
    pass


class APIError(JobMarketAnalyzerError):
    """Raised when API calls fail"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[float] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class DatabaseError(JobMarketAnalyzerError):
    """Raised when database operations fail"""
    pass


class ConfigurationError(JobMarketAnalyzerError):
    """Raised when configuration is invalid or missing"""
    pass


class ValidationError(JobMarketAnalyzerError):
    """Raised when input validation fails"""
    pass


class AuthenticationError(JobMarketAnalyzerError):
    """Raised when authentication fails"""
    pass

