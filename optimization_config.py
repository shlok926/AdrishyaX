"""
StegoForge v4.0 Backend Optimization Configuration
Centralized settings for performance tuning and resource management
"""

import os
from datetime import timedelta

# ===== CACHING CONFIGURATION =====
CACHE_CONFIG = {
    'enable_response_caching': True,
    'capacity_check_cache_ttl': 300,  # Cache capacity checks for 5 minutes
    'image_metadata_cache_ttl': 600,  # Cache image metadata for 10 minutes
    'curve_info_cache_ttl': 3600,  # Cache ECDH curve info for 1 hour
    'max_cache_entries': 1000,
    'cache_eviction_policy': 'lru'  # Least Recently Used
}

# ===== RATE LIMITING CONFIGURATION =====
RATE_LIMIT_CONFIG = {
    'global_limit': 60,  # Global requests per minute
    'per_endpoint_limits': {
        '/api/v1/encode': 10,  # Encoding is expensive
        '/api/v1/encode-batch': 5,  # Batch encoding more expensive
        '/api/v1/encode-split': 5,
        '/api/v1/encode-multi-carrier': 5,
        '/api/v1/decode': 20,  # Decoding cheaper
        '/api/v1/decode-batch': 10,
        '/api/v1/decode-split': 10,
        '/api/v1/analyze': 10,
        '/api/v1/capacity-check': 30,  # Light operation
        '/api/v1/capacity-info': 30,
        '/api/v1/video/embed': 3,  # Video operations most expensive
        '/api/v1/video/extract': 5,
        '/api/v1/steganalysis': 8,
        '/api/v1/preview': 15,
        '/api/v1/session/history': 50,  # Light operation
        'default': 30
    },
    'cleanup_interval': 60,  # Clean up old entries every 60 seconds
    'window_size': 60  # Rolling window size in seconds
}

# ===== IMAGE PROCESSING CONFIGURATION =====
IMAGE_CONFIG = {
    'max_image_dimension': 8192,  # Max width or height
    'max_image_pixels': 67108864,  # Max 8K pixels total
    'supported_formats': ['PNG', 'JPEG', 'BMP', 'GIF', 'WEBP'],
    'enable_lazy_loading': True,
    'enable_image_pooling': True,
    'max_pooled_images': 10,
    'compression_quality': 85,
    'verify_image_integrity': True
}

# ===== MEMORY OPTIMIZATION =====
MEMORY_CONFIG = {
    'enable_streaming': True,
    'stream_chunk_size': 1024 * 1024,  # 1MB chunks
    'max_memory_per_request': 500 * 1024 * 1024,  # 500MB max per request
    'enable_memory_pooling': True,
    'gc_threshold': (100000, 10, 10),  # Python garbage collection threshold
    'profile_memory': os.getenv('MEMORY_PROFILE', 'false').lower() == 'true'
}

# ===== COMPRESSION CONFIGURATION =====
COMPRESSION_CONFIG = {
    'enable_compression_cache': True,
    'cache_compression_results': True,
    'compression_cache_ttl': 3600,
    'max_compression_cache_size': 100 * 1024 * 1024,  # 100MB
    'default_compression_level': 6,  # zlib compression level (1-9)
    'zip_compression_level': 6,
    '7z_compression_level': 5  # 7-Zip compression (0-9)
}

# ===== VALIDATION CONFIGURATION =====
VALIDATION_CONFIG = {
    'strict_password_validation': True,
    'min_password_length': 8,
    'max_password_length': 256,
    'password_complexity_required': False,  # Optional enhancement
    'allowed_password_chars': 'all',  # 'all', 'alphanumeric', 'printable'
    'max_message_length': 10000,
    'validate_utf8': True,
    'enable_xss_prevention': True
}

# ===== TIMEOUT CONFIGURATION =====
TIMEOUT_CONFIG = {
    'request_timeout': 300,  # 5 minutes
    'encode_timeout': 120,  # 2 minutes for encoding
    'decode_timeout': 60,  # 1 minute for decoding
    'analysis_timeout': 30,  # 30 seconds for analysis
    'compression_timeout': 60,  # 1 minute for compression
    'io_timeout': 30  # 30 seconds for file I/O
}

# ===== LOGGING CONFIGURATION =====
LOGGING_CONFIG = {
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'enable_request_logging': True,
    'enable_performance_metrics': True,
    'log_response_times': True,
    'slow_request_threshold_ms': 1000  # Log requests slower than 1 second
}

# ===== MONITORING & METRICS =====
METRICS_CONFIG = {
    'enable_metrics': True,
    'track_endpoint_performance': True,
    'track_memory_usage': True,
    'track_cache_hit_rate': True,
    'metrics_retention_days': 7,
    'export_metrics_interval': 300  # Export every 5 minutes
}

# ===== SESSION CONFIGURATION =====
SESSION_CONFIG = {
    'max_sessions': 1000,
    'session_ttl': 3600,  # 1 hour
    'max_history_per_session': 100,
    'auto_cleanup_interval': 300,  # Clean up every 5 minutes
    'cleanup_expired_sessions': True
}

# ===== SECURITY CONFIGURATION =====
SECURITY_CONFIG = {
    'enable_csrf_protection': True,
    'enable_cors': True,
    'cors_origins': ['http://localhost:5000', 'http://127.0.0.1:5000'],
    'enable_hsts': True,
    'hsts_max_age': 31536000,
    'enable_csp': True,
    'enable_x_frame_options': True,
    'enable_x_content_type_options': True,
    'enable_x_xss_protection': True
}

# ===== OPTIMIZATION PROFILES =====
OPTIMIZATION_PROFILES = {
    'development': {
        'caching_enabled': False,
        'rate_limit_enabled': False,
        'metrics_enabled': True,
        'detailed_logging': True
    },
    'production': {
        'caching_enabled': True,
        'rate_limit_enabled': True,
        'metrics_enabled': True,
        'detailed_logging': False
    },
    'testing': {
        'caching_enabled': False,
        'rate_limit_enabled': False,
        'metrics_enabled': True,
        'detailed_logging': True
    }
}

# ===== RESOURCE LIMITS =====
RESOURCE_LIMITS = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'max_batch_files': 1000,
    'max_carriers': 20,
    'max_concurrent_requests': 100,
    'max_queue_size': 500
}

def get_optimization_profile():
    """Get the current optimization profile based on environment."""
    env = os.getenv('OPTIMIZATION_PROFILE', 'production')
    return OPTIMIZATION_PROFILES.get(env, OPTIMIZATION_PROFILES['production'])

def get_rate_limit_for_endpoint(endpoint):
    """Get rate limit for specific endpoint."""
    return RATE_LIMIT_CONFIG['per_endpoint_limits'].get(
        endpoint,
        RATE_LIMIT_CONFIG['per_endpoint_limits']['default']
    )
