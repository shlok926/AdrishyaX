# Backend Optimization - Developer Quick Reference

## 🚀 Quick Start (5 Minutes)

### Step 1: Import
```python
from optimization_config import RATE_LIMIT_CONFIG
from performance_utils import AdvancedRateLimiter, rate_limit_by_endpoint
from error_handler import ValidationError, ErrorHandler, InputValidator
```

### Step 2: Initialize
```python
# In Flask app initialization
limiter = AdvancedRateLimiter(RATE_LIMIT_CONFIG['per_endpoint_limits'])
error_handler = ErrorHandler()
error_handler.register_handlers(app)
```

### Step 3: Apply to Routes
```python
@app.route('/api/v1/encode', methods=['POST'])
@rate_limit_by_endpoint(limiter)
def api_encode():
    try:
        # Your code
        pass
    except StegoForgeException:
        raise  # Handled by error_handler
```

---

## 🔧 Common Tasks

### Validate Input
```python
# Password
valid, msg = InputValidator.validate_password(password)
if not valid:
    raise ValidationError(msg)

# Image
valid, msg = InputValidator.validate_image_file(image_file)
if not valid:
    raise ImageProcessingError(msg)

# Message
valid, msg = InputValidator.validate_message(message)
if not valid:
    raise ValidationError(msg)
```

### Cache Data
```python
from performance_utils import LRUCache

cache = LRUCache(max_size=1000, ttl=300)

# Get
cached = cache.get(key)
if cached:
    return cached

# Compute...

# Put
cache.put(key, result)
```

### Rate Limiting
```python
# Check remaining requests
remaining = limiter.get_remaining(client_ip, endpoint)

# Manual cleanup
removed = limiter.cleanup()
```

### Circuit Breaker
```python
from performance_utils import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

if breaker.is_open():
    raise Exception('Service temporarily unavailable')

try:
    # Critical operation
    breaker.record_success()
except:
    breaker.record_failure()
    raise
```

### Performance Monitoring
```python
from performance_utils import PerformanceMonitor

monitor = PerformanceMonitor()

# Record metrics
monitor.record_request(endpoint, duration_ms, status_code)

# Get stats
stats = monitor.get_stats('/api/v1/encode')
print(f"Avg response: {stats['avg_time_ms']}ms")

# Health metrics
health = monitor.get_health_metrics()
print(f"Memory: {health['memory_mb']}MB")
```

---

## ⚡ Performance Tips

### Cache Expensive Operations
```python
# DON'T: Recompute every time
capacity = calculate_max_payload(image)

# DO: Cache result
cache = LRUCache(ttl=600)
cached = cache.get(image_hash)
if cached:
    capacity = cached
else:
    capacity = calculate_max_payload(image)
    cache.put(image_hash, capacity)
```

### Use Memory Pool for Buffers
```python
# DON'T: Create new BytesIO each time
buffer = io.BytesIO()

# DO: Use memory pool
from performance_utils import MemoryPool
pool = MemoryPool(max_buffers=10)
buffer = pool.acquire()
try:
    # Use buffer
    pass
finally:
    pool.release(buffer)
```

### Stream Large Files
```python
# DON'T: Load entire file
data = file.read()

# DO: Process in chunks
chunk_size = 1024 * 1024
while True:
    chunk = file.read(chunk_size)
    if not chunk:
        break
    # Process chunk
```

### Retry Failed Operations
```python
from error_handler import retry_on_failure

@retry_on_failure(max_retries=3, exceptions=(IOError,))
def critical_operation():
    # Automatically retries with exponential backoff
    pass
```

---

## 🎨 Custom Exceptions

### When to Use Each

```python
ValidationError         # Invalid input (password, image, message)
AuthenticationError     # Wrong password, access denied
InsufficientCapacityError  # Payload too large for carrier
ImageProcessingError    # Image validation or processing fails
CompressionError        # Compression operation fails
EncryptionError         # Encryption/decryption fails
RateLimitError          # Rate limit exceeded
MessageExpiredError     # TTL expired
SelfDestructError       # Max attempts exceeded
FileProcessingError     # File handling issues
TimeoutError            # Operation timeout

# Example
if payload_size > capacity:
    raise InsufficientCapacityError(
        'Payload too large',
        required_bytes=payload_size,
        available_bytes=capacity
    )
```

---

## 📊 Configuration Adjustments

### Increase Rate Limits for Heavy Load
```python
RATE_LIMIT_CONFIG['global_limit'] = 120  # Default: 60
RATE_LIMIT_CONFIG['per_endpoint_limits']['default'] = 60  # Default: 30
```

### Increase Cache Size
```python
CACHE_CONFIG['max_cache_entries'] = 2000  # Default: 1000
CACHE_CONFIG['capacity_check_cache_ttl'] = 600  # Default: 300
```

