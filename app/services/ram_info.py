import psutil


def get_ram_info():
    """
    Возвращает информацию об оперативной памяти.
    """

    try:

        memory = psutil.virtual_memory()

        total = float(
            memory.total
        )

        used = float(
            memory.used
        )

        available = float(
            memory.available
        )

        free = float(
            memory.free
        )

        percent = float(
            memory.percent
        )

        return {
            "usage": round(
                max(
                    0.0,
                    min(
                        100.0,
                        percent,
                    ),
                ),
                1,
            ),

            "total": total,

            "used": used,

            "available": available,

            "free": free,

            "total_gb": round(
                total / (1024 ** 3),
                2,
            ),

            "used_gb": round(
                used / (1024 ** 3),
                2,
            ),

            "available_gb": round(
                available / (1024 ** 3),
                2,
            ),

            "free_gb": round(
                free / (1024 ** 3),
                2,
            ),
        }

    except Exception as exc:

        print(
            "[RAMInfo] ERROR:",
            repr(exc),
        )

        return {
            "usage": 0.0,
            "total": 0.0,
            "used": 0.0,
            "available": 0.0,
            "free": 0.0,
            "total_gb": 0.0,
            "used_gb": 0.0,
            "available_gb": 0.0,
            "free_gb": 0.0,
            "error": str(exc),
        }