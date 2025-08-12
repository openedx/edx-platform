import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("WEB_CONCURRENCY", max(2, multiprocessing.cpu_count() * 2 + 1)))
threads = int(os.environ.get("GUNICORN_THREADS", 2))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))
loglevel = os.environ.get("LOG_LEVEL", "info")
accesslog = os.environ.get("GUNICORN_ACCESSLOG", "-")
errorlog = os.environ.get("GUNICORN_ERRORLOG", "-")
preload_app = os.environ.get("GUNICORN_PRELOAD", "false").lower() == "true"

# Basic request logging

def pre_request(worker, req):  # noqa: D401
    worker.log.debug("%s %s", req.method, req.path)