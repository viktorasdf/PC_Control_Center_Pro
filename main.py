
import sys
import ctypes
import os


def ensure_admin():
    """Перезапускает программу с правами администратора."""

    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("[System] Права администратора: OK")
            return True
    except Exception as exc:
        print("[System] Ошибка проверки прав:", exc)

    print("[System] Программа запущена без прав администратора.")
    print("[System] Запрашиваем права администратора...")

    script_path = os.path.abspath(__file__)
    python_exe = os.path.abspath(sys.executable)
    working_dir = os.path.dirname(script_path)

    print("[System] Python:", python_exe)
    print("[System] Script:", script_path)

    # Запускаем cmd.exe с правами администратора.
    # CMD остаётся открытым, поэтому мы увидим возможную ошибку Python.
    command = (
        f'cd /d "{working_dir}" && '
        f'"{python_exe}" "{script_path}"'
    )

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            "cmd.exe",
            f'/k {command}',
            working_dir,
            1,
        )

        print("[System] ShellExecute result:", result)

        if result <= 32:
            print("[System] Ошибка запуска.")
            return False

        print("[System] Повышенный CMD запущен.")
        return False

    except Exception as exc:
        print("[System] ShellExecute exception:", repr(exc))
        return False


def main():

    if not ensure_admin():
        sys.exit(0)

    print()
    print("=" * 60)
    print(" PC CONTROL CENTER PRO")
    print(" ADMIN MODE")
    print("=" * 60)
    print()

    from PySide6.QtWidgets import QApplication
    from app.core.main_window import MainWindow

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
