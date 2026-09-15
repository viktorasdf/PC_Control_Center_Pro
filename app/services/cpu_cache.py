import psutil
import time


class CPUCache:

    def __init__(self):
        self._usage = 0.0
        self._timestamp = 0.0
        self._initialized = False

    def update(self):
        try:
            value = float(
                psutil.cpu_percent(
                    interval=None
                )
            )

            value = max(
                0.0,
                min(
                    100.0,
                    value
                )
            )

            self._usage = value
            self._timestamp = time.perf_counter()
            self._initialized = True

            return value

        except Exception as exc:
            print(
                f"[CPUCache] update error: {exc}"
            )
            return self._usage

    def get(self):
        return {
            "usage": round(
                self._usage,
                1
            ),
            "timestamp": self._timestamp,
            "available": self._initialized,
        }


_cpu_cache = CPUCache()


def update_cpu_cache():
    return _cpu_cache.update()


def get_cpu_cache():
    return _cpu_cache.get()
