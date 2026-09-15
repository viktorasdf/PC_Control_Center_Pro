
from __future__ import annotations

import os
import winreg
from pathlib import Path


REGISTRY_LOCATIONS = [
    (
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        "HKCU Run",
    ),
    (
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        "HKCU RunOnce",
    ),
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        "HKLM Run",
    ),
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        "HKLM RunOnce",
    ),
]


# ==============================================================
# BACKUP / DISABLED REGISTRY LOCATION
# ==============================================================

DISABLED_REGISTRY_PATH = (
    r"Software\PC_Control_Center_Pro\DisabledStartup"
)


# ==============================================================
# HELPERS
# ==============================================================

def _location_to_registry(location: str):
    for root, path, location_name in REGISTRY_LOCATIONS:
        if location_name == location:
            return root, path

    return None


def _read_registry_key(
    root,
    path,
    location_name,
):
    items = []

    try:
        with winreg.OpenKey(
            root,
            path,
            0,
            winreg.KEY_READ,
        ) as key:

            count = winreg.QueryInfoKey(key)[1]

            for index in range(count):

                try:

                    name, value, value_type = winreg.EnumValue(
                        key,
                        index,
                    )

                    items.append(
                        {
                            "name": str(name),
                            "command": str(value),
                            "location": location_name,
                            "type": "registry",
                            "value_type": int(value_type),
                            "enabled": True,
                        }
                    )

                except OSError:
                    continue

    except OSError:
        pass

    return items


def _get_startup_directories() -> list[tuple[str, Path]]:
    directories = []

    appdata = os.environ.get("APPDATA")
    program_data = os.environ.get("PROGRAMDATA")

    if appdata:
        directories.append(
            (
                "User Startup",
                Path(appdata)
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
                / "Startup",
            )
        )

    if program_data:
        directories.append(
            (
                "All Users Startup",
                Path(program_data)
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
                / "Startup",
            )
        )

    return directories




def _read_startup_folders():
    items = []

    for location_name, directory in _get_startup_directories():

        if not directory.exists():
            continue

        try:

            for item in directory.iterdir():

                try:

                    if not item.is_file():
                        continue

                    # --------------------------------------------------
                    # IGNORE WINDOWS SYSTEM FILES
                    # --------------------------------------------------

                    if item.name.lower() == "desktop.ini":
                        continue

                    # Disabled startup items are handled separately.
                    if item.name.lower().endswith(".disabled"):
                        continue

                    items.append(
                        {
                            "name": item.stem,
                            "command": str(item),
                            "location": location_name,
                            "type": "startup_folder",
                            "value_type": None,
                            "enabled": True,
                        }
                    )

                except OSError:
                    continue

        except OSError:
            continue

    return items


# ==============================================================
# DISABLED REGISTRY ITEMS
# ==============================================================

def _get_disabled_registry_items() -> list[dict]:
    items = []

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            DISABLED_REGISTRY_PATH,
            0,
            winreg.KEY_READ,
        ) as key:

            count = winreg.QueryInfoKey(key)[1]

            for index in range(count):

                try:

                    name, value, value_type = winreg.EnumValue(
                        key,
                        index,
                    )

                    # Format:
                    # LOCATION|ORIGINAL_NAME
                    text_name = str(name)

                    if "|" not in text_name:
                        continue

                    location, original_name = text_name.split(
                        "|",
                        1,
                    )

                    items.append(
                        {
                            "name": original_name,
                            "command": str(value),
                            "location": location,
                            "type": "registry_disabled",
                            "value_type": int(value_type),
                            "enabled": False,
                        }
                    )

                except OSError:
                    continue

    except OSError:
        pass

    return items


# ==============================================================
# PUBLIC SCAN
# ==============================================================

def get_startup_items() -> list[dict]:
    items = []

    for (
        root,
        path,
        location_name,
    ) in REGISTRY_LOCATIONS:

        items.extend(
            _read_registry_key(
                root,
                path,
                location_name,
            )
        )

    items.extend(
        _read_startup_folders()
    )

    items.sort(
        key=lambda item: (
            str(item.get("location", "")),
            str(item.get("name", "")).lower(),
        )
    )

    return items


def get_disabled_startup_items() -> list[dict]:
    return _get_disabled_registry_items()


def scan_startup() -> dict:
    items = get_startup_items()
    disabled_items = get_disabled_startup_items()

    return {
        "count": len(items),
        "items": items,
        "disabled_items": disabled_items,
        "registry_count": sum(
            1
            for item in items
            if item.get("type") == "registry"
        ),
        "folder_count": sum(
            1
            for item in items
            if item.get("type") == "startup_folder"
        ),
        "disabled_count": len(disabled_items),
    }


# ==============================================================
# REGISTRY DISABLE
# ==============================================================

