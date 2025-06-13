"""
Configuration Gunicorn pour VentureLink.
"""
import multiprocessing
import os

# Variables d'environnement
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
threads = int(os.environ.get('GUNICORN_THREADS', 2))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 2))
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 200))

# Fichiers de logs
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Processus et démarrage
daemon = False
preload_app = True
graceful_timeout = 10
worker_tmp_dir = '/dev/shm' if os.path.exists('/dev/shm') else None

# Hooks et gestion des processus
def on_starting(server):
    """Log when server starts."""
    server.log.info("Starting Gunicorn server for VentureLink")

def on_exit(server):
    """Log when server exits."""
    server.log.info("Shutting down Gunicorn server for VentureLink")

def post_fork(server, worker):
    """Actions to run after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_fork(server, worker):
    """Actions to run before forking a worker."""
    pass 