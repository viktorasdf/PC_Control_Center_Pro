"""
PC Control Center Pro
app/services/gpu_info.py

Windows GPU information and monitoring service.

Compatible with:
    - Windows 10 / 11
    - Python 3.13
    - PowerShell 5.1+
    - AMD / NVIDIA / Intel GPUs

Important:
    This module intentionally does NOT use Get-Counter -SampleInterval.
    Some Windows PowerShell versions reject fractional SampleInterval
    values and that was the source of previous errors.

Public API:
    get_gpu_info()
    get_cached_gpu_info()
    get_gpu_usage()
    get_cached_gpu_usage()
    get_gpu_engine_summary()
    get_gpu_processes()
    gpu_self_test()
    monitoring_self_test()
    clear_gpu_cache()
    reset_gpu_cache()
    print_gpu_debug_info()
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
import threading
import time
from collections import defaultdict
from typing import Any


# ============================================================================
# Configuration
# ============================================================================

GPU_CACHE_TTL = 2.0
GPU_ENGINE_CACHE_TTL = 0.7
GPU_PROCESS_CACHE_TTL = 0.8

POWERSHELL_TIMEOUT = 8
POWERSHELL_COUNTER_TIMEOUT = 8

# Do not use fractional Get-Counter -SampleInterval.
# A single snapshot is enough for the Windows GPU Engine counter.
COUNTER_PATH = r"\GPU Engine(*)\Utilization Percentage"


# ============================================================================
# Internal state
# ============================================================================

_LOCK = threading.RLock()

_GPU_CACHE: dict[str, Any] | None = None
_GPU_CACHE_TIME = 0.0

_ENGINE_CACHE: dict[str, Any] | None = None
_ENGINE_CACHE_TIME = 0.0

_PROCESS_CACHE: list[dict[str, Any]] | None = None
_PROCESS_CACHE_TIME = 0.0

_LAST_GPU_USAGE = 0.0


# ============================================================================
# Generic helpers
# ============================================================================

def _now() -> float:
    return time.monotonic()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default

        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default

        return int(float(value))

    except (TypeError, ValueError):
        return default


def _clamp_percent(value: Any) -> float:
    value = _safe_float(value)

    if value < 0.0:
        return 0.0

    if value > 100.0:
        return 100.0

    return value


def _copy_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    # JSON round-trip gives us a safe detached copy for the nested
    # adapter/process dictionaries used by this module.
    try:
        return json.loads(json.dumps(value))
    except Exception:
        return dict(value)


def _copy_processes(
    value: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    try:
        return json.loads(json.dumps(value))
    except Exception:
        return [dict(item) for item in value if isinstance(item, dict)]


# ============================================================================
# PowerShell
# ============================================================================

def _run_powershell(
    script: str,
    timeout: int = POWERSHELL_TIMEOUT,
) -> str:
    """
    Execute a temporary PowerShell script.

    Errors are returned as an empty string so a temporary Windows counter
    failure never crashes the GUI.
    """

    script_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".ps1",
            encoding="utf-8",
            newline="\r\n",
            delete=False,
        ) as handle:
            handle.write(script)
            script_path = handle.name

        creationflags = 0

        if os.name == "nt":
            creationflags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=creationflags,
        )

        stdout = (result.stdout or "").strip()

        if result.returncode != 0:
            return ""

        return stdout

    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    ):
        return ""

    except Exception as exc:
        print(f"[GPU PowerShell] ERROR: {exc}")
        return ""

    finally:
        if script_path:
            try:
                os.remove(script_path)
            except OSError:
                pass


def _parse_json_output(output: str) -> Any:
    if not output:
        return None

    # PowerShell may occasionally print a warning before JSON.
    # Find the first JSON object/array and parse from there.
    output = output.strip()

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    starts = [
        output.find("{"),
        output.find("["),
    ]
    starts = [x for x in starts if x >= 0]

    if not starts:
        return None

    start = min(starts)

    try:
        return json.loads(output[start:])
    except json.JSONDecodeError:
        return None


# ============================================================================
# GPU static information
# ============================================================================

def _query_video_controllers() -> list[dict[str, Any]]:
    script = r"""