### Reduce Memory Usage
```python
MEMORY_CONFIG['enable_streaming'] = True
MEMORY_CONFIG['stream_chunk_size'] = 512 * 1024  # 512KB chunks
MEMORY_CONFIG['max_memory_per_request'] = 100 * 1024 * 1024  # 100MB
```

---

## 🔍 Debugging

### Check Health Status
```bash
curl http://127.0.0.1:5000/api/v1/health | python -m json.tool
```

### View Endpoint Metrics
```python
stats = performance_monitor.get_stats()
for endpoint, metrics in stats.items():
    print(f"{endpoint}:")
    print(f"  Requests: {metrics['total_requests']}")
    print(f"  Success: {metrics['success_count']}")
    print(f"  Avg Time: {metrics['avg_time_ms']}ms")
```

### Check Rate Limit Status
```python
remaining = limiter.get_remaining('192.168.1.1', '/api/v1/encode')
print(f"Remaining requests: {remaining}")
```

### View Error Statistics
```python
errors = error_handler.get_error_stats()
print(f"Total errors: {errors['total_errors']}")
print(f"By type: {errors['error_counts']}")
```

---

## 🆘 Common Issues

### "Rate limit exceeded"
```
Solution: 
- Check remaining: limiter.get_remaining(ip, endpoint)
- Adjust limit: RATE_LIMIT_CONFIG['per_endpoint_limits']
- Implement caching to reduce requests
```

### "Service temporarily unavailable"
```
Solution:
- Check circuit breaker: breaker.get_status()
- Monitor error rate
- Increase failure_threshold or recovery_timeout
```

### "Memory usage high"
```
Solution:
- Enable streaming: MEMORY_CONFIG['enable_streaming'] = True
- Reduce cache size: CACHE_CONFIG['max_cache_entries']
- Check cache stats: cache.get_stats()
```

### "Slow response times"
```
Solution:
- Check endpoint stats: monitor.get_stats(endpoint)
- Increase cache TTL
- Profile with: python benchmark_optimizations.py
```

---

## 📝 Code Snippets

### Optimized Endpoint Template
```python
@app.route('/api/v1/myendpoint', methods=['POST'])
@rate_limit_by_endpoint(limiter)
@monitor_performance(performance_monitor)
def api_myendpoint():
    try:
        # Validate inputs
        valid, msg = InputValidator.validate_password(password)
        if not valid:
            raise ValidationError(msg)
        
        # Check cache if applicable
        cached = cache.get(request_key)
        if cached:
            return jsonify(cached), 200
        
        # Check circuit breaker
        if circuit_breaker.is_open():
            raise StegoForgeException('Service unavailable')
        
        # Your logic here
        result = perform_operation()
        
        # Cache result
        cache.put(request_key, result)
        
        circuit_breaker.record_success()
        return jsonify(result), 200
    
    except StegoForgeException:
        circuit_breaker.record_failure()
        raise
    except Exception as e:
        circuit_breaker.record_failure()
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        raise
```

### Retry Logic Template
```python
@retry_on_failure(max_retries=3, exceptions=(IOError, OSError))
def critical_file_operation():
    # This will automatically retry up to 3 times on IOError/OSError
    # with exponential backoff
    perform_file_operation()
```

### Memory Pool Usage Template
```python
def process_large_file(file_obj):
    buffer = memory_pool.acquire()
    try:
        # Use buffer for processing
        file_obj.read()  # or other operations
        buffer.write(processed_data)
        return buffer.getvalue()
    finally:
        memory_pool.release(buffer)
```

---

## 📚 References

| Component | File | Key Class |
|-----------|------|-----------|
| Configuration | `optimization_config.py` | - |
| Caching | `performance_utils.py` | `LRUCache` |
| Rate Limiting | `performance_utils.py` | `AdvancedRateLimiter` |
| Monitoring | `performance_utils.py` | `PerformanceMonitor` |
| Validation | `performance_utils.py` | `InputValidator` |
| Memory Pool | `performance_utils.py` | `MemoryPool` |
| Circuit Breaker | `performance_utils.py` | `CircuitBreaker` |
| Error Handling | `error_handler.py` | `ErrorHandler` |
| Exceptions | `error_handler.py` | `StegoForgeException` |

---

## ✅ Best Practices

1. **Always validate input** - Use `InputValidator` for all user inputs
2. **Use custom exceptions** - Provide detailed error context
3. **Cache expensive operations** - 40-70% performance gain
4. **Monitor metrics** - Track performance and errors
5. **Implement circuit breaker** - For critical operations
6. **Handle timeouts** - Prevent hanging requests
7. **Clean up resources** - Use try/finally with pools
8. **Log errors with context** - Include full exception details
9. **Test under load** - Use `locust` for load testing
10. **Review metrics regularly** - Optimize based on actual usage

---

**Quick Reference Version:** 4.0.0  
**Last Updated:** 2024
