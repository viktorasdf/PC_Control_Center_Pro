import time
import psutil


_last_time = None
_last_read = 0
_last_write = 0


def get_disk_activity():
    """
    Реальная активность дисковых операций.

    usage — условная активность 0-100%
    read  — скорость чтения MB/s
    write — скорость записи MB/s
    """

    global _last_time
    global _last_read
    global _last_write

    try:
        counters = psutil.disk_io_counters()

        if counters is None:
            return {
                "usage": 0.0,
                "read": 0.0,
                "write": 0.0,
            }

        now = time.monotonic()

        read_bytes = counters.read_bytes
        write_bytes = counters.write_bytes

        if _last_time is None:
            _last_time = now
            _last_read = read_bytes
            _last_write = write_bytes

            return {
                "usage": 0.0,
                "read": 0.0,
                "write": 0.0,
            }

        elapsed = now - _last_time

        if elapsed <= 0:
            elapsed = 1.0

        read_delta = max(
            0,
            read_bytes - _last_read
        )

        write_delta = max(
            0,
            write_bytes - _last_write
        )

        read_mb = (
            read_delta / elapsed / 1024 / 1024
        )

        write_mb = (
            write_delta / elapsed / 1024 / 1024
        )

        _last_time = now
        _last_read = read_bytes
        _last_write = write_bytes

        activity = max(
            read_mb,
            write_mb
        )

        activity = max(
            0.0,
            min(
                100.0,
                activity
            )
        )

        return {
            "usage": activity,
            "read": read_mb,
            "write": write_mb,
        }

    except Exception:
        return {
            "usage": 0.0,
            "read": 0.0,
            "write": 0.0,
        }


def get_disk_space(path="C:\\"):
    """
    Заполненность диска.
    """

    try:
        disk = psutil.disk_usage(path)

        return {
            "percent": float(disk.percent),
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
        }

    except Exception:
        return {
            "percent": 0.0,
            "total": 0,
            "used": 0,
            "free": 0,
        }


def get_disk_info(path="C:\\"):
    """
    Полная информация о диске.
    """

    activity = get_disk_activity()
    space = get_disk_space(path)

    return {
        "activity": activity["usage"],
        "read": activity["read"],
        "write": activity["write"],
        "space": space["percent"],
        "total": space["total"],
        "used": space["used"],
        "free": space["free"],
    }