def disable_registry_startup(
    location: str,
    name: str,
) -> tuple[bool, str]:

    registry_info = _location_to_registry(location)

    if registry_info is None:
        return False, "Неизвестный источник реестра."

    root, path = registry_info

    try:

        with winreg.OpenKey(
            root,
            path,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:

            value, value_type = winreg.QueryValueEx(
                key,
                name,
            )

            disabled_key = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                DISABLED_REGISTRY_PATH,
                0,
                winreg.KEY_WRITE,
            )

            backup_name = f"{location}|{name}"

            winreg.SetValueEx(
                disabled_key,
                backup_name,
                0,
                value_type,
                value,
            )

            winreg.CloseKey(
                disabled_key
            )

            winreg.DeleteValue(
                key,
                name,
            )

        return True, "Элемент автозагрузки отключён."

    except PermissionError:

        return (
            False,
            "Недостаточно прав. Для изменения этого элемента "
            "может потребоваться запуск PC Control Center Pro "
            "от имени администратора.",
        )

    except FileNotFoundError:

        return False, "Элемент автозагрузки не найден."

    except OSError as exc:

        return (
            False,
            f"Не удалось отключить элемент: {exc}",
        )


# ==============================================================
# REGISTRY ENABLE
# ==============================================================

def enable_registry_startup(
    location: str,
    name: str,
) -> tuple[bool, str]:

    registry_info = _location_to_registry(location)

    if registry_info is None:
        return False, "Неизвестный источник реестра."

    root, path = registry_info

    backup_name = f"{location}|{name}"

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            DISABLED_REGISTRY_PATH,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as disabled_key:

            value, value_type = winreg.QueryValueEx(
                disabled_key,
                backup_name,
            )

            with winreg.OpenKey(
                root,
                path,
                0,
                winreg.KEY_READ | winreg.KEY_WRITE,
            ) as key:

                winreg.SetValueEx(
                    key,
                    name,
                    0,
                    value_type,
                    value,
                )

            winreg.DeleteValue(
                disabled_key,
                backup_name,
            )

        return True, "Элемент автозагрузки включён."

    except FileNotFoundError:

        return False, "Сохранённая запись автозагрузки не найдена."

    except PermissionError:

        return (
            False,
            "Недостаточно прав. Для изменения этого элемента "
            "может потребоваться запуск PC Control Center Pro "
            "от имени администратора.",
        )

    except OSError as exc:

        return (
            False,
            f"Не удалось включить элемент: {exc}",
        )


# ==============================================================
# STARTUP FOLDER DISABLE
# ==============================================================

def disable_startup_folder(
    command: str,
) -> tuple[bool, str]:

    try:

        source = Path(command)

        if not source.exists():
            return False, "Файл автозагрузки не найден."

        if source.name.endswith(".disabled"):
            return False, "Элемент уже отключён."

        target = source.with_name(
            source.name + ".disabled"
        )

        if target.exists():
            return (
                False,
                "Резервное имя уже существует.",
            )

        source.rename(target)

        return True, "Элемент автозагрузки отключён."

    except PermissionError:

        return (
            False,
            "Недостаточно прав для изменения файла.",
        )

    except OSError as exc:

        return (
            False,
            f"Не удалось отключить файл: {exc}",
        )


# ==============================================================
# STARTUP FOLDER ENABLE
# ==============================================================

def enable_startup_folder(
    command: str,
) -> tuple[bool, str]:

    try:

        disabled = Path(command)

        if not disabled.exists():
            return False, "Отключённый файл не найден."

        if not disabled.name.endswith(".disabled"):
            return False, "Файл не является отключённым элементом."

        original = Path(
            str(disabled)[
                :-len(".disabled")
            ]
        )

        if original.exists():
            return (
                False,
                "Исходный файл уже существует.",
            )

        disabled.rename(original)

        return True, "Элемент автозагрузки включён."

    except PermissionError:

        return (
            False,
            "Недостаточно прав для изменения файла.",
        )

    except OSError as exc:

        return (
            False,
            f"Не удалось включить файл: {exc}",
        )


# ==============================================================
# GENERIC ENABLE / DISABLE
# ==============================================================

def disable_startup_item(
    item: dict,
) -> tuple[bool, str]:

    item_type = item.get("type")

    if item_type == "registry":

        return disable_registry_startup(
            str(item.get("location", "")),
            str(item.get("name", "")),
        )

    if item_type == "startup_folder":

        return disable_startup_folder(
            str(item.get("command", "")),
        )

    return False, "Этот тип элемента нельзя отключить."


def enable_startup_item(
    item: dict,
) -> tuple[bool, str]:

    item_type = item.get("type")

    if item_type == "registry_disabled":

        return enable_registry_startup(
            str(item.get("location", "")),
            str(item.get("name", "")),
        )

    if item_type == "startup_folder_disabled":

        return enable_startup_folder(
            str(item.get("command", "")),
        )

    return False, "Этот тип элемента нельзя включить."
