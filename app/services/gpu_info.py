import json
import shutil
import subprocess


def run_command(command, timeout=5):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            return result.stdout.strip()

    except (subprocess.SubprocessError, OSError):
        pass

    return ""


def get_gpu_info():
    """
    Определение видеокарты в Windows.

    Приоритет:
    1. NVIDIA nvidia-smi
    2. Windows Win32_VideoController
    """

    gpu = {
        "name": "Не определена",
        "memory_total": 0,
        "memory_used": 0,
        "memory_percent": 0,
        "temperature": None,
        "usage": None,
        "vendor": "Unknown",
    }

    # ==================================================
    # NVIDIA
    # ==================================================

    nvidia_smi = shutil.which("nvidia-smi")

    if nvidia_smi:
        output = run_command([
            nvidia_smi,
            "--query-gpu=name,memory.total,memory.used,"
            "utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ], timeout=3)

        if output:
            try:
                parts = [
                    item.strip()
                    for item in output.splitlines()[0].split(",")
                ]

                if len(parts) >= 5:
                    memory_total = float(parts[1])
                    memory_used = float(parts[2])

                    gpu["name"] = parts[0]
                    gpu["memory_total"] = memory_total
                    gpu["memory_used"] = memory_used
                    gpu["usage"] = float(parts[3])
                    gpu["temperature"] = float(parts[4])
                    gpu["vendor"] = "NVIDIA"

                    if memory_total > 0:
                        gpu["memory_percent"] = (
                            memory_used / memory_total
                        ) * 100

                    return gpu

            except (ValueError, IndexError):
                pass

    # ==================================================
    # WINDOWS
    # ==================================================

    powershell_command = (
        "Get-CimInstance Win32_VideoController | "
        "Select-Object -First 1 Name,AdapterRAM,DriverVersion | "
        "ConvertTo-Json -Compress"
    )

    output = run_command([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        powershell_command,
    ])

    if output:
        try:
            data = json.loads(output)

            name = data.get("Name")
            adapter_ram = data.get("AdapterRAM")
            driver_version = data.get("DriverVersion")

            if name:
                gpu["name"] = name

            if adapter_ram:
                gpu["memory_total"] = (
                    int(adapter_ram) / (1024 ** 3)
                )

            gpu["driver"] = driver_version or "Unknown"

            name_lower = (name or "").lower()

            if "nvidia" in name_lower:
                gpu["vendor"] = "NVIDIA"

            elif (
                "amd" in name_lower
                or "radeon" in name_lower
            ):
                gpu["vendor"] = "AMD"

            elif "intel" in name_lower:
                gpu["vendor"] = "Intel"

            else:
                gpu["vendor"] = "Unknown"

        except (
            json.JSONDecodeError,
            ValueError,
            TypeError,
        ):
            pass

    return gpu