from __future__ import annotations

import os
from pathlib import Path


def get_temp_directories() -> list[Path]:
    directories = []

    values = [
        os.environ.get("TEMP"),
        os.environ.get("TMP"),
    ]

    for value in values:
        if not value:
            continue

        path = Path(value)

        if path.exists() and path.is_dir():
            if path not in directories:
                directories.append(path)

    return directories


def scan_temp_files() -> dict:
    files = 0
    folders = 0
    total_bytes = 0

    for directory in get_temp_directories():

        try:

            for item in directory.rglob("*"):

                try:

                    if item.is_file():

                        files += 1
                        total_bytes += item.stat().st_size

                    elif item.is_dir():

                        folders += 1

                except (
                    OSError,
                    PermissionError,
                ):
                    continue

        except (
            OSError,
            PermissionError,
        ):
            continue

    return {
        "files": files,
        "folders": folders,
        "bytes": total_bytes,
        "megabytes": round(
            total_bytes / (1024 ** 2),
            1,
        ),
        "gigabytes": round(
            total_bytes / (1024 ** 3),
            2,
        ),
        "directories": [
            str(path)
            for path in get_temp_directories()
        ],
    }


def delete_temp_files(
    dry_run: bool = True,
) -> dict:

    deleted_files = 0
    deleted_folders = 0
    deleted_bytes = 0
    skipped = 0
    errors = 0

    for directory in get_temp_directories():

        try:

            items = list(
                directory.rglob("*")
            )

        except (
            OSError,
            PermissionError,
        ):

            errors += 1
            continue

        # ????? ??????? ???????.
        for item in items:

            if not item.is_file():
                continue

            if item.is_symlink():
                skipped += 1
                continue

            try:

                size = item.stat().st_size

                if dry_run:
                    deleted_files += 1
                    deleted_bytes += size
                    continue

                item.unlink()

                deleted_files += 1
                deleted_bytes += size

            except (
                OSError,
                PermissionError,
            ):

                skipped += 1

        # ????? ?????? ??????? ??????? ?????? ????????.
        if not dry_run:

            for item in reversed(items):

                if not item.is_dir():
                    continue

                if item.is_symlink():
                    skipped += 1
                    continue

                try:
                    item.rmdir()
                    deleted_folders += 1

                except (
                    OSError,
                    PermissionError,
                ):

                    pass

    return {
        "deleted_files": deleted_files,
        "deleted_folders": deleted_folders,
        "deleted_bytes": deleted_bytes,
        "deleted_megabytes": round(
            deleted_bytes / (1024 ** 2),
            1,
        ),
        "skipped": skipped,
        "errors": errors,
        "dry_run": dry_run,
    }
