import os
import time

try:
    import psutil
except Exception:
    psutil = None


def get_system_health(db_path):
    cpu_usage = psutil.cpu_percent(interval=0.2) if psutil else None
    memory_usage = psutil.virtual_memory().percent if psutil else None
    disk_usage = psutil.disk_usage(os.path.dirname(db_path)).percent if psutil else None
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    uptime_seconds = int(time.time() - psutil.boot_time()) if psutil else None

    return {
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
        'db_size': db_size,
        'uptime_seconds': uptime_seconds,
    }
