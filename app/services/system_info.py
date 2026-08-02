import platform
import psutil


def get_cpu_info():
    return {
        "usage": psutil.cpu_percent(interval=None),
        "cores": psutil.cpu_count(logical=False) or 0,
        "threads": psutil.cpu_count(logical=True) or 0,
        "name": platform.processor() or "Unknown CPU",
    }


def get_memory_info():
    memory = psutil.virtual_memory()

    return {
        "used": memory.used,
        "total": memory.total,
        "percent": memory.percent,
    }


def get_system_info():
    return {
        "computer": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }