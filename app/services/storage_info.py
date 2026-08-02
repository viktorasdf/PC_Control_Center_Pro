import psutil


def get_storage_info():
    """
    Возвращает информацию обо всех доступных локальных дисках.
    """

    drives = []

    for partition in psutil.disk_partitions(all=False):

        # Пропускаем CD/DVD и другие неизвестные файловые системы
        if not partition.fstype:
            continue

        try:
            usage = psutil.disk_usage(
                partition.mountpoint
            )

            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)

            drives.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent": usage.percent,
            })

        except (PermissionError, OSError):
            continue

    return drives