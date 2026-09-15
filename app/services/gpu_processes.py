import subprocess
import re


def get_gpu_processes():
    """
    Получает процессы, использующие GPU, через Windows GPU Engine counters.

    Возвращает:
    [
        {
            "pid": 4032,
            "instance": "...",
            "usage": 30.52
        },
        ...
    ]
    """

    powershell_script = r"""
    Get-Counter '\GPU Engine(*)\Utilization Percentage' |
        Select-Object -ExpandProperty CounterSamples |
        Where-Object { $_.CookedValue -gt 0 } |
        ForEach-Object {
            Write-Output "$($_.InstanceName)|$([math]::Round($_.CookedValue, 2))"
        }
    """

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                powershell_script
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15
        )

        if result.returncode != 0:
            print("GPU counter error:")
            print(result.stderr.strip())
            return []

        processes = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line or "|" not in line:
                continue

            instance, usage_text = line.rsplit("|", 1)

            match = re.search(r"pid_(\d+)_", instance)

            if not match:
                continue

            try:
                pid = int(match.group(1))
                usage = float(usage_text.replace(",", "."))
            except ValueError:
                continue

            processes.append({
                "pid": pid,
                "instance": instance,
                "usage": usage
            })

        return processes

    except subprocess.TimeoutExpired:
        print("GPU process error: PowerShell timed out")
        return []

    except Exception as e:
        print(f"GPU process error: {e}")
        return []