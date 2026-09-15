
"""
monitoring.py
PC Control Center Pro

System monitoring service.

Provides:
    - CPU usage
    - RAM usage
    - Disk usage
    - Network download/upload speed
    - GPU usage
    - GPU engine usage
    - GPU information
    - GPU process list

Compatible with:
    Windows 10/11
    Python 3.13
    psutil
    current gpu_info.py

IMPORTANT:
    gpu_info.py is the single source of truth for GPU data.
    This module does not implement GPU engine detection itself.
"""

from __future__ import annotations

import threading
import time
from typing import Any

import psutil

from app.services.gpu_info import (
    get_gpu_info,
    get_gpu_processes,
    get_gpu_engine_summary,
)


# ============================================================================
# Configuration
# ============================================================================

DISK_CACHE_TTL = 1.0

GPU_PROCESS_CACHE_TTL = 0.8
GPU_PROCESS_HOLD_TIME = 2.0


# ============================================================================
# Internal state
# ============================================================================

_lock = threading.RLock()


# ============================================================================
# Network state
# ============================================================================

_last_network_time = 0.0
_last_network_bytes_sent = 0
_last_network_bytes_recv = 0

_network_download = 0.0
_network_upload = 0.0


# ============================================================================
# Disk state
# ============================================================================

_last_disk_time = 0.0
_last_disk_percent = 0.0


# ============================================================================
# GPU state
# ============================================================================

_last_gpu_info: dict[str, Any] | None = None

_last_gpu_engine_summary: dict[str, Any] | None = None

_last_gpu_process_time = 0.0
_last_gpu_processes: list[dict[str, Any]] = []

_last_gpu_process_nonempty_time = 0.0


