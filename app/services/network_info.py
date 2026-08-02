import psutil
import socket


def get_network_info():
    """
    Возвращает информацию о сетевых интерфейсах.
    """

    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    counters = psutil.net_io_counters(pernic=True)

    networks = []

    for name, addresses in interfaces.items():

        # Пропускаем виртуальные интерфейсы
        if name.lower().startswith(
            ("loopback", "lo", "vmware", "virtualbox")
        ):
            continue

        ipv4 = "Не определён"
        ipv6 = "Не определён"
        mac = "Не определён"

        for address in addresses:

            if address.family == socket.AF_INET:
                ipv4 = address.address

            elif address.family == socket.AF_INET6:
                ipv6 = address.address

            elif address.family == psutil.AF_LINK:
                mac = address.address

        interface_stats = stats.get(name)

        if interface_stats:
            speed_mbps = interface_stats.speed
            is_up = interface_stats.isup
        else:
            speed_mbps = 0
            is_up = False

        interface_counters = counters.get(name)

        if interface_counters:
            bytes_sent = interface_counters.bytes_sent
            bytes_recv = interface_counters.bytes_recv
        else:
            bytes_sent = 0
            bytes_recv = 0

        networks.append({
            "name": name,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "mac": mac,
            "speed_mbps": speed_mbps,
            "is_up": is_up,
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
        })

    return networks