$ErrorActionPreference = 'SilentlyContinue'

try {
    $items = Get-CimInstance Win32_VideoController |
        Select-Object Name,
                      AdapterRAM,
                      DriverVersion,
                      VideoProcessor,
                      PNPDeviceID

    if ($items) {
        $items | ConvertTo-Json -Compress
    }
}
catch {}
"""

    output = _run_powershell(
        script,
        timeout=POWERSHELL_TIMEOUT,
    )

    data = _parse_json_output(output)

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        return []

    result: list[dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        name = str(item.get("Name") or "").strip()

        if not name:
            continue

        result.append(
            {
                "name": name,
                "adapter_ram": _safe_int(
                    item.get("AdapterRAM")
                ),
                "driver": str(
                    item.get("DriverVersion") or ""
                ).strip(),
                "video_processor": str(
                    item.get("VideoProcessor") or ""
                ).strip(),
                "pnp_device_id": str(
                    item.get("PNPDeviceID") or ""
                ).strip(),
            }
        )

    return result


def _detect_vendor(
    name: str,
    processor: str = "",
) -> str:
    value = f"{name} {processor}".lower()

    if "amd" in value or "radeon" in value:
        return "AMD"

    if (
        "nvidia" in value
        or "geforce" in value
        or "quadro" in value
    ):
        return "NVIDIA"

    if (
        "intel" in value
        or "iris" in value
        or "uhd graphics" in value
        or "hd graphics" in value
    ):
        return "Intel"

    return "Unknown"


def _select_gpu(
    controllers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not controllers:
        return None

    # Prefer a real hardware adapter over Microsoft virtual/basic display.
    for item in controllers:
        name = str(item.get("name") or "").lower()

        if (
            "microsoft basic display" not in name
            and "microsoft remote display" not in name
            and "remote display adapter" not in name
        ):
            return item

    return controllers[0]


def _make_static_gpu_info(
    controller: dict[str, Any],
) -> dict[str, Any]:
    name = str(
        controller.get("name")
        or "Unknown GPU"
    ).strip()

    processor = str(
        controller.get("video_processor")
        or ""
    ).strip()

    vendor = _detect_vendor(
        name,
        processor,
    )

    memory_total = _safe_int(
        controller.get("adapter_ram"),
        0,
    )

    # Windows Win32_VideoController AdapterRAM is bytes.
    # Keep bytes here because monitoring.py/dashboard.py currently expect it.
    if memory_total < 0:
        memory_total = 0

    return {
        "name": name or "Unknown GPU",
        "vendor": vendor,
        "driver": str(
            controller.get("driver")
            or "Unknown"
        ).strip()
        or "Unknown",
        "memory": memory_total,
        "memory_total": memory_total,
        "memory_used": 0,
        "memory_percent": 0.0,
        "temperature": None,
        "video_processor": processor,
        "pnp_device_id": str(
            controller.get("pnp_device_id")
            or ""
        ).strip(),
    }


# ============================================================================
# GPU engine instance parsing
# ============================================================================

def _extract_pid(instance: str) -> int | None:
    if not instance:
        return None

    match = re.search(
        r"(?:^|_)pid_(\d+)(?:_|$)",
        instance,
        re.IGNORECASE,
    )

    if match:
        return _safe_int(
            match.group(1),
            0,
        ) or None

    # Some systems expose a slightly different instance format.
    match = re.search(
        r"pid[-_](\d+)",
        instance,
        re.IGNORECASE,
    )

    if match:
        return _safe_int(
            match.group(1),
            0,
        ) or None

    return None


def _extract_luid(instance: str) -> str | None:
    if not instance:
        return None

    match = re.search(
        r"(luid_0x[0-9a-f]+_0x[0-9a-f]+)",
        instance,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    match = re.search(
        r"(luid_[^_]+_[^_]+)",
        instance,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def _engine_type_from_instance(
    instance: str,
) -> str:
    value = str(instance or "").lower()

    # Check the longer names first.
    if "engtype_videodecode" in value:
        return "video_decode"

    if "engtype_videoencode" in value:
        return "video_encode"

    if "engtype_compute" in value:
        return "compute"

    if "engtype_copy" in value:
        return "copy"

    if "engtype_3d" in value:
        return "3d"

    if "engtype_overlay" in value:
        return "overlay"

    if "engtype_security" in value:
        return "other"

    if "engtype_video" in value:
        return "other"

    return "other"


# ============================================================================
# GPU Engine counters
# ============================================================================

def _query_gpu_engine_samples_once() -> list[dict[str, Any]]:
    """
    Read one GPU Engine snapshot.

    Deliberately uses:

        Get-Counter '\\GPU Engine(*)\\Utilization Percentage'

    without -SampleInterval.

    This works with Windows PowerShell versions where fractional
    SampleInterval values such as 0.2 or 0.35 are rejected.
    """

    script = rf"""
