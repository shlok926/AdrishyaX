"""
StegoForge v4.0 Enhanced Error Handling
Custom exceptions, error recovery, and detailed error reporting
"""

import logging
from flask import jsonify
from functools import wraps
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# ===== CUSTOM EXCEPTIONS =====
class StegoForgeException(Exception):
    """Base exception for StegoForge."""
    
    def __init__(self, message, error_code='UNKNOWN', status_code=500, details=None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)


class ValidationError(StegoForgeException):
    """Raised when input validation fails."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message,
            error_code='VALIDATION_ERROR',
            status_code=400,
            details=details
        )


class AuthenticationError(StegoForgeException):
    """Raised when authentication fails."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message,
            error_code='AUTHENTICATION_ERROR',
            status_code=403,
            details=details
        )


class InsufficientCapacityError(StegoForgeException):
    """Raised when carrier has insufficient capacity."""
    
    def __init__(self, message, required_bytes=0, available_bytes=0):
        details = {
            'required_bytes': required_bytes,
            'available_bytes': available_bytes
        }
        super().__init__(
            message,
            error_code='INSUFFICIENT_CAPACITY',
            status_code=400,
            details=details
        )


class ImageProcessingError(StegoForgeException):
    """Raised when image processing fails."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message,
            error_code='IMAGE_PROCESSING_ERROR',
            status_code=400,
            details=details
        )


class CompressionError(StegoForgeException):
    """Raised when compression fails."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message,
            error_code='COMPRESSION_ERROR',
            status_code=500,
            details=details
        )