# ============================================================================
# Generic helpers
# ============================================================================

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    try:
        result = float(value)

        if result != result:
            return default

        if result < 0:
            return default

        return result

    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Safely convert a value to int."""

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _clamp_percent(
    value: Any,
) -> float:
    """Convert value to percentage in range 0..100."""

    number = _safe_float(value)

    if number < 0:
        return 0.0

    if number > 100:
        return 100.0

    return number


# ============================================================================
# CPU
# ============================================================================

def get_cpu_usage() -> float:
    """
    Return current CPU usage percentage.

    Non-blocking.
    """

    try:
        return _clamp_percent(
            psutil.cpu_percent(
                interval=None
            )
        )

    except Exception as exc:
        print(
            f"[Monitoring] CPU error: {exc}"
        )

        return 0.0


# ============================================================================
# RAM
# ============================================================================

def get_ram_usage() -> float:
    """Return RAM usage percentage."""

    try:
        memory = psutil.virtual_memory()

        return _clamp_percent(
            memory.percent
        )

    except Exception as exc:
        print(
            f"[Monitoring] RAM error: {exc}"
        )

        return 0.0


def get_memory_info() -> dict[str, float]:
    """Return detailed RAM information."""

    try:
        memory = psutil.virtual_memory()

        return {
            "total": float(memory.total),
            "available": float(memory.available),
            "used": float(memory.used),
            "percent": _clamp_percent(
                memory.percent
            ),
        }

    except Exception as exc:
        print(
            f"[Monitoring] Memory error: {exc}"
        )

        return {
            "total": 0.0,
            "available": 0.0,
            "used": 0.0,
            "percent": 0.0,
        }


# ============================================================================
# Disk
# ============================================================================

def get_disk_usage(
    path: str = "C:\\",
) -> float:
    """Return disk usage percentage."""

    global _last_disk_time
    global _last_disk_percent

    now = time.monotonic()

    with _lock:

        if (
            now - _last_disk_time
            < DISK_CACHE_TTL
        ):
            return _last_disk_percent

        try:
            usage = psutil.disk_usage(path)

            _last_disk_percent = _clamp_percent(
                usage.percent
            )

            _last_disk_time = now

            return _last_disk_percent

        except Exception as exc:
            print(
                f"[Monitoring] Disk error: {exc}"
            )

            return _last_disk_percent


def get_disk_info(
    path: str = "C:\\",
) -> dict[str, Any]:
    """Return detailed disk information."""

    try:
        usage = psutil.disk_usage(path)

        return {
            "path": path,
            "total": int(usage.total),
            "used": int(usage.used),
            "free": int(usage.free),
            "percent": _clamp_percent(
                usage.percent
            ),
        }

    except Exception as exc:
        print(
            f"[Monitoring] Disk info error: {exc}"
        )

        return {
            "path": path,
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0.0,
        }


# ============================================================================
# Network
# ============================================================================

def _update_network_speed() -> tuple[float, float]:
    """
    Calculate network speed in bytes/sec.
    """

    global _last_network_time
    global _last_network_bytes_sent
    global _last_network_bytes_recv

    global _network_download
    global _network_upload

    now = time.monotonic()

    try:
        counters = psutil.net_io_counters()

        if counters is None:
            return (
                _network_download,
                _network_upload,
            )

        sent = int(counters.bytes_sent)
        recv = int(counters.bytes_recv)

        # First sample.
        if _last_network_time <= 0:

            _last_network_time = now

            _last_network_bytes_sent = sent
            _last_network_bytes_recv = recv

            _network_download = 0.0
            _network_upload = 0.0

            return 0.0, 0.0

        elapsed = (
            now - _last_network_time
        )

        if elapsed <= 0:
            return (
                _network_download,
                _network_upload,
            )

        delta_sent = (
            sent
            - _last_network_bytes_sent
        )

        delta_recv = (
            recv
            - _last_network_bytes_recv
        )

        if delta_sent < 0:
            delta_sent = 0

        if delta_recv < 0:
            delta_recv = 0

        _network_upload = (
            delta_sent / elapsed
        )

        _network_download = (
            delta_recv / elapsed
        )

        _last_network_time = now

        _last_network_bytes_sent = sent
        _last_network_bytes_recv = recv

        return (
            _network_download,
            _network_upload,
        )

    except Exception as exc:
        print(
            f"[Monitoring] Network error: {exc}"
        )

        return (
            _network_download,
            _network_upload,
        )


def get_network_speed() -> dict[str, float]:
    """Return network speed in bytes/sec."""

    with _lock:

        download, upload = (
            _update_network_speed()
        )

    return {
        "download": max(
            0.0,
            float(download),
        ),
        "upload": max(
            0.0,
            float(upload),
        ),
    }


# ============================================================================
# GPU information
# ============================================================================

def _normalize_gpu_info(
    info: Any,
) -> dict[str, Any]:
    """
    Normalize GPU information returned by gpu_info.py.

    This function does NOT query the GPU itself.
    """

    if not isinstance(info, dict):
        raise TypeError(
            "get_gpu_info() returned non-dict"
        )

    result = dict(info)

    result["name"] = str(
        result.get(
            "name",
            "Unknown GPU",
        )
        or "Unknown GPU"
    )

    result["vendor"] = str(
        result.get(
            "vendor",
            "Unknown",
        )
        or "Unknown"
    )

    result["driver"] = str(
        result.get(
            "driver",
            "Unknown",
        )
        or "Unknown"
    )

    result["usage"] = _clamp_percent(
        result.get(
            "usage",
            0.0,
        )
    )

    result["usage_3d"] = _clamp_percent(
        result.get(
            "usage_3d",
            0.0,
        )
    )

    result["usage_compute"] = _clamp_percent(
        result.get(
            "usage_compute",
            0.0,
        )
    )

    result["usage_video_decode"] = (
        _clamp_percent(
            result.get(
                "usage_video_decode",
                0.0,
            )
        )
    )

    result["usage_video_encode"] = (
        _clamp_percent(
            result.get(
                "usage_video_encode",
                0.0,
            )
        )
    )

    result["usage_copy"] = _clamp_percent(
        result.get(
            "usage_copy",
            0.0,
        )
    )

    result["memory"] = _safe_int(
        result.get(
            "memory",
            0,
        )
    )

    result["memory_total"] = _safe_int(
        result.get(
            "memory_total",
            0,
        )
    )

    return result


def get_gpu_data() -> dict[str, Any]:
    """
    Return normalized GPU information.

    gpu_info.py remains the single GPU source of truth.
    """

    global _last_gpu_info

    try:

        raw_info = get_gpu_info()

        result = _normalize_gpu_info(
            raw_info
        )

        with _lock:
            _last_gpu_info = dict(result)

        return result

    except Exception as exc:

        print(
            f"[Monitoring] GPU error: {exc}"
        )

        with _lock:

            if _last_gpu_info is not None:
                return dict(
                    _last_gpu_info
                )

        return {
            "name": "Unknown GPU",
            "vendor": "Unknown",
            "driver": "Unknown",

            "usage": 0.0,
            "usage_3d": 0.0,
            "usage_compute": 0.0,
            "usage_video_decode": 0.0,
            "usage_video_encode": 0.0,
            "usage_copy": 0.0,

            "memory": 0,
            "memory_total": 0,
        }


def get_gpu_usage() -> float:
    """Return GPU usage percentage."""

    info = get_gpu_data()

    return _clamp_percent(
        info.get(
            "usage",
            0.0,
        )
    )


# ============================================================================
# GPU engine summary
# ============================================================================

def _normalize_gpu_engine_summary(
    summary: Any,
) -> dict[str, Any]:
    """
    Normalize GPU engine summary returned by gpu_info.py.

    IMPORTANT:
        No recursive calls are made here.
    """

    if not isinstance(summary, dict):
        return {
            "usage": 0.0,
            "engines": {},
            "adapters": {},
            "sample_count": 0,
            "total_sample_count": 0,
        }

    result = dict(summary)

    result["usage"] = _clamp_percent(
        result.get(
            "usage",
            0.0,
        )
    )

    raw_engines = result.get(
        "engines",
        {},
    )

    engines: dict[str, float] = {}

    if isinstance(
        raw_engines,
        dict,
    ):
        for name, value in raw_engines.items():

            try:
                engine_name = str(
                    name
                ).strip().lower()

                if not engine_name:
                    continue

                engines[engine_name] = (
                    _clamp_percent(value)
                )

            except Exception:
                continue

    result["engines"] = engines

    raw_adapters = result.get(
        "adapters",
        {},
    )

    adapters: dict[str, dict[str, Any]] = {}

    if isinstance(
        raw_adapters,
        dict,
    ):

        for adapter_key, adapter in (
            raw_adapters.items()
        ):

            if not isinstance(
                adapter,
                dict,
            ):
                continue

            adapter_result = dict(
                adapter
            )

            adapter_result["luid"] = str(
                adapter_result.get(
                    "luid",
                    adapter_key,
                )
                or adapter_key
            )

            adapter_result["usage"] = (
                _clamp_percent(
                    adapter_result.get(
                        "usage",
                        0.0,
                    )
                )
            )

            raw_adapter_engines = (
                adapter_result.get(
                    "engines",
                    {},
                )
            )

            adapter_engines: dict[
                str,
                float,
            ] = {}

            if isinstance(
                raw_adapter_engines,
                dict,
            ):

                for name, value in (
                    raw_adapter_engines.items()
                ):

                    engine_name = str(
                        name
                    ).strip().lower()

                    if not engine_name:
                        continue

                    adapter_engines[
                        engine_name
                    ] = _clamp_percent(
                        value
                    )

            adapter_result[
                "engines"
            ] = adapter_engines

            adapter_result[
                "sample_count"
            ] = max(
                0,
                _safe_int(
                    adapter_result.get(
                        "sample_count",
                        0,
                    )
                ),
            )

            adapter_result[
                "active_sample_count"
            ] = max(
                0,
                _safe_int(
                    adapter_result.get(
                        "active_sample_count",
                        0,
                    )
                ),
            )

            adapters[
                str(adapter_key)
            ] = adapter_result

    result["adapters"] = adapters

    result["sample_count"] = max(
        0,
        _safe_int(
            result.get(
                "sample_count",
                0,
            )
        ),
    )

    result["total_sample_count"] = max(
        0,
        _safe_int(
            result.get(
                "total_sample_count",
                0,
            )
        ),
    )

    return result


def get_gpu_engine_data(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Return GPU engine summary.

    gpu_info.py performs the actual Windows GPU Engine
    counter query.
    """

    global _last_gpu_engine_summary

    try:

        summary = get_gpu_engine_summary(
            force_refresh=force_refresh
        )

        result = (
            _normalize_gpu_engine_summary(
                summary
            )
        )

        with _lock:
            _last_gpu_engine_summary = dict(
                result
            )

        return result

    except Exception as exc:

        print(
            f"[Monitoring] GPU engine error: {exc}"
        )

        with _lock:

            if (
                _last_gpu_engine_summary
                is not None
            ):
                return dict(
                    _last_gpu_engine_summary
                )

        return {
            "usage": 0.0,
            "engines": {},
            "adapters": {},
            "sample_count": 0,
            "total_sample_count": 0,
        }