$ErrorActionPreference = 'SilentlyContinue'

try {{
    $counter = Get-Counter '{COUNTER_PATH}' -ErrorAction SilentlyContinue

    if ($counter) {{
        $samples = @(
            $counter.CounterSamples |
            ForEach-Object {{
                [PSCustomObject]@{{
                    InstanceName = [string]$_.InstanceName
                    CookedValue  = [double]$_.CookedValue
                }}
            }}
        )

        if ($samples.Count -gt 0) {{
            $samples | ConvertTo-Json -Compress
        }}
    }}
}}
catch {{}}
"""

    output = _run_powershell(
        script,
        timeout=POWERSHELL_COUNTER_TIMEOUT,
    )

    data = _parse_json_output(output)

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        return []

    result: list[dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        instance = str(
            item.get("InstanceName") or ""
        ).strip()

        if not instance:
            continue

        value = _clamp_percent(
            item.get("CookedValue")
        )

        result.append(
            {
                "instance": instance,
                "value": value,
                "pid": _extract_pid(instance),
                "luid": _extract_luid(instance),
                "engine": _engine_type_from_instance(
                    instance
                ),
            }
        )

    return result


def _query_gpu_engine_samples() -> list[dict[str, Any]]:
    """
    Query counters with a small number of retries.

    A completely zero snapshot is accepted, but a missing snapshot
    is retried once. No recursive calls are made here.
    """

    samples = _query_gpu_engine_samples_once()

    if samples:
        return samples

    time.sleep(0.05)

    return _query_gpu_engine_samples_once()


# ============================================================================
# Engine aggregation
# ============================================================================

def _aggregate_engine_samples(
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate GPU engine counters.

    We use MAX per engine instead of SUM because Windows can expose
    multiple counter instances belonging to the same logical engine.
    Summing them can incorrectly produce >100% utilization.
    """

    engines: dict[str, float] = {}

    adapters: dict[str, dict[str, Any]] = {}

    process_engines: dict[
        int,
        dict[str, float],
    ] = defaultdict(dict)

    active_sample_count = 0

    for sample in samples:
        if not isinstance(sample, dict):
            continue

        value = _clamp_percent(
            sample.get("value")
        )

        if value > 0.0:
            active_sample_count += 1

        engine = str(
            sample.get("engine")
            or "other"
        ).strip().lower()

        if not engine:
            engine = "other"

        pid = sample.get("pid")
        luid = sample.get("luid")

        # Global engine max.
        engines[engine] = max(
            engines.get(engine, 0.0),
            value,
        )

        # Adapter.
        if luid:
            luid = str(luid)

            if luid not in adapters:
                adapters[luid] = {
                    "luid": luid,
                    "usage": 0.0,
                    "engines": {},
                    "sample_count": 0,
                    "active_sample_count": 0,
                }

            adapter = adapters[luid]

            adapter["sample_count"] += 1

            if value > 0.0:
                adapter["active_sample_count"] += 1

            adapter_engines = adapter["engines"]

            adapter_engines[engine] = max(
                adapter_engines.get(engine, 0.0),
                value,
            )

            adapter["usage"] = max(
                float(adapter["usage"]),
                value,
            )

        # Process.
        if pid is not None:
            pid_int = _safe_int(pid, 0)

            if pid_int > 0:
                process = process_engines[pid_int]

                process[engine] = max(
                    process.get(engine, 0.0),
                    value,
                )

    overall_usage = max(
        engines.values(),
        default=0.0,
    )

    normalized_engines: dict[str, float] = {}

    for engine, value in engines.items():
        value = _clamp_percent(value)

        if value > 0.0:
            normalized_engines[
                str(engine)
            ] = round(value, 2)

    normalized_adapters: dict[
        str,
        dict[str, Any],
    ] = {}

    for luid, adapter in adapters.items():
        adapter_engines: dict[str, float] = {}

        for engine, value in adapter.get(
            "engines",
            {},
        ).items():
            value = _clamp_percent(value)

            if value > 0.0:
                adapter_engines[
                    str(engine)
                ] = round(value, 2)

        normalized_adapters[luid] = {
            "luid": luid,
            "usage": round(
                _clamp_percent(
                    adapter.get(
                        "usage",
                        0.0,
                    )
                ),
                2,
            ),
            "engines": adapter_engines,
            "sample_count": _safe_int(
                adapter.get(
                    "sample_count",
                    0,
                )
            ),
            "active_sample_count": _safe_int(
                adapter.get(
                    "active_sample_count",
                    0,
                )
            ),
        }

    normalized_processes: dict[
        int,
        dict[str, float],
    ] = {}

    for pid, values in process_engines.items():
        normalized: dict[str, float] = {}

        for engine, value in values.items():
            value = _clamp_percent(value)

            if value > 0.0:
                normalized[
                    str(engine)
                ] = round(value, 4)

        normalized_processes[
            pid
        ] = normalized

    return {
        "usage": round(
            _clamp_percent(
                overall_usage
            ),
            2,
        ),
        "engines": normalized_engines,
        "adapters": normalized_adapters,
        "process_engines": normalized_processes,
        "sample_count": active_sample_count,
        "total_sample_count": len(samples),
    }


