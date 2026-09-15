import platform
import psutil
import getpass
import os
def get_user_info():
    """
    Возвращает информацию о текущем пользователе Windows
    и компьютере.
    """

    username = (
        os.environ.get("USERNAME")
        or getpass.getuser()
        or "Unknown"
    ).strip()

    computer_name = (
        os.environ.get("COMPUTERNAME")
        or platform.node()
        or "Unknown"
    ).strip()

    hostname = (
        platform.node()
        or computer_name
        or "Unknown"
    ).strip()

    return {
        "username": username,
        "computer": computer_name,
        "hostname": hostname,
    }


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
    hostname = platform.node()

    return {
        "computer": hostname,
        "hostname": hostname,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def get_motherboard_info():
    """
    Получение информации о материнской плате
    через Windows WMI.
    """

    try:
        import subprocess

        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-CimInstance Win32_BaseBoard | "
                "Select-Object Manufacturer,Product,Version,SerialNumber | "
                "ConvertTo-Json -Compress"
            ),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
            )

        import json

        data = json.loads(
            result.stdout
        )

        return {
            "manufacturer": data.get(
                "Manufacturer",
                "Unknown",
            ),
            "product": data.get(
                "Product",
                "Unknown",
            ),
            "version": data.get(
                "Version",
                "Unknown",
            ),
            "serial": data.get(
                "SerialNumber",
                "Unknown",
            ),
        }

    except Exception as e:

        print(
            f"[SystemInfo] Motherboard error: {e}"
        )

        return {
            "manufacturer": "Unknown",
            "product": "Unknown",
            "version": "Unknown",
            "serial": "Unknown",
        }


def get_bios_info():
    """
    Получение информации о BIOS.
    """

    try:
        import subprocess
        import json

        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-CimInstance Win32_BIOS | "
                "Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate | "
                "ConvertTo-Json -Compress"
            ),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
            )

        data = json.loads(
            result.stdout
        )

        return {
            "manufacturer": data.get(
                "Manufacturer",
                "Unknown",
            ),
            "version": data.get(
                "SMBIOSBIOSVersion",
                "Unknown",
            ),
            "release_date": data.get(
                "ReleaseDate",
                "Unknown",
            ),
        }

    except Exception as e:

        print(
            f"[SystemInfo] BIOS error: {e}"
        )

        return {
            "manufacturer": "Unknown",
            "version": "Unknown",
            "release_date": "Unknown",
        }