"""
Gunicorn configuration for production
"""
import multiprocessing

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = 1  # Single worker to stay within 512MB Replit memory limit
worker_class = 'gthread'  # Use threads for concurrency instead of processes
threads = 4  # Handle multiple requests with threads
worker_connections = 1000
timeout = 300  # Increased for video processing
keepalive = 2
preload_app = True  # Load app once before forking
max_requests = 1000  # Recycle worker after 1000 requests
max_requests_jitter = 50  # Add randomness to avoid simultaneous recycling

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'ai-tennis-coach'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
# keyfile = None
# certfile = None
