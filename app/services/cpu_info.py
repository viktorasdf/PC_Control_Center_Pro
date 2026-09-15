import psutil


def get_cpu_info():
    """
    Возвращает текущую информацию о CPU.

    Это лёгкий сервис.
    Никаких QThread здесь нет.

    Worker отвечает за периодичность вызовов.
    """

    try:
        usage = psutil.cpu_percent(
            interval=None
        )

        frequency = psutil.cpu_freq()

        if frequency:
            current_mhz = float(
                frequency.current or 0
            )

            min_mhz = float(
                frequency.min or 0
            )

            max_mhz = float(
                frequency.max or 0
            )
        else:
            current_mhz = 0.0
            min_mhz = 0.0
            max_mhz = 0.0

        logical = psutil.cpu_count(
            logical=True
        ) or 0

        physical = psutil.cpu_count(
            logical=False
        ) or 0

        load = psutil.getloadavg()

        return {
            "usage": round(
                max(
                    0.0,
                    min(
                        100.0,
                        float(usage),
                    ),
                ),
                1,
            ),

            "cores": int(
                physical
            ),

            "threads": int(
                logical
            ),

            "frequency_current": round(
                current_mhz,
                1,
            ),

            "frequency_min": round(
                min_mhz,
                1,
            ),

            "frequency_max": round(
                max_mhz,
                1,
            ),

            "load_1m": round(
                float(load[0]),
                2,
            ),

            "load_5m": round(
                float(load[1]),
                2,
            ),

            "load_15m": round(
                float(load[2]),
                2,
            ),
        }

    except Exception as exc:

        print(
            "[CPUInfo] ERROR:",
            repr(exc),
        )

        return {
            "usage": 0.0,
            "cores": 0,
            "threads": 0,
            "frequency_current": 0.0,
            "frequency_min": 0.0,
            "frequency_max": 0.0,
            "load_1m": 0.0,
            "load_5m": 0.0,
            "load_15m": 0.0,
            "error": str(exc),
        }