# ============================================================================
# GPU processes
# ============================================================================

def get_gpu_process_list(
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """
    Return processes currently using GPU.

    The actual GPU process detection is performed by gpu_info.py.

    A short hold period prevents the UI from flickering when Windows
    temporarily returns an empty GPU process sample.
    """

    global _last_gpu_process_time
    global _last_gpu_processes
    global _last_gpu_process_nonempty_time

    now = time.monotonic()

    with _lock:

        if (
            not force_refresh
            and (
                now
                - _last_gpu_process_time
                < GPU_PROCESS_CACHE_TTL
            )
        ):

            return [
                dict(item)
                for item
                in _last_gpu_processes
            ]

    try:

        processes = get_gpu_processes(
            force_refresh=True
        )

        if not isinstance(
            processes,
            list,
        ):
            processes = []

        cleaned: list[
            dict[str, Any]
        ] = []

        for item in processes:

            if not isinstance(
                item,
                dict,
            ):
                continue

            pid = _safe_int(
                item.get(
                    "pid",
                    0,
                )
            )

            if pid <= 0:
                continue

            name = str(
                item.get(
                    "name",
                    f"PID {pid}",
                )
                or f"PID {pid}"
            ).strip()

            usage = _clamp_percent(
                item.get(
                    "usage",
                    0.0,
                )
            )

            if usage <= 0:
                continue

            raw_engines = item.get(
                "engines",
                {},
            )

            engines: dict[
                str,
                float,
            ] = {}

            if isinstance(
                raw_engines,
                dict,
            ):

                for engine_name, value in (
                    raw_engines.items()
                ):

                    name_key = str(
                        engine_name
                    ).strip().lower()

                    if not name_key:
                        continue

                    engines[name_key] = (
                        _clamp_percent(value)
                    )

            cleaned.append(
                {
                    "pid": pid,
                    "name": name,
                    "usage": usage,
                    "engines": engines,
                }
            )

        cleaned.sort(
            key=lambda item: item[
                "usage"
            ],
            reverse=True,
        )

        cleaned = cleaned[:30]

        with _lock:

            _last_gpu_process_time = now

            if cleaned:

                _last_gpu_processes = [
                    dict(item)
                    for item in cleaned
                ]

                _last_gpu_process_nonempty_time = (
                    now
                )

                return [
                    dict(item)
                    for item in cleaned
                ]

            # Windows can temporarily return an empty
            # process list. Hold the previous list briefly.
            if (
                _last_gpu_processes
                and (
                    now
                    - _last_gpu_process_nonempty_time
                    < GPU_PROCESS_HOLD_TIME
                )
            ):

                return [
                    dict(item)
                    for item
                    in _last_gpu_processes
                ]

            _last_gpu_processes = []

            return []

    except Exception as exc:

        print(
            f"[Monitoring] GPU process error: {exc}"
        )

        with _lock:

            return [
                dict(item)
                for item
                in _last_gpu_processes
            ]


# ============================================================================
# Complete monitoring snapshot
# ============================================================================

def get_monitoring_data() -> dict[str, Any]:
    """
    Return complete monitoring snapshot.

    This is the main function used by the UI.
    """

    cpu = get_cpu_usage()

    ram = get_ram_usage()

    disk = get_disk_usage()

    network = get_network_speed()

    gpu = get_gpu_data()

    gpu_engine = get_gpu_engine_data()

    processes = get_gpu_process_list()

    return {

        # ------------------------------------------------------------------
        # CPU
        # ------------------------------------------------------------------

        "cpu": cpu,

        # ------------------------------------------------------------------
        # RAM
        # ------------------------------------------------------------------

        "ram": ram,

        # ------------------------------------------------------------------
        # Disk
        # ------------------------------------------------------------------

        "disk": disk,

        # ------------------------------------------------------------------
        # GPU
        # ------------------------------------------------------------------

        "gpu": _clamp_percent(
            gpu.get(
                "usage",
                0.0,
            )
        ),

        "gpu_name": gpu.get(
            "name",
            "Unknown GPU",
        ),

        "gpu_vendor": gpu.get(
            "vendor",
            "Unknown",
        ),

        "gpu_driver": gpu.get(
            "driver",
            "Unknown",
        ),

        "gpu_usage_3d": _clamp_percent(
            gpu.get(
                "usage_3d",
                0.0,
            )
        ),

        "gpu_usage_compute": _clamp_percent(
            gpu.get(
                "usage_compute",
                0.0,
            )
        ),

        "gpu_usage_video_decode": (
            _clamp_percent(
                gpu.get(
                    "usage_video_decode",
                    0.0,
                )
            )
        ),

        "gpu_usage_video_encode": (
            _clamp_percent(
                gpu.get(
                    "usage_video_encode",
                    0.0,
                )
            )
        ),

        "gpu_usage_copy": _clamp_percent(
            gpu.get(
                "usage_copy",
                0.0,
            )
        ),

        "gpu_memory": _safe_int(
            gpu.get(
                "memory",
                0,
            )
        ),

        "gpu_memory_total": _safe_int(
            gpu.get(
                "memory_total",
                0,
            )
        ),

        # ------------------------------------------------------------------
        # GPU Engine summary
        # ------------------------------------------------------------------

        "gpu_engine_summary": gpu_engine,

        "gpu_engine_sample_count": max(
            0,
            _safe_int(
                gpu_engine.get(
                    "sample_count",
                    0,
                )
            ),
        ),

        "gpu_engine_total_sample_count": max(
            0,
            _safe_int(
                gpu_engine.get(
                    "total_sample_count",
                    0,
                )
            ),
        ),

        "gpu_engine_adapters": dict(
            gpu_engine.get(
                "adapters",
                {},
            )
        ),

        # ------------------------------------------------------------------
        # Network
        # ------------------------------------------------------------------

        "download": network[
            "download"
        ],

        "upload": network[
            "upload"
        ],

        # ------------------------------------------------------------------
        # GPU processes
        # ------------------------------------------------------------------

        "gpu_processes": processes,

        "gpu_process_count": len(
            processes
        ),
    }


# ============================================================================
# Compatibility aliases
# ============================================================================

def get_monitoring() -> dict[str, Any]:
    """Compatibility alias."""

    return get_monitoring_data()


def get_system_stats() -> dict[str, Any]:
    """Compatibility alias."""

    return get_monitoring_data()


def get_stats() -> dict[str, Any]:
    """Compatibility alias."""

    return get_monitoring_data()


# ============================================================================
# SystemMonitor
# ============================================================================

class SystemMonitor:
    """
    Background monitoring helper.

    Example:

        monitor = SystemMonitor()
        monitor.start()

        data = monitor.latest()

        monitor.stop()
    """

    def __init__(
        self,
        interval: float = 1.0,
    ) -> None:

        try:
            interval_value = float(
                interval
            )

        except (
            TypeError,
            ValueError,
        ):
            interval_value = 1.0

        self.interval = max(
            0.1,
            interval_value,
        )

        self.running = False

        self._thread: (
            threading.Thread | None
        ) = None

        self._data: dict[
            str,
            Any,
        ] = {}

        self._data_lock = (
            threading.RLock()
        )

    def get_data(
        self,
    ) -> dict[str, Any]:

        data = get_monitoring_data()

        with self._data_lock:

            self._data = dict(
                data
            )

        return dict(data)

    def latest(
        self,
    ) -> dict[str, Any]:

        with self._data_lock:

            return dict(
                self._data
            )

    def start(self) -> None:

        if self.running:
            return

        self.running = True

        self._thread = (
            threading.Thread(
                target=self._worker,
                name=(
                    "PCControlCenter-"
                    "Monitor"
                ),
                daemon=True,
            )
        )

        self._thread.start()

    def stop(self) -> None:

        self.running = False

        thread = self._thread

        if (
            thread is not None
            and thread.is_alive()
            and thread
            is not threading.current_thread()
        ):

            thread.join(
                timeout=max(
                    0.5,
                    self.interval + 0.5,
                )
            )

        self._thread = None

    def _worker(self) -> None:

        while self.running:

            started = time.monotonic()

            try:

                self.get_data()

            except Exception as exc:

                print(
                    "[Monitoring Worker] "
                    f"ERROR: {exc}"
                )

            elapsed = (
                time.monotonic()
                - started
            )

            sleep_time = max(
                0.05,
                self.interval
                - elapsed,
            )

            time.sleep(
                sleep_time
            )


# ============================================================================
# Self test
# ============================================================================

def monitoring_self_test() -> dict[str, Any]:
    """
    Run compact monitoring diagnostic.
    """

    result: dict[str, Any] = {

        "ok": False,

        "cpu": 0.0,
        "ram": 0.0,
        "disk": 0.0,

        "gpu": 0.0,
        "gpu_usage_3d": 0.0,
        "gpu_usage_compute": 0.0,
        "gpu_usage_video_decode": 0.0,
        "gpu_usage_video_encode": 0.0,
        "gpu_usage_copy": 0.0,

        "download": 0.0,
        "upload": 0.0,

        "gpu_name": "Unknown GPU",

        "gpu_process_count": 0,

        "gpu_engine_sample_count": 0,
        "gpu_engine_total_sample_count": 0,
    }

    try:

        # Prime CPU counter.
        try:
            psutil.cpu_percent(
                interval=None
            )

        except Exception:
            pass

        time.sleep(0.1)

        data = get_monitoring_data()

        result.update(
            {
                "ok": True,

                "cpu": data.get(
                    "cpu",
                    0.0,
                ),

                "ram": data.get(
                    "ram",
                    0.0,
                ),

                "disk": data.get(
                    "disk",
                    0.0,
                ),

                "gpu": data.get(
                    "gpu",
                    0.0,
                ),

                "gpu_usage_3d": data.get(
                    "gpu_usage_3d",
                    0.0,
                ),

                "gpu_usage_compute": data.get(
                    "gpu_usage_compute",
                    0.0,
                ),

                "gpu_usage_video_decode": (
                    data.get(
                        "gpu_usage_video_decode",
                        0.0,
                    )
                ),

                "gpu_usage_video_encode": (
                    data.get(
                        "gpu_usage_video_encode",
                        0.0,
                    )
                ),

                "gpu_usage_copy": data.get(
                    "gpu_usage_copy",
                    0.0,
                ),

                "download": data.get(
                    "download",
                    0.0,
                ),

                "upload": data.get(
                    "upload",
                    0.0,
                ),

                "gpu_name": data.get(
                    "gpu_name",
                    "Unknown GPU",
                ),

                "gpu_process_count": data.get(
                    "gpu_process_count",
                    0,
                ),

                "gpu_engine_sample_count": (
                    data.get(
                        "gpu_engine_sample_count",
                        0,
                    )
                ),

                "gpu_engine_total_sample_count": (
                    data.get(
                        "gpu_engine_total_sample_count",
                        0,
                    )
                ),
            }
        )

    except Exception as exc:

        print(
            "[Monitoring Self Test] "
            f"ERROR: {exc}"
        )

    return result


# ============================================================================
# Cache control
# ============================================================================

def clear_monitoring_cache() -> None:
    """Clear all monitoring caches."""

    global _last_network_time
    global _last_network_bytes_sent
    global _last_network_bytes_recv

    global _network_download
    global _network_upload

    global _last_disk_time
    global _last_disk_percent

    global _last_gpu_info
    global _last_gpu_engine_summary

    global _last_gpu_process_time
    global _last_gpu_processes
    global _last_gpu_process_nonempty_time

    with _lock:

        # Network
        _last_network_time = 0.0

        _last_network_bytes_sent = 0
        _last_network_bytes_recv = 0

        _network_download = 0.0
        _network_upload = 0.0

        # Disk
        _last_disk_time = 0.0
        _last_disk_percent = 0.0

        # GPU
        _last_gpu_info = None
        _last_gpu_engine_summary = None

        # GPU processes
        _last_gpu_process_time = 0.0
        _last_gpu_processes = []
        _last_gpu_process_nonempty_time = 0.0


# ============================================================================
# Public API
# ============================================================================

__all__ = [

    "SystemMonitor",

    "get_cpu_usage",
    "get_ram_usage",
    "get_memory_info",

    "get_disk_usage",
    "get_disk_info",

    "get_network_speed",

    "get_gpu_data",
    "get_gpu_usage",
    "get_gpu_engine_data",
    "get_gpu_process_list",

    "get_monitoring_data",
    "get_monitoring",
    "get_system_stats",
    "get_stats",

    "monitoring_self_test",
    "clear_monitoring_cache",
]