class EncryptionError(StegoForgeException):
    """Raised when encryption/decryption fails."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message,
            error_code='ENCRYPTION_ERROR',
            status_code=500,
            details=details
        )


class RateLimitError(StegoForgeException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message, remaining=0, reset_time=None):
        details = {
            'remaining_requests': remaining,
            'reset_time': reset_time
        }
        super().__init__(
            message,
            error_code='RATE_LIMIT_EXCEEDED',
            status_code=429,
            details=details
        )


class MessageExpiredError(StegoForgeException):
    """Raised when embedded message has expired."""
    
    def __init__(self, message, expired_at=None):
        details = {'expired_at': expired_at}
        super().__init__(
            message,
            error_code='MESSAGE_EXPIRED',
            status_code=403,
            details=details
        )


class SelfDestructError(StegoForgeException):
    """Raised when message self-destructed."""
    
    def __init__(self, message, remaining_attempts=0):
        details = {'remaining_attempts': remaining_attempts}
        super().__init__(
            message,
            error_code='SELF_DESTRUCT_ACTIVATED',
            status_code=403,
            details=details
        )


class FileProcessingError(StegoForgeException):
    """Raised when file processing fails."""
    
    def __init__(self, message, filename=None, details=None):
        if details is None:
            details = {}
        if filename:
            details['filename'] = filename
        super().__init__(
            message,
            error_code='FILE_PROCESSING_ERROR',
            status_code=400,
            details=details
        )


class TimeoutError(StegoForgeException):
    """Raised when operation times out."""
    
    def __init__(self, message, operation_type=None, timeout_ms=None):
        details = {
            'operation_type': operation_type,
            'timeout_ms': timeout_ms
        }
        super().__init__(
            message,
            error_code='OPERATION_TIMEOUT',
            status_code=504,
            details=details
        )


# ===== ERROR HANDLERS =====
class ErrorHandler:
    """Centralized error handling for Flask application."""
    
    def __init__(self, app=None):
        self.app = app
        self.error_counts = {}
        self.error_timestamps = {}
    
    def register_handlers(self, app):
        """Register error handlers with Flask app."""
        self.app = app
        
        # StegoForge exceptions
        app.register_error_handler(StegoForgeException, self._handle_stegoforge_error)
        
        # Flask exceptions
        app.register_error_handler(400, self._handle_bad_request)
        app.register_error_handler(404, self._handle_not_found)
        app.register_error_handler(413, self._handle_payload_too_large)
        app.register_error_handler(429, self._handle_rate_limit)
        app.register_error_handler(500, self._handle_internal_error)
        app.register_error_handler(503, self._handle_service_unavailable)
    
    def _handle_stegoforge_error(self, error):
        """Handle custom StegoForge exceptions."""
        self._record_error(error.error_code)
        
        response = {
            'success': False,
            'error': error.message,
            'error_code': error.error_code,
            'timestamp': error.timestamp,
            'details': error.details
        }
        
        logger.error(
            f'StegoForge Error [{error.error_code}]: {error.message}',
            extra={'details': error.details}
        )
        
        return jsonify(response), error.status_code
    
    def _handle_bad_request(self, error):
        """Handle 400 Bad Request."""
        self._record_error('BAD_REQUEST')
        
        response = {
            'success': False,
            'error': 'Invalid request',
            'error_code': 'BAD_REQUEST',
            'timestamp': datetime.now().isoformat(),
            'details': {'description': str(error)}
        }
        
        logger.warning(f'Bad Request: {str(error)}')
        
        return jsonify(response), 400
    
    def _handle_not_found(self, error):
        """Handle 404 Not Found."""
        self._record_error('NOT_FOUND')
        
        response = {
            'success': False,
            'error': 'Endpoint not found',
            'error_code': 'NOT_FOUND',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning(f'Not Found: {error.description}')
        
        return jsonify(response), 404
    
    def _handle_payload_too_large(self, error):
        """Handle 413 Payload Too Large."""
        self._record_error('PAYLOAD_TOO_LARGE')
        
        response = {
            'success': False,
            'error': 'File too large (max 50MB)',
            'error_code': 'PAYLOAD_TOO_LARGE',
            'timestamp': datetime.now().isoformat(),
            'details': {'max_size_mb': 50}
        }
        
        logger.warning('Payload too large')
        
        return jsonify(response), 413
    
    def _handle_rate_limit(self, error):
        """Handle 429 Rate Limit."""
        self._record_error('RATE_LIMIT_EXCEEDED')
        
        response = {
            'success': False,
            'error': 'Rate limit exceeded',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning('Rate limit exceeded')
        
        return jsonify(response), 429
    
    def _handle_internal_error(self, error):
        """Handle 500 Internal Server Error."""
        self._record_error('INTERNAL_SERVER_ERROR')
        
        response = {
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.now().isoformat(),
            'request_id': None  # Could be added from request context
        }
        
        logger.error(f'Internal Server Error: {str(error)}', exc_info=True)
        
        return jsonify(response), 500
    
    def _handle_service_unavailable(self, error):
        """Handle 503 Service Unavailable."""
        self._record_error('SERVICE_UNAVAILABLE')
        
        response = {
            'success': False,
            'error': 'Service temporarily unavailable',
            'error_code': 'SERVICE_UNAVAILABLE',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.error(f'Service Unavailable: {str(error)}')
        
        return jsonify(response), 503
    
    def _record_error(self, error_code):
        """Record error for monitoring."""
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        self.error_timestamps[error_code] = datetime.now()
    
    def get_error_stats(self):
        """Get error statistics."""
        return {
            'error_counts': self.error_counts,
            'error_timestamps': self.error_timestamps,
            'total_errors': sum(self.error_counts.values())
        }


# ===== ERROR RECOVERY =====
def retry_on_failure(max_retries=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """Decorator for retrying failed operations with exponential backoff."""
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        logger.warning(
                            f'Attempt {attempt + 1} failed for {f.__name__}, '
                            f'retrying in {current_delay}s: {str(e)}'
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f'All {max_retries} attempts failed for {f.__name__}: {str(e)}'
                        )
            
            raise last_exception
        
        return decorated_function
    
    return decorator


# ===== SAFE EXECUTION WRAPPER =====
def safe_execute(func, default_return=None, log_errors=True):
    """Safely execute a function with error handling."""
    
    try:
        return func()
    
    except StegoForgeException:
        if log_errors:
            logger.error(f'StegoForge error in {func.__name__}: {str(e)}')
        raise
    
    except Exception as e:
        if log_errors:
            logger.error(
                f'Unexpected error in {func.__name__}: {str(e)}\n{traceback.format_exc()}'
            )
        
        return default_return


logger.info('Error handling system initialized')
