import platform
import psutil
import subprocess


def get_cpu_name():
    """
    Получает нормальное название процессора через Windows.
    """

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor).Name"
            ],
            capture_output=True,
            text=True,
            timeout=3
        )

        name = result.stdout.strip()

        if name:
            return name

    except Exception:
        pass

    name = platform.processor()

    if name:
        return name

    return "Не определён"


def get_hardware_info():
    """
    Возвращает основную информацию
    об аппаратном обеспечении.
    """

    # ==================================================
    # CPU
    # ==================================================

    cpu_name = get_cpu_name()

    cpu_cores = psutil.cpu_count(
        logical=False
    )

    cpu_threads = psutil.cpu_count(
        logical=True
    )

    cpu_frequency = psutil.cpu_freq()

    if cpu_frequency:

        current_frequency = (
            cpu_frequency.current
        )

        max_frequency = (
            cpu_frequency.max
        )

    else:

        current_frequency = 0
        max_frequency = 0

    # ==================================================
    # RAM
    # ==================================================

    memory = psutil.virtual_memory()

    ram_total_gb = (
        memory.total / (1024 ** 3)
    )

    # ==================================================
    # SYSTEM
    # ==================================================

    system = platform.system()

    release = platform.release()

    version = platform.version()

    machine = platform.machine()

    computer_name = platform.node()

    return {

        "cpu": {

            "name": cpu_name,

            "cores": (
                cpu_cores or 0
            ),

            "threads": (
                cpu_threads or 0
            ),

            "frequency_current": (
                current_frequency
            ),

            "frequency_max": (
                max_frequency
            ),
        },

        "ram": {

            "total_gb": (
                ram_total_gb
            ),
        },

        "system": {

            "name": system,

            "release": release,

            "version": version,

            "architecture": machine,

            "computer": computer_name,
        },
    }