# ============================================================================
# Public GPU engine summary
# ============================================================================

def get_gpu_engine_summary(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Return current GPU engine summary.

    Keys:
        usage
        engines
        adapters
        sample_count
        total_sample_count
    """

    global _ENGINE_CACHE
    global _ENGINE_CACHE_TIME

    now = _now()

    with _LOCK:
        if (
            not force_refresh
            and _ENGINE_CACHE is not None
            and (
                now - _ENGINE_CACHE_TIME
                < GPU_ENGINE_CACHE_TTL
            )
        ):
            return _copy_dict(
                _ENGINE_CACHE
            )

    try:
        samples = _query_gpu_engine_samples()

        if not samples:
            result = {
                "usage": 0.0,
                "engines": {},
                "adapters": {},
                "sample_count": 0,
                "total_sample_count": 0,
            }

        else:
            result = _aggregate_engine_samples(
                samples
            )

            # Public summary intentionally does not expose the
            # internal process aggregation.
            result.pop(
                "process_engines",
                None,
            )

        with _LOCK:
            _ENGINE_CACHE = _copy_dict(
                result
            )
            _ENGINE_CACHE_TIME = now

        return _copy_dict(result)

    except Exception as exc:
        print(
            f"[GPU Engine] ERROR: {exc}"
        )

        with _LOCK:
            if _ENGINE_CACHE is not None:
                return _copy_dict(
                    _ENGINE_CACHE
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

def _get_process_name(pid: int) -> str:
    if pid <= 0:
        return f"PID {pid}"

    script = f"""
$ErrorActionPreference = 'SilentlyContinue'

try {{
    $p = Get-Process -Id {pid} -ErrorAction SilentlyContinue

    if ($p) {{
        [PSCustomObject]@{{
            Name = [string]$p.ProcessName
        }} | ConvertTo-Json -Compress
    }}
}}
catch {{}}
"""

    output = _run_powershell(
        script,
        timeout=3,
    )

    data = _parse_json_output(output)

    if isinstance(data, dict):
        name = str(
            data.get("Name") or ""
        ).strip()

        if name:
            if not name.lower().endswith(".exe"):
                name += ".exe"

            return name

    return f"PID {pid}"


def _build_gpu_processes_from_samples(
    samples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Aggregate process GPU usage in Python.

    This avoids the PowerShell parser/indexing problems that occurred
    in the previous implementation.
    """

    process_engines: dict[
        int,
        dict[str, float],
    ] = defaultdict(dict)

    for sample in samples:
        if not isinstance(sample, dict):
            continue

        pid = sample.get("pid")

        if pid is None:
            continue

        pid_int = _safe_int(pid, 0)

        if pid_int <= 0:
            continue

        value = _clamp_percent(
            sample.get("value")
        )

        if value <= 0.05:
            continue

        engine = str(
            sample.get("engine")
            or "other"
        ).strip().lower()

        current = process_engines[pid_int].get(
            engine,
            0.0,
        )

        # MAX, not SUM.
        process_engines[pid_int][engine] = max(
            current,
            value,
        )

    result: list[dict[str, Any]] = []

    for pid, engines in process_engines.items():
        usage = max(
            engines.values(),
            default=0.0,
        )

        if usage <= 0.05:
            continue

        # Ignore microscopic System COPY activity.
        if (
            pid == 4
            and engines.get("3d", 0.0) <= 0.0
            and engines.get("compute", 0.0) <= 0.0
            and engines.get("video_decode", 0.0) <= 0.0
            and engines.get("video_encode", 0.0) <= 0.0
            and engines.get("copy", 0.0) < 0.20
        ):
            continue

        name = _get_process_name(pid)

        normalized_engines = {}

        for engine, value in engines.items():
            value = _clamp_percent(value)

            if value > 0.0:
                normalized_engines[
                    engine
                ] = round(value, 4)

        result.append(
            {
                "pid": pid,
                "name": name,
                "usage": round(
                    _clamp_percent(usage),
                    4,
                ),
                "engines": normalized_engines,
            }
        )

    result.sort(
        key=lambda item: item["usage"],
        reverse=True,
    )

    return result[:30]


def get_gpu_processes(
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """
    Return processes currently using the GPU.

    Uses the same GPU Engine counters as get_gpu_engine_summary().
    No recursive calls.
    """

    global _PROCESS_CACHE
    global _PROCESS_CACHE_TIME

    now = _now()

    with _LOCK:
        if (
            not force_refresh
            and _PROCESS_CACHE is not None
            and (
                now - _PROCESS_CACHE_TIME
                < GPU_PROCESS_CACHE_TTL
            )
        ):
            return _copy_processes(
                _PROCESS_CACHE
            )

    try:
        samples = _query_gpu_engine_samples()

        if not samples:
            result: list[dict[str, Any]] = []

        else:
            result = _build_gpu_processes_from_samples(
                samples
            )

        with _LOCK:
            _PROCESS_CACHE = _copy_processes(
                result
            )
            _PROCESS_CACHE_TIME = now

        return _copy_processes(result)

    except Exception as exc:
        print(
            f"[GPU Processes] ERROR: {exc}"
        )

        with _LOCK:
            if _PROCESS_CACHE is not None:
                return _copy_processes(
                    _PROCESS_CACHE
                )

        return []


# ============================================================================
# GPU info
# ============================================================================

def _empty_gpu_info() -> dict[str, Any]:
    return {
        "name": "Unknown GPU",
        "vendor": "Unknown",
        "usage": 0.0,
        "usage_3d": 0.0,
        "usage_compute": 0.0,
        "usage_video_decode": 0.0,
        "usage_video_encode": 0.0,
        "usage_copy": 0.0,
        "driver": "Unknown",
        "memory": 0,
        "memory_total": 0,
        "memory_used": 0,
        "memory_percent": 0.0,
        "temperature": None,
        "video_processor": "",
        "pnp_device_id": "",
        "engine_summary": {
            "usage": 0.0,
            "engines": {},
            "adapters": {},
            "sample_count": 0,
            "total_sample_count": 0,
        },
        "engine_sample_count": 0,
        "engine_total_sample_count": 0,
        "engine_adapters": {},
    }


def _normalize_gpu_info(
    info: dict[str, Any],
) -> dict[str, Any]:
    result = _copy_dict(info)

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

    for key in (
        "usage",
        "usage_3d",
        "usage_compute",
        "usage_video_decode",
        "usage_video_encode",
        "usage_copy",
        "memory_percent",
    ):
        result[key] = _clamp_percent(
            result.get(key, 0.0)
        )

    for key in (
        "memory",
        "memory_total",
        "memory_used",
    ):
        result[key] = max(
            0,
            _safe_int(
                result.get(key, 0)
            ),
        )

    return result


def _query_gpu_info_uncached() -> dict[str, Any]:
    controllers = _query_video_controllers()

    controller = _select_gpu(
        controllers
    )

    if controller is None:
        return _empty_gpu_info()

    static_info = _make_static_gpu_info(
        controller
    )

    result = _empty_gpu_info()

    result.update(
        static_info
    )

    # Current engine snapshot.
    summary = get_gpu_engine_summary(
        force_refresh=True
    )

    result["engine_summary"] = _copy_dict(
        summary
    )

    result["engine_sample_count"] = _safe_int(
        summary.get(
            "sample_count",
            0,
        )
    )

    result["engine_total_sample_count"] = _safe_int(
        summary.get(
            "total_sample_count",
            0,
        )
    )

    result["engine_adapters"] = _copy_dict(
        summary.get(
            "adapters",
            {},
        )
    )

    engines = summary.get(
        "engines",
        {},
    )

    if not isinstance(engines, dict):
        engines = {}

    usage_3d = _clamp_percent(
        engines.get(
            "3d",
            0.0,
        )
    )

    usage_compute = _clamp_percent(
        engines.get(
            "compute",
            0.0,
        )
    )

    usage_decode = _clamp_percent(
        engines.get(
            "video_decode",
            0.0,
        )
    )

    usage_encode = _clamp_percent(
        engines.get(
            "video_encode",
            0.0,
        )
    )

    usage_copy = _clamp_percent(
        engines.get(
            "copy",
            0.0,
        )
    )

    summary_usage = _clamp_percent(
        summary.get(
            "usage",
            0.0,
        )
    )

    result["usage"] = summary_usage
    result["usage_3d"] = usage_3d
    result["usage_compute"] = usage_compute
    result["usage_video_decode"] = usage_decode
    result["usage_video_encode"] = usage_encode
    result["usage_copy"] = usage_copy

    # This old field is intentionally the same as total VRAM reported
    # by Win32_VideoController. There is no reliable universal VRAM-used
    # counter available for every AMD/Intel/NVIDIA configuration.
    result["memory_used"] = 0
    result["memory_percent"] = 0.0

    return _normalize_gpu_info(result)


def get_gpu_info(
    force_refresh: bool = False,
    include_usage: bool = True,
) -> dict[str, Any]:
    """
    Return complete GPU information.

    This is the main source of truth for monitoring.py.

    include_usage is accepted for compatibility with older AIWorker code.
    """

    del include_usage

    global _GPU_CACHE
    global _GPU_CACHE_TIME
    global _LAST_GPU_USAGE

    now = _now()

    with _LOCK:
        if (
            not force_refresh
            and _GPU_CACHE is not None
            and (
                now - _GPU_CACHE_TIME
                < GPU_CACHE_TTL
            )
        ):
            return _copy_dict(
                _GPU_CACHE
            )

    try:
        result = _query_gpu_info_uncached()

        with _LOCK:
            _GPU_CACHE = _copy_dict(
                result
            )
            _GPU_CACHE_TIME = now
            _LAST_GPU_USAGE = _clamp_percent(
                result.get(
                    "usage",
                    0.0,
                )
            )

        return _copy_dict(result)

    except Exception as exc:
        print(
            f"[GPU Info] ERROR: {exc}"
        )

        with _LOCK:
            if _GPU_CACHE is not None:
                return _copy_dict(
                    _GPU_CACHE
                )

        return _empty_gpu_info()


# ============================================================================
# Cached GPU info — dashboard compatibility
# ============================================================================

def get_cached_gpu_info(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Return GPU information from cache ONLY.

    IMPORTANT:
        This function NEVER starts PowerShell.
        This function NEVER calls get_gpu_info().
        This function NEVER refreshes GPU counters.

    GPUWorker is responsible for refreshing _GPU_CACHE
    through get_gpu_info().

    AIAnalyzer, Dashboard and TopBar can safely use this
    function without blocking the application.
    """

    del force_refresh

    with _LOCK:
        if _GPU_CACHE is not None:
            return _copy_dict(_GPU_CACHE)

    # Cache is not initialized yet.
    # Return an immediate empty structure.
    return _empty_gpu_info()


# ============================================================================
# GPU usage compatibility API
# ============================================================================

def get_gpu_usage() -> float:
    """Return current GPU usage percentage."""

    global _LAST_GPU_USAGE

    try:
        info = get_gpu_info()

        usage = _clamp_percent(
            info.get(
                "usage",
                0.0,
            )
        )

        with _LOCK:
            _LAST_GPU_USAGE = usage

        return usage

    except Exception:
        with _LOCK:
            return _LAST_GPU_USAGE


def get_cached_gpu_usage() -> float | None:
    """
    Return last known GPU usage without starting PowerShell.
    """

    with _LOCK:
        if _GPU_CACHE is not None:
            return _clamp_percent(
                _GPU_CACHE.get(
                    "usage",
                    _LAST_GPU_USAGE,
                )
            )

        if _LAST_GPU_USAGE > 0.0:
            return _LAST_GPU_USAGE

    return 0.0


# ============================================================================
# Self test
# ============================================================================

def gpu_self_test() -> dict[str, Any]:
    """
    Compact GPU diagnostic.
    """

    result: dict[str, Any] = {
        "ok": False,
        "gpu_detected": False,
        "name": "Unknown GPU",
        "vendor": "Unknown",
        "usage": 0.0,
        "usage_3d": 0.0,
        "usage_compute": 0.0,
        "usage_video_decode": 0.0,
        "usage_video_encode": 0.0,
        "usage_copy": 0.0,
        "driver": "Unknown",
        "memory": 0,
        "memory_total": 0,
        "engine_sample_count": 0,
        "engine_total_sample_count": 0,
        "process_count": 0,
    }

    try:
        info = get_gpu_info(
            force_refresh=True
        )

        processes = get_gpu_processes(
            force_refresh=True
        )

        result.update(
            {
                "ok": True,
                "gpu_detected": (
                    info.get("name")
                    not in (
                        None,
                        "",
                        "Unknown GPU",
                    )
                ),
                "name": info.get(
                    "name",
                    "Unknown GPU",
                ),
                "vendor": info.get(
                    "vendor",
                    "Unknown",
                ),
                "usage": _clamp_percent(
                    info.get(
                        "usage",
                        0.0,
                    )
                ),
                "usage_3d": _clamp_percent(
                    info.get(
                        "usage_3d",
                        0.0,
                    )
                ),
                "usage_compute": _clamp_percent(
                    info.get(
                        "usage_compute",
                        0.0,
                    )
                ),
                "usage_video_decode": _clamp_percent(
                    info.get(
                        "usage_video_decode",
                        0.0,
                    )
                ),
                "usage_video_encode": _clamp_percent(
                    info.get(
                        "usage_video_encode",
                        0.0,
                    )
                ),
                "usage_copy": _clamp_percent(
                    info.get(
                        "usage_copy",
                        0.0,
                    )
                ),
                "driver": info.get(
                    "driver",
                    "Unknown",
                ),
                "memory": _safe_int(
                    info.get(
                        "memory",
                        0,
                    )
                ),
                "memory_total": _safe_int(
                    info.get(
                        "memory_total",
                        0,
                    )
                ),
                "engine_sample_count": _safe_int(
                    info.get(
                        "engine_sample_count",
                        0,
                    )
                ),
                "engine_total_sample_count": _safe_int(
                    info.get(
                        "engine_total_sample_count",
                        0,
                    )
                ),
                "process_count": len(
                    processes
                ),
            }
        )

    except Exception as exc:
        print(
            f"[GPU Self Test] ERROR: {exc}"
        )

    return result


# Alias used by some older code.
def gpu_monitor_self_test() -> dict[str, Any]:
    return gpu_self_test()


# ============================================================================
# Cache control
# ============================================================================

def clear_gpu_cache() -> None:
    """Clear every GPU cache."""

    global _GPU_CACHE
    global _GPU_CACHE_TIME
    global _ENGINE_CACHE
    global _ENGINE_CACHE_TIME
    global _PROCESS_CACHE
    global _PROCESS_CACHE_TIME
    global _LAST_GPU_USAGE

    with _LOCK:
        _GPU_CACHE = None
        _GPU_CACHE_TIME = 0.0

        _ENGINE_CACHE = None
        _ENGINE_CACHE_TIME = 0.0

        _PROCESS_CACHE = None
        _PROCESS_CACHE_TIME = 0.0

        _LAST_GPU_USAGE = 0.0


def reset_gpu_cache() -> None:
    """Compatibility alias."""

    clear_gpu_cache()


# ============================================================================
# Debug helper
# ============================================================================

def print_gpu_debug_info() -> None:
    """
    Manual PowerShell diagnostic.

    Run:
        python -c "from app.services.gpu_info import print_gpu_debug_info; print_gpu_debug_info()"
    """

    print("=" * 72)
    print("PC CONTROL CENTER PRO - GPU DEBUG")
    print("=" * 72)

    print("\n[1] GPU INFO")
    print("-" * 72)

    try:
        info = get_gpu_info(
            force_refresh=True
        )

        for key, value in info.items():
            print(f"{key}: {value}")

    except Exception as exc:
        print(f"ERROR: {exc}")

    print("\n[2] ENGINE SUMMARY")
    print("-" * 72)

    try:
        summary = get_gpu_engine_summary(
            force_refresh=True
        )

        for key, value in summary.items():
            print(f"{key}: {value}")

    except Exception as exc:
        print(f"ERROR: {exc}")

    print("\n[3] GPU PROCESSES")
    print("-" * 72)

    try:
        processes = get_gpu_processes(
            force_refresh=True
        )

        print(
            f"Process count: {len(processes)}"
        )

        for process in processes:
            print(process)

    except Exception as exc:
        print(f"ERROR: {exc}")

    print("\n[4] SELF TEST")
    print("-" * 72)

    try:
        test = gpu_self_test()

        for key, value in test.items():
            print(f"{key}: {value}")

    except Exception as exc:
        print(f"ERROR: {exc}")

    print("=" * 72)
    print("GPU DEBUG FINISHED")
    print("=" * 72)


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "get_gpu_info",
    "get_cached_gpu_info",

    "get_gpu_usage",
    "get_cached_gpu_usage",

    "get_gpu_engine_summary",
    "get_gpu_processes",

    "gpu_self_test",
    "gpu_monitor_self_test",

    "clear_gpu_cache",
    "reset_gpu_cache",

    "print_gpu_debug_info",
]


# ============================================================================
# Module test
# ============================================================================

if __name__ == "__main__":
    print_gpu_debug_info()
