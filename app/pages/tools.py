
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from app.services.startup_service import (
    scan_startup,
    disable_startup_item,
    enable_startup_item,
)
from app.services.cleanup_service import (
    scan_temp_files,
    delete_temp_files,
)


# ==============================================================
# COLORS
# ==============================================================

BG = "#050b18"
CARD = "#091528"
BORDER = "#182c4a"
TEXT = "#f4f7ff"
MUTED = "#8ea3bd"
BLUE = "#168cff"
GREEN = "#22c55e"
PURPLE = "#a970ff"
ORANGE = "#ffb020"


# ==============================================================
# TOOL CARD
# ==============================================================

class ToolCard(QFrame):

    def __init__(
        self,
        icon,
        title,
        description,
        button_text,
        color=BLUE,
        parent=None,
    ):

        super().__init__(parent)

        self._accent_color = color

        self.setObjectName("ToolCard")

        light_theme = bool(
            getattr(self.window(), "_light_theme", False)
        )

        card_bg = "#ffffff" if light_theme else CARD
        card_border = "#d6e0ea" if light_theme else BORDER

        self.setStyleSheet(
            f"""
            QFrame#ToolCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}

            QLabel {{
                background: transparent;
                border: none;
            }}

            QPushButton {{
                background: {color};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: #ffffff;
                color: {color};
            }}

            QPushButton:pressed {{
                background: {BORDER};
            }}
            """
        )

        lay = QVBoxLayout(self)

        lay.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        lay.setSpacing(8)

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        header = QHBoxLayout()

        icon_label = QLabel(icon)

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 27px;
                background: transparent;
                border: none;
            }}
            """
        )

        header.addWidget(icon_label)

        self.title_label = QLabel(title)

        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 16px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            """
        )

        header.addWidget(self.title_label)

        header.addStretch()

        lay.addLayout(header)

        # ------------------------------------------------------
        # DESCRIPTION
        # ------------------------------------------------------

        self.description_label = QLabel(description)

        self.description_label.setWordWrap(True)

        self.description_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            """
        )

        lay.addWidget(self.description_label)

        lay.addStretch()

        # ------------------------------------------------------
        # BUTTON
        # ------------------------------------------------------

        self.button = QPushButton(button_text)

        self.button.setCursor(
            Qt.PointingHandCursor
        )

        self.button.setMinimumHeight(36)

        lay.addWidget(self.button)
    
        self.title_label.setText(title)
        self.description_label.setText(description)
        self.button.setText(button_text)

    def set_theme(self, light):
        light = bool(light)

        card_bg = "#ffffff" if light else CARD
        card_border = "#d6e0ea" if light else BORDER
        text_color = "#172033" if light else TEXT
        muted_color = "#64748b" if light else MUTED

        self.setStyleSheet(
            f"""
            QFrame#ToolCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 14px;
            }}

            QLabel {{
                background: transparent;
                border: none;
            }}

            QPushButton {{
                background: {self._accent_color};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: #ffffff;
                color: {self._accent_color};
            }}

            QPushButton:pressed {{
                background: {card_border};
            }}
            """
        )

        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {text_color};
                font-size: 16px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            """
        )

        self.description_label.setStyleSheet(
            f"""
            QLabel {{
                color: {muted_color};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            """
        )

    def set_content(self, title, description, button_text):
        self.title_label.setText(title)
        self.description_label.setText(description)
        self.button.setText(button_text)
# ==============================================================
# CLEANUP DIALOG
# ==============================================================

class CleanupDialog(QDialog):

    TRANSLATIONS = {
        "ru": {
            "title": "🧹  Очистка системы",
            "subtitle": "Поиск временных файлов и безопасная очистка системы",
            "not_scanned": "Сканирование ещё не выполнялось",
            "files": "Файлы",
            "folders": "Папки",
            "size": "Объём",
            "sources": "Источники",
            "not_found": "не найдены",
            "scan": "🔍  Сканировать",
            "clean": "🧹  Очистить",
            "scanning": "🔍 Сканирование...",
            "scan_done": "✅ Сканирование завершено",
            "error": "Ошибка",
            "scan_error": "Не удалось выполнить сканирование:",
            "cleanup": "Очистка системы",
            "first_scan": "Сначала выполните сканирование.",
            "nothing_to_delete": "Временные файлы для удаления не найдены.",
            "confirm": "Подтверждение очистки",
            "confirm_text": "Будут удалены доступные временные файлы.",
            "continue": "Продолжить?",
            "cleaning": "🧹 Выполняется очистка...",
            "clean_done": "Очистка завершена.",
            "rescan": "🔄 Очистка завершена. Выполняется повторное сканирование...",
            "deleted_files": "Удалено файлов",
            "deleted_folders": "Удалено папок",
            "freed": "Освобождено",
            "skipped": "Пропущено",
            "errors": "Ошибок",
            "unavailable_files": "Занятые или недоступные файлы будут пропущены.",
            "close": "Закрыть",
        },
        "uk": {
            "title": "🧹  Очищення системи",
            "subtitle": "Пошук тимчасових файлів і безпечне очищення системи",
            "not_scanned": "Сканування ще не виконувалося",
            "files": "Файли",
            "folders": "Папки",
            "size": "Обсяг",
            "sources": "Джерела",
            "not_found": "не знайдено",
            "scan": "🔍  Сканувати",
            "clean": "🧹  Очистити",
            "scanning": "🔍 Сканування...",
            "scan_done": "✅ Сканування завершено",
            "error": "Помилка",
            "scan_error": "Не вдалося виконати сканування:",
            "cleanup": "Очищення системи",
            "first_scan": "Спочатку виконайте сканування.",
            "nothing_to_delete": "Тимчасових файлів для видалення не знайдено.",
            "confirm": "Підтвердження очищення",
            "confirm_text": "Буде видалено доступні тимчасові файли.",
            "continue": "Продовжити?",
            "cleaning": "🧹 Виконується очищення...",
            "clean_done": "Очищення завершено.",
            "rescan": "🔄 Очищення завершено. Виконується повторне сканування...",
            "deleted_files": "Видалено файлів",
            "deleted_folders": "Видалено папок",
            "freed": "Звільнено",
            "skipped": "Пропущено",
            "errors": "Помилок",
            "unavailable_files": "Зайняті або недоступні файли буде пропущено.",
            "close": "Закрити",
        },
        "en": {
            "title": "🧹  System Cleanup",
            "subtitle": "Find temporary files and safely clean the system",
            "not_scanned": "Scan has not been run yet",
            "files": "Files",
            "folders": "Folders",
            "size": "Size",
            "sources": "Sources",
            "not_found": "not found",
            "scan": "🔍  Scan",
            "clean": "🧹  Clean",
            "scanning": "🔍 Scanning...",
            "scan_done": "✅ Scan completed",
            "error": "Error",
            "scan_error": "Failed to perform the scan:",
            "cleanup": "System Cleanup",
            "first_scan": "Run a scan first.",
            "nothing_to_delete": "No temporary files were found to delete.",
            "confirm": "Confirm Cleanup",
            "confirm_text": "Available temporary files will be deleted.",
            "continue": "Continue?",
            "cleaning": "🧹 Cleaning...",
            "clean_done": "Cleanup completed.",
            "rescan": "🔄 Cleanup completed. Running a new scan...",
            "deleted_files": "Files deleted",
            "deleted_folders": "Folders deleted",
            "freed": "Freed",
            "skipped": "Skipped",
            "errors": "Errors",
            "unavailable_files": "Busy or unavailable files will be skipped.",
            "close": "Close",
        },
        "de": {
            "title": "🧹  Systembereinigung",
            "subtitle": "Temporäre Dateien suchen und das System sicher bereinigen",
            "not_scanned": "Scan wurde noch nicht ausgeführt",
            "files": "Dateien",
            "folders": "Ordner",
            "size": "Größe",
            "sources": "Quellen",
            "not_found": "nicht gefunden",
            "scan": "🔍  Scannen",
            "clean": "🧹  Bereinigen",
            "scanning": "🔍 Scan läuft...",
            "scan_done": "✅ Scan abgeschlossen",
            "error": "Fehler",
            "scan_error": "Scan konnte nicht ausgeführt werden:",
            "cleanup": "Systembereinigung",
            "first_scan": "Führen Sie zuerst einen Scan durch.",
            "nothing_to_delete": "Keine temporären Dateien zum Löschen gefunden.",
            "confirm": "Bereinigung bestätigen",
            "confirm_text": "Verfügbare temporäre Dateien werden gelöscht.",
            "continue": "Fortfahren?",
            "cleaning": "🧹 Bereinigung läuft...",
            "clean_done": "Bereinigung abgeschlossen.",
            "rescan": "🔄 Bereinigung abgeschlossen. Neuer Scan wird ausgeführt...",
            "deleted_files": "Gelöschte Dateien",
            "deleted_folders": "Gelöschte Ordner",
            "freed": "Freigegeben",
            "skipped": "Übersprungen",
            "errors": "Fehler",
            "unavailable_files": "Belegte oder nicht verfügbare Dateien werden übersprungen.",
            "close": "Schließen",
        },
        "it": {
            "title": "🧹  Pulizia del sistema",
            "subtitle": "Cerca i file temporanei e pulisci il sistema in sicurezza",
            "not_scanned": "La scansione non è ancora stata eseguita",
            "files": "File",
            "folders": "Cartelle",
            "size": "Dimensione",
            "sources": "Origini",
            "not_found": "non trovate",
            "scan": "🔍  Scansiona",
            "clean": "🧹  Pulisci",
            "scanning": "🔍 Scansione...",
            "scan_done": "✅ Scansione completata",
            "error": "Errore",
            "scan_error": "Impossibile eseguire la scansione:",
            "cleanup": "Pulizia del sistema",
            "first_scan": "Esegui prima una scansione.",
            "nothing_to_delete": "Nessun file temporaneo da eliminare trovato.",
            "confirm": "Conferma pulizia",
            "confirm_text": "I file temporanei disponibili verranno eliminati.",
            "continue": "Continuare?",
            "cleaning": "🧹 Pulizia in corso...",
            "clean_done": "Pulizia completata.",
            "rescan": "🔄 Pulizia completata. Nuova scansione in corso...",
            "deleted_files": "File eliminati",
            "deleted_folders": "Cartelle eliminate",
            "freed": "Liberato",
            "skipped": "Saltati",
            "errors": "Errori",
            "unavailable_files": "I file occupati o non disponibili verranno ignorati.",
            "close": "Chiudi",
        },
        "es": {
            "title": "🧹  Limpieza del sistema",
            "subtitle": "Buscar archivos temporales y limpiar el sistema de forma segura",
            "not_scanned": "El análisis aún no se ha ejecutado",
            "files": "Archivos",
            "folders": "Carpetas",
            "size": "Tamaño",
            "sources": "Fuentes",
            "not_found": "no encontradas",
            "scan": "🔍  Escanear",
            "clean": "🧹  Limpiar",
            "scanning": "🔍 Analizando...",
            "scan_done": "✅ Análisis completado",
            "error": "Error",
            "scan_error": "No se pudo realizar el análisis:",
            "cleanup": "Limpieza del sistema",
            "first_scan": "Realiza primero un análisis.",
            "nothing_to_delete": "No se encontraron archivos temporales para eliminar.",
            "confirm": "Confirmar limpieza",
            "confirm_text": "Se eliminarán los archivos temporales disponibles.",
            "continue": "¿Continuar?",
            "cleaning": "🧹 Limpiando...",
            "clean_done": "Limpieza completada.",
            "rescan": "🔄 Limpieza completada. Ejecutando un nuevo análisis...",
            "deleted_files": "Archivos eliminados",
            "deleted_folders": "Carpetas eliminadas",
            "freed": "Liberado",
            "skipped": "Omitidos",
            "errors": "Errores",
            "unavailable_files": "Los archivos ocupados o no disponibles se omitirán.",
            "close": "Cerrar",
        },
        "fr": {
            "title": "🧹  Nettoyage du système",
            "subtitle": "Rechercher les fichiers temporaires et nettoyer le système en toute sécurité",
            "not_scanned": "L'analyse n'a pas encore été effectuée",
            "files": "Fichiers",
            "folders": "Dossiers",
            "size": "Taille",
            "sources": "Sources",
            "not_found": "introuvables",
            "scan": "🔍  Analyser",
            "clean": "🧹  Nettoyer",
            "scanning": "🔍 Analyse...",
            "scan_done": "✅ Analyse terminée",
            "error": "Erreur",
            "scan_error": "Impossible d'effectuer l'analyse :",
            "cleanup": "Nettoyage du système",
            "first_scan": "Effectuez d'abord une analyse.",
            "nothing_to_delete": "Aucun fichier temporaire à supprimer n'a été trouvé.",
            "confirm": "Confirmer le nettoyage",
            "confirm_text": "Les fichiers temporaires disponibles seront supprimés.",
            "continue": "Continuer ?",
            "cleaning": "🧹 Nettoyage en cours...",
            "clean_done": "Nettoyage terminé.",
            "rescan": "🔄 Nettoyage terminé. Nouvelle analyse en cours...",
            "deleted_files": "Fichiers supprimés",
            "deleted_folders": "Dossiers supprimés",
            "freed": "Libéré",
            "skipped": "Ignorés",
            "errors": "Erreurs",
            "unavailable_files": "Les fichiers occupés ou indisponibles seront ignorés.",
            "close": "Fermer",
        },
    }

    def __init__(self, parent=None):
        self.ui_language = getattr(parent, "ui_language", "ru")

        super().__init__(parent)

        self.setWindowTitle(
            self._tr("title")
        )

        self.setMinimumWidth(
            620
        )

        self.last_scan = None

        self._build_ui()

        self.scan_button.clicked.connect(
            self._scan
        )

        self.clean_button.clicked.connect(
            self._clean
        )

    def _tr(self, key):
        language = getattr(self, "ui_language", "ru")
        table = self.TRANSLATIONS.get(
            language,
            self.TRANSLATIONS["ru"],
        )
        return table.get(
            key,
            self.TRANSLATIONS["ru"].get(
                key,
                key,
            ),
        )

    def set_language(self, language):
        self.ui_language = language or "ru"

        self.setWindowTitle(
            self._tr("title")
        )

        self._build_ui()
    def set_theme(self, light):
        light = bool(light)

        for card in (
            self.cleanup_card,
            self.startup_card,
            self.security_card,
            self.system_card,
        ):
            card.set_theme(light)
    def _build_ui(self):

        layout = QVBoxLayout(
            self
        )

        title = QLabel(
            self._tr("title")
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {TEXT};
                padding: 8px 0;
            }}
            """
        )

        layout.addWidget(
            title
        )

        subtitle = QLabel(
            self._tr("subtitle")
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 13px;
                padding-bottom: 10px;
            }}
            """
        )

        layout.addWidget(
            subtitle
        )

        self.status_label = QLabel(
            self._tr("not_scanned")
        )

        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 14px;
                font-weight: 600;
                padding: 8px 0;
            }}
            """
        )

        layout.addWidget(
            self.status_label
        )

        stats = QHBoxLayout()

        self.files_label = QLabel(
            f"{self._tr('files')}: —"
        )

        self.folders_label = QLabel(
            f"{self._tr('folders')}: —"
        )

        self.size_label = QLabel(
            f"{self._tr('size')}: —"
        )

        self.directories_label = QLabel(
            f"{self._tr('sources')}: —"
        )

        for label in (
            self.files_label,
            self.folders_label,
            self.size_label,
        ):

            label.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT};
                    font-size: 13px;
                    padding: 8px;
                    background: {CARD};
                    border-radius: 8px;
                }}
                """
            )

            stats.addWidget(
                label
            )

        layout.addLayout(
            stats
        )

        self.directories_label.setWordWrap(
            True
        )

        self.directories_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 12px;
                padding: 10px;
                background: {CARD};
                border-radius: 8px;
            }}
            """
        )

        layout.addWidget(
            self.directories_label
        )

        buttons = QHBoxLayout()

        self.scan_button = QPushButton(
            self._tr("scan")
        )

        self.scan_button.setMinimumHeight(
            42
        )

        self.clean_button = QPushButton(
            self._tr("clean")
        )

        self.clean_button.setMinimumHeight(
            42
        )

        buttons.addWidget(
            self.scan_button
        )

        buttons.addWidget(
            self.clean_button
        )

        layout.addLayout(
            buttons
        )

        close_button = QPushButton(
            self._tr("close")
        )

        close_button.clicked.connect(
            self.reject
        )

        layout.addWidget(
            close_button
        )

    def _scan(self):

        print(
            "[Cleanup] Scan started"
        )

        self.scan_button.setEnabled(
            False
        )

        self.clean_button.setEnabled(
            False
        )

        self.status_label.setText(
            self._tr("scanning")
        )

        try:
            result = scan_temp_files()

        except Exception as exc:

            print(
                f"[Cleanup] Scan error: {exc}"
            )

            QMessageBox.critical(
                self,
                self._tr("error"),
                (
                    f"{self._tr('scan_error')}\n\n"
                    f"{exc}"
                ),
            )

            self.scan_button.setEnabled(
                True
            )

            return

        files = int(
            result.get(
                "files",
                0,
            )
        )

        folders = int(
            result.get(
                "folders",
                0,
            )
        )

        megabytes = float(
            result.get(
                "megabytes",
                0,
            )
        )

        gigabytes = float(
            result.get(
                "gigabytes",
                0,
            )
        )

        directories = result.get(
            "directories",
            [],
        )

        self.last_scan = result

        self.files_label.setText(
            f"{self._tr('files')}: {files}"
        )

        self.folders_label.setText(
            f"{self._tr('folders')}: {folders}"
        )

        self.size_label.setText(
            f"{self._tr('size')}: {megabytes:.1f} MB ({gigabytes:.2f} GB)"
        )

        if directories:

            self.directories_label.setText(
                f"{self._tr('sources')}:\n"
                + "\n".join(
                    str(path)
                    for path in directories
                )
            )

        else:

            self.directories_label.setText(
                f"{self._tr('sources')}: {self._tr('not_found')}"
            )

        self.status_label.setText(
            self._tr("scan_done")
        )

        self.scan_button.setEnabled(
            True
        )

        self.clean_button.setEnabled(
            files > 0
        )

        print(
            "[Cleanup] Scan finished:"
            f" files={files}"
            f" folders={folders}"
            f" MB={megabytes}"
        )

    def _clean(self):

        if not self.last_scan:

            QMessageBox.warning(
                self,
                self._tr("cleanup"),
                self._tr("first_scan"),
            )

            return

        files = int(
            self.last_scan.get(
                "files",
                0,
            )
        )

        megabytes = float(
            self.last_scan.get(
                "megabytes",
                0,
            )
        )

        if files <= 0:

            QMessageBox.information(
                self,
                self._tr("cleanup"),
                self._tr("nothing_to_delete"),
            )

            return

        answer = QMessageBox.question(
            self,
            self._tr("confirm"),
            (
                f"{self._tr('confirm_text')}\n\n"
                f"{self._tr('files')}: {files}\n"
                f"{self._tr('size')}: {megabytes:.1f} MB\n\n"
                f"{self._tr('unavailable_files')}\n\n"
                f"{self._tr('continue')}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        print(
            "[Cleanup] Deletion started"
        )

        self.scan_button.setEnabled(
            False
        )

        self.clean_button.setEnabled(
            False
        )

        self.status_label.setText(
            self._tr("cleaning")
        )

        try:

            result = delete_temp_files(
                dry_run=False
            )

        except Exception as exc:

            print(
                f"[Cleanup] Delete error: {exc}"
            )

            QMessageBox.critical(
                self,
                self._tr("error"),
                (
                    f"{self._tr('cleanup')}\n\n"
                    f"{exc}"
                ),
            )

            self.scan_button.setEnabled(
                True
            )

            return

        deleted_files = int(
            result.get(
                "deleted_files",
                0,
            )
        )

        deleted_folders = int(
            result.get(
                "deleted_folders",
                0,
            )
        )

        deleted_mb = float(
            result.get(
                "deleted_megabytes",
                0,
            )
        )

        skipped = int(
            result.get(
                "skipped",
                0,
            )
        )

        errors = int(
            result.get(
                "errors",
                0,
            )
        )

        print(
            "[Cleanup] Deletion finished:"
            f" files={deleted_files}"
            f" folders={deleted_folders}"
            f" MB={deleted_mb}"
            f" skipped={skipped}"
            f" errors={errors}"
        )

        QMessageBox.information(
            self,
            self._tr("cleanup"),
            (
                f"{self._tr('clean_done')}\n\n"
                f"{self._tr('deleted_files')}: {deleted_files}\n"
                f"{self._tr('deleted_folders')}: {deleted_folders}\n"
                f"{self._tr('freed')}: {deleted_mb:.1f} MB\n"
                f"{self._tr('skipped')}: {skipped}\n"
                f"{self._tr('errors')}: {errors}"
            ),
        )

        self.last_scan = None

        self.status_label.setText(
            self._tr("rescan")
        )

        self.scan_button.setEnabled(
            True
        )

        self._scan()


# STARTUP DIALOG
# ==============================================================

class StartupDialog(QDialog):

    ui_language = "ru"

    TRANSLATIONS = {
        "ru": {
            "startup_dialog_title": "🚀  Автозагрузка Windows",
            "startup_dialog_subtitle": "Управление программами и элементами, запускаемыми вместе с Windows",
            "startup_program": "Программа",
            "startup_source": "Источник",
            "startup_command": "Команда",
            "startup_type": "Тип",
            "startup_status": "Статус",
            "startup_refresh": "🔄  Обновить",
            "startup_disable": "⛔  Отключить",
            "startup_enable": "✅  Включить",
            "startup_close": "Закрыть",
            "enabled": "🟢 Включено",
            "disabled": "🔴 Отключено",
            "stats_enabled": "Включено",
            "stats_disabled": "Отключено",
            "stats_registry": "Реестр",
            "stats_startup_folders": "Папки Startup",
        },
        "uk": {
            "startup_dialog_title": "🚀  Автозавантаження Windows",
            "startup_dialog_subtitle": "Керування програмами та елементами, які запускаються разом із Windows",
            "startup_program": "Програма",
            "startup_source": "Джерело",
            "startup_command": "Команда",
            "startup_type": "Тип",
            "startup_status": "Статус",
            "startup_refresh": "🔄  Оновити",
            "startup_disable": "⛔  Вимкнути",
            "startup_enable": "✅  Увімкнути",
            "enabled": "🟢 Увімкнено",
            "disabled": "🔴 Вимкнено",
            "stats_enabled": "Увімкнено",
            "stats_disabled": "Вимкнено",
            "stats_registry": "Реєстр",
            "stats_startup_folders": "Папки автозапуску",
            
        },
        "en": {
            "startup_dialog_title": "🚀  Windows Startup",
            "startup_dialog_subtitle": "Manage programs and items that start with Windows",
            "startup_program": "Program",
            "startup_source": "Source",
            "startup_command": "Command",
            "startup_type": "Type",
            "startup_status": "Status",
            "startup_refresh": "🔄  Refresh",
            "startup_disable": "⛔  Disable",
            "startup_enable": "✅  Enable",
            "startup_close": "Close",
            "enabled": "🟢 Enabled",
            "disabled": "🔴 Disabled",
            "stats_enabled": "Enabled",
            "stats_disabled": "Disabled",
            "stats_registry": "Registry",
            "stats_startup_folders": "Startup folders",
        },
        "de": {
            "startup_dialog_title": "🚀  Windows-Autostart",
            "startup_dialog_subtitle": "Programme und Elemente verwalten, die zusammen mit Windows gestartet werden",
            "startup_program": "Programm",
            "startup_source": "Quelle",
            "startup_command": "Befehl",
            "startup_type": "Typ",
            "startup_status": "Status",
            "startup_refresh": "🔄  Aktualisieren",
            "startup_disable": "⛔  Deaktivieren",
            "startup_enable": "✅  Aktivieren",
            "startup_close": "Schließen",
            "enabled": "🟢 Aktiviert",
            "disabled": "🔴 Deaktiviert",
            "stats_enabled": "Aktiviert",
            "stats_disabled": "Deaktiviert",
            "stats_registry": "Registrierung",
            "stats_startup_folders": "Startup-Ordner",
        },
        "it": {
            "startup_dialog_title": "🚀  Avvio di Windows",
            "startup_dialog_subtitle": "Gestisci programmi ed elementi che vengono avviati insieme a Windows",
            "startup_program": "Programma",
            "startup_source": "Origine",
            "startup_command": "Comando",
            "startup_type": "Tipo",
            "startup_status": "Stato",
            "startup_refresh": "🔄  Aggiorna",
            "startup_disable": "⛔  Disabilita",
            "startup_enable": "✅  Abilita",
            "startup_close": "Chiudi",
            "enabled": "🟢 Abilitato",
            "disabled": "🔴 Disabilitato",
            "stats_enabled": "Abilitato",
            "stats_disabled": "Disabilitato",
            "stats_registry": "Registro",
            "stats_startup_folders": "Cartelle di avvio",
        },
        "es": {
            "startup_dialog_title": "🚀  Inicio de Windows",
            "startup_dialog_subtitle": "Gestiona los programas y elementos que se inician con Windows",
            "startup_program": "Programa",
            "startup_source": "Origen",
            "startup_command": "Comando",
            "startup_type": "Tipo",
            "startup_status": "Estado",
            "startup_refresh": "🔄  Actualizar",
            "startup_disable": "⛔  Deshabilitar",
            "startup_enable": "✅  Habilitar",
            "startup_close": "Cerrar",
            "enabled": "🟢 Activado",
            "disabled": "🔴 Desactivado",
            "stats_enabled": "Activado",
            "stats_disabled": "Desactivado",
            "stats_registry": "Registro",
            "stats_startup_folders": "Carpetas de inicio",
        },
        "fr": {
            "startup_dialog_title": "🚀  Démarrage de Windows",
            "startup_dialog_subtitle": "Gérer les programmes et éléments qui se lancent avec Windows",
            "startup_program": "Programme",
            "startup_source": "Source",
            "startup_command": "Commande",
            "startup_type": "Type",
            "startup_status": "Statut",
            "startup_refresh": "🔄  Actualiser",
            "startup_disable": "⛔  Désactiver",
            "startup_enable": "✅  Activer",
            "startup_close": "Fermer",
            "enabled": "🟢 Activé",
            "disabled": "🔴 Désactivé",
            "stats_enabled": "Activé",
            "stats_disabled": "Désactivé",
            "stats_registry": "Registre",
            "stats_startup_folders": "Dossiers de démarrage",
        },
    }

    def _tr(self, key, **kwargs):
        language = getattr(self, "ui_language", "ru")
        table = self.TRANSLATIONS.get(language, self.TRANSLATIONS["ru"])
        text = table.get(key, self.TRANSLATIONS["ru"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def __init__(self, parent=None):
        self.ui_language = getattr(parent, "ui_language", "ru")

        super().__init__(parent)

        self.setWindowTitle(
            "Автозагрузка Windows"
        )

        self.resize(
            1100,
            650,
        )

        self.items = []

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {BG};
                color: {TEXT};
            }}

            QLabel {{
                background: transparent;
                border: none;
            }}

            QTableWidget {{
                background: {CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                gridline-color: {BORDER};
                selection-background-color: #2548ff;
                selection-color: white;
            }}

            QTableWidget::item {{
                padding: 7px;
            }}

            QHeaderView::section {{
                background: #0d1d34;
                color: {TEXT};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 8px;
                font-weight: 700;
            }}

            QPushButton {{
                background: #10203a;
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: #1b3154;
            }}

            QPushButton:disabled {{
                color: #52657e;
                background: #0a1322;
                border-color: #101f34;
            }}
            """
        )

        self._build_ui()
        self._scan()


    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        root.setSpacing(12)

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        title = QLabel(
            self._tr("startup_dialog_title")
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 23px;
                font-weight: 900;
            }}
            """
        )

        root.addWidget(title)

        subtitle = QLabel(
            self._tr("startup_dialog_subtitle")
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 12px;
            }}
            """
        )

        root.addWidget(subtitle)

        # ------------------------------------------------------
        # STATISTICS
        # ------------------------------------------------------

        self.stats = QLabel()

        self.stats.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
            }}
            """
        )

        root.addWidget(self.stats)

        # ------------------------------------------------------
        # TABLE
        # ------------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(
            [
                self._tr("startup_program"),
                self._tr("startup_source"),
                self._tr("startup_command"),
                self._tr("startup_type"),
                self._tr("startup_status"),
            ]
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.table.verticalHeader().setVisible(False)

        self.table.itemSelectionChanged.connect(
            self._update_buttons
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents,
        )

        root.addWidget(
            self.table,
            1,
        )

        # ------------------------------------------------------
        # BUTTONS
        # ------------------------------------------------------

        buttons = QHBoxLayout()

        self.refresh_button = QPushButton(
            self._tr("startup_refresh")
        )

        self.refresh_button.setCursor(
            Qt.PointingHandCursor
        )

        self.refresh_button.clicked.connect(
            self._scan
        )

        buttons.addWidget(
            self.refresh_button
        )

        self.disable_button = QPushButton(
            self._tr("startup_disable")
        )

        self.disable_button.setCursor(
            Qt.PointingHandCursor
        )

        self.disable_button.clicked.connect(
            self._disable_selected
        )

        buttons.addWidget(
            self.disable_button
        )

        self.enable_button = QPushButton(
            self._tr("startup_enable")
        )

        self.enable_button.setCursor(
            Qt.PointingHandCursor
        )

        self.enable_button.clicked.connect(
            self._enable_selected
        )

        buttons.addWidget(
            self.enable_button
        )

        buttons.addStretch()

        close_button = QPushButton(
            self._tr("startup_close")
        )

        close_button.setCursor(
            Qt.PointingHandCursor
        )

        close_button.clicked.connect(
            self.accept
        )

        buttons.addWidget(
            close_button
        )

        root.addLayout(buttons)

        self._update_buttons()


    # ==========================================================
    # SCAN
    # ==========================================================

    
    def _scan(self):

        print(
            "[Startup] Scan started"
        )

        self.refresh_button.setEnabled(
            False
        )

        self.disable_button.setEnabled(
            False
        )

        self.enable_button.setEnabled(
            False
        )

        try:

            result = scan_startup()

        except Exception as exc:

            print(
                f"[Startup] Scan error: {exc}"
            )

            QMessageBox.critical(
                self,
                "Ошибка",
                (
                    "Не удалось получить список "
                    "автозагрузки:\n\n"
                    f"{exc}"
                ),
            )

            self.refresh_button.setEnabled(
                True
            )

            return

        enabled_items = result.get(
            "items",
            [],
        )

        disabled_items = result.get(
            "disabled_items",
            [],
        )

        self.items = (
            list(enabled_items)
            + list(disabled_items)
        )

        self.items.sort(
            key=lambda item: (
                not bool(
                    item.get(
                        "enabled",
                        False,
                    )
                ),
                str(
                    item.get(
                        "location",
                        "",
                    )
                ),
                str(
                    item.get(
                        "name",
                        "",
                    )
                ).lower(),
            )
        )

        registry_count = result.get(
            "registry_count",
            0,
        )

        folder_count = result.get(
            "folder_count",
            0,
        )

        disabled_count = result.get(
            "disabled_count",
            0,
        )

        self.stats.setText(
        f"{self._tr('stats_enabled')}: {len(enabled_items)}    |    "
        f"{self._tr('stats_disabled')}: {disabled_count}    |    "
        f"{self._tr('stats_registry')}: {registry_count}    |    "
        f"{self._tr('stats_startup_folders')}: {folder_count}"
        )

        self.table.setRowCount(
            len(self.items)
        )

        for row, item in enumerate(
            self.items
        ):

            name = str(
                item.get(
                    "name",
                    "",
                )
            )

            location = str(
                item.get(
                    "location",
                    "",
                )
            )

            command = str(
                item.get(
                    "command",
                    "",
                )
            )

            item_type = str(
                item.get(
                    "type",
                    "",
                )
            )

            enabled = bool(
                item.get(
                    "enabled",
                    False,
                )
            )

            if item_type in (
                "registry",
                "registry_disabled",
            ):

                type_text = "Реестр"

            elif item_type in (
                "startup_folder",
                "startup_folder_disabled",
            ):

                type_text = "Папка Startup"

            else:

                type_text = item_type

                status_text = (
                    self._tr("enabled")
                    if enabled
                    else self._tr("disabled")
            )
            status_text = (
                self._tr("enabled")
                if enabled
                else self._tr("disabled")
            )
            values = [
                name,
                location,
                command,
                type_text,
                status_text,
            ]

            for column, value in enumerate(
                values
            ):

                cell = QTableWidgetItem(
                    value
                )

                cell.setToolTip(
                    value
                )

                self.table.setItem(
                    row,
                    column,
                    cell
                )

        self.table.resizeRowsToContents()

        self._update_buttons()

        self.refresh_button.setEnabled(
            True
        )

        print(
            "[Startup] Scan finished:"
            f" items={len(self.items)}"
            f" enabled={len(enabled_items)}"
            f" disabled={disabled_count}"
        )

    # ==========================================================
    # SELECTED ITEM
    # ==========================================================

    def _get_selected_item(self):

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        if row < 0 or row >= len(self.items):
            return None

        return self.items[row]


    # ==========================================================
    # BUTTON STATE
    # ==========================================================

    def _update_buttons(self):

        item = self._get_selected_item()

        if item is None:

            self.disable_button.setEnabled(
                False
            )

            self.enable_button.setEnabled(
                False
            )

            return

        enabled = bool(
            item.get(
                "enabled",
                False,
            )
        )

        self.disable_button.setEnabled(
            enabled
        )

        self.enable_button.setEnabled(
            not enabled
        )


    # ==========================================================
    # DISABLE
    # ==========================================================

    def _disable_selected(self):

        item = self._get_selected_item()

        if item is None:
            return

        name = str(
            item.get(
                "name",
                "этот элемент",
            )
        )

        answer = QMessageBox.question(
            self,
            "Отключение автозагрузки",
            (
                f"Отключить автозагрузку для:\n\n"
                f"{name}\n\n"
                f"Источник: {item.get('location', '')}\n\n"
                f"Программа больше не будет запускаться "
                f"автоматически вместе с Windows."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:

            success, message = disable_startup_item(
                item
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось отключить элемент:\n\n{exc}",
            )

            return

        if success:

            QMessageBox.information(
                self,
                self._tr("startup"),
                message,
            )

            self._scan()

        else:

            QMessageBox.warning(
                self,
                self._tr("startup"),
                message,
            )


    # ==========================================================
    # ENABLE
    # ==========================================================

    def _enable_selected(self):

        item = self._get_selected_item()

        if item is None:
            return

        name = str(
            item.get(
                "name",
                "этот элемент",
            )
        )

        answer = QMessageBox.question(
            self,
            "Включение автозагрузки",
            (
                f"Включить автозагрузку для:\n\n"
                f"{name}\n\n"
                f"Источник: {item.get('location', '')}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:

            success, message = enable_startup_item(
                item
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось включить элемент:\n\n{exc}",
            )

            return

        if success:

            QMessageBox.information(
                self,
                self._tr("startup"),
                message,
            )

            self._scan()

        else:

            QMessageBox.warning(
                self,
                self._tr("startup"),
                message,
            )


# ==============================================================
# TOOLS PAGE
# ==============================================================

class ToolsPage(QWidget):

    ui_language = "ru"

    SUPPORTED_LANGUAGES = ("ru", "uk", "en", "de", "it", "es", "fr")

    TRANSLATIONS = {
        "ru": {
            "title": "Инструменты",
            "subtitle": "Полезные инструменты для обслуживания и диагностики Windows",
            "cleanup": "Очистка системы",
            "cleanup_desc": "Поиск временных файлов, кэша и другого ненужного мусора.",
            "cleanup_button": "Сканировать",
            "startup": "Автозагрузка",
            "startup_desc": "Просмотр программ, которые запускаются вместе с Windows.",
            "startup_button": "Анализировать",
            "security": "Безопасность",
            "security_desc": "Быстрая проверка основных компонентов безопасности Windows.",
            "security_button": "Проверить",
            "system": "Системные инструменты",
            "system_desc": "Доступ к встроенным средствам диагностики Windows.",
            "system_button": "Открыть",
            "security_manual": "Откройте приложение Безопасность Windows вручную.",
            "system_info": "Набор системных инструментов Windows будет добавлен следующим этапом.",
            "system_taskmgr": "Диспетчер задач",
            "system_ device_manager": "Диспетчер устройств",
            "system_disk_management": "Управление дисками",
            "system_services": "Службы Windows",
            "system_event_viewer": "Просмотр событий",
            "system_system_info": "Сведения о системе",
            "system_cmd": "Командная строка",
            "system_powershell": "PowerShell",
            "system_close": "Закрыть",
        },
        "uk": {
            "title": "Інструменти",
            "subtitle": "Корисні інструменти для обслуговування та діагностики Windows",
            "cleanup": "Очищення системи",
            "cleanup_desc": "Пошук тимчасових файлів, кешу та іншого непотрібного сміття.",
            "cleanup_button": "Сканувати",
            "startup": "Автозавантаження",
            "startup_desc": "Перегляд програм, які запускаються разом із Windows.",
            "startup_button": "Аналізувати",
            "security": "Безпека",
            "security_desc": "Швидка перевірка основних компонентів безпеки Windows.",
            "security_button": "Перевірити",
            "system": "Системні інструменти",
            "system_desc": "Доступ до вбудованих засобів діагностики Windows.",
            "system_button": "Відкрити",
            "security_manual": "Відкрийте програму Безпека Windows вручну.",
            "system_info": "Набір системних інструментів Windows буде додано на наступному етапі.",
            "system_taskmgr": "Диспетчер завдань",
            "system_device_manager": "Диспетчер пристроїв",
            "system_disk_management": "Керування дисками",
            "system_services": "Служби Windows",
            "system_event_viewer": "Перегляд подій",
            "system_system_info": "Відомості про систему",
            "system_cmd": "Командний рядок",
            "system_powershell": "PowerShell",
            "system_close": "Закрити",
        },
        "en": {
            "title": "Tools",
            "subtitle": "Useful tools for Windows maintenance and diagnostics",
            "cleanup": "System cleanup",
            "cleanup_desc": "Find temporary files, cache, and other unnecessary data.",
            "cleanup_button": "Scan",
            "startup": "Startup",
            "startup_desc": "View programs that start together with Windows.",
            "startup_button": "Analyze",
            "security": "Security",
            "security_desc": "Quick check of the main Windows security components.",
            "security_button": "Check",
            "system": "System tools",
            "system_desc": "Access built-in Windows diagnostic tools.",
            "system_button": "Open",
            "security_manual": "Open Windows Security manually.",
            "system_info": "Windows system tools will be added in the next stage.",
            "system_taskmgr": "Task Manager",
            "system_device_manager": "Device Manager",
            "system_disk_management": "Disk Management",
            "system_services": "Windows Services",
            "system_event_viewer": "Event Viewer",
            "system_system_info": "System Information",
            "system_cmd": "Command Prompt",
            "system_powershell": "PowerShell",
            "system_close": "Close",
        },
        "de": {
            "title": "Werkzeuge",
            "subtitle": "Nützliche Werkzeuge für Wartung und Diagnose von Windows",
            "cleanup": "Systembereinigung",
            "cleanup_desc": "Temporäre Dateien, Cache und andere unnötige Daten suchen.",
            "cleanup_button": "Scannen",
            "startup": "Autostart",
            "startup_desc": "Programme anzeigen, die zusammen mit Windows gestartet werden.",
            "startup_button": "Analysieren",
            "security": "Sicherheit",
            "security_desc": "Schnelle Prüfung der wichtigsten Windows-Sicherheitskomponenten.",
            "security_button": "Prüfen",
            "system": "Systemwerkzeuge",
            "system_desc": "Zugriff auf integrierte Windows-Diagnosewerkzeuge.",
            "system_button": "Öffnen",
            "security_manual": "Öffnen Sie Windows-Sicherheit manuell.",
            "system_info": "Windows-Systemwerkzeuge werden im nächsten Schritt hinzugefügt.",
            "system_taskmgr": "Task-Manager",
            "system_device_manager": "Geräte-Manager",
            "system_disk_management": "Datenträgerverwaltung",
            "system_services": "Windows-Dienste",
            "system_event_viewer": "Ereignisanzeige",
            "system_system_info": "Systeminformationen",
            "system_cmd": "Eingabeaufforderung",
            "system_powershell": "PowerShell",
            "system_close": "Schließen",
        },
        "it": {
            "title": "Strumenti",
            "subtitle": "Strumenti utili per la manutenzione e la diagnostica di Windows",
            "cleanup": "Pulizia del sistema",
            "cleanup_desc": "Cerca file temporanei, cache e altri dati non necessari.",
            "cleanup_button": "Scansiona",
            "startup": "Avvio automatico",
            "startup_desc": "Visualizza i programmi che vengono avviati insieme a Windows.",
            "startup_button": "Analizza",
            "security": "Sicurezza",
            "security_desc": "Controllo rapido dei principali componenti di sicurezza di Windows.",
            "security_button": "Controlla",
            "system": "Strumenti di sistema",
            "system_desc": "Accesso agli strumenti diagnostici integrati di Windows.",
            "system_button": "Apri",
            "security_manual": "Apri manualmente Sicurezza di Windows.",
            "system_info": "Gli strumenti di sistema di Windows saranno aggiunti nella fase successiva.",
            "system_taskmgr": "Gestione attività",
            "system_device_manager": "Gestione dispositivi",
            "system_disk_management": "Gestione disco",
            "system_services": "Servizi Windows",
            "system_event_viewer": "Visualizzatore eventi",
            "system_system_info": "Informazioni di sistema",
            "system_cmd": "Prompt dei comandi",
            "system_powershell": "PowerShell",
            "system_close": "Chiudi",
        },
        "es": {
            "title": "Herramientas",
            "subtitle": "Herramientas útiles para el mantenimiento y diagnóstico de Windows",
            "cleanup": "Limpieza del sistema",
            "cleanup_desc": "Busca archivos temporales, caché y otros datos innecesarios.",
            "cleanup_button": "Escanear",
            "startup": "Inicio automático",
            "startup_desc": "Ver los programas que se inician junto con Windows.",
            "startup_button": "Analizar",
            "security": "Seguridad",
            "security_desc": "Comprobación rápida de los principales componentes de seguridad de Windows.",
            "security_button": "Comprobar",
            "system": "Herramientas del sistema",
            "system_desc": "Acceso a las herramientas de diagnóstico integradas de Windows.",
            "system_button": "Abrir",
            "security_manual": "Abra Seguridad de Windows manualmente.",
            "system_info": "Las herramientas del sistema de Windows se añadirán en la siguiente etapa.",
            "system_taskmgr": "Administrador de tareas",
            "system_device_manager": "Administrador de dispositivos",
            "system_disk_management": "Administración de discos",
            "system_services": "Servicios de Windows",
            "system_event_viewer": "Visor de eventos",
            "system_system_info": "Información del sistema",
            "system_cmd": "Símbolo del sistema",
            "system_powershell": "PowerShell",
            "system_close": "Cerrar",
        },
        "fr": {
            "title": "Outils",
            "subtitle": "Outils utiles pour la maintenance et le diagnostic de Windows",
            "cleanup": "Nettoyage du système",
            "cleanup_desc": "Recherche les fichiers temporaires, le cache et autres données inutiles.",
            "cleanup_button": "Analyser",
            "startup": "Démarrage",
            "startup_desc": "Afficher les programmes qui se lancent avec Windows.",
            "startup_button": "Analyser",
            "security": "Sécurité",
            "security_desc": "Vérification rapide des principaux composants de sécurité de Windows.",
            "security_button": "Vérifier",
            "system": "Outils système",
            "system_desc": "Accès aux outils de diagnostic intégrés de Windows.",
            "system_button": "Ouvrir",
            "security_manual": "Ouvrez manuellement Sécurité Windows.",
            "system_info": "Les outils système de Windows seront ajoutés à l'étape suivante.",
            "system_taskmgr": "Gestionnaire des tâches",
            "system_device_manager": "Gestionnaire de périphériques",
            "system_disk_management": "Gestion des disques",
            "system_services": "Services Windows",
            "system_event_viewer": "Observateur d’événements",
            "system_system_info": "Informations système",
            "system_cmd": "Invite de commandes",
            "system_powershell": "PowerShell",
            "system_close": "Fermer",
        },
    }

    def _tr(self, key, **kwargs):
        language = getattr(self, "ui_language", "ru")
        table = self.TRANSLATIONS.get(language, self.TRANSLATIONS["ru"])
        text = table.get(key, self.TRANSLATIONS["ru"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        self.main_window = parent

        self.setObjectName(
            "ToolsPage"
        )

        self.setStyleSheet(
            f"""
            QWidget#ToolsPage {{
                background: {BG};
                color: {TEXT};
            }}

            QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )

        self._build_ui()
    def set_language(self, language):
        language = str(language or "ru")

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        if hasattr(self, "title_label"):
            self.title_label.setText(self._tr("title"))

        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(self._tr("subtitle"))

        if hasattr(self, "cleanup_card"):
            self.cleanup_card.set_content(
                self._tr("cleanup"),
                self._tr("cleanup_desc"),
                self._tr("cleanup_button"),
            )

        if hasattr(self, "startup_card"):
            self.startup_card.set_content(
                self._tr("startup"),
                self._tr("startup_desc"),
                self._tr("startup_button"),
            )

        if hasattr(self, "security_card"):
            self.security_card.set_content(
                self._tr("security"),
                self._tr("security_desc"),
                self._tr("security_button"),
            )

        if hasattr(self, "system_card"):
            self.system_card.set_content(
                self._tr("system"),
                self._tr("system_desc"),
                self._tr("system_button"),
            )



    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        root.setSpacing(
            14
        )

        # ------------------------------------------------------
        # TITLE
        # ------------------------------------------------------

        self.title_label = QLabel(self._tr("title"))

        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 25px;
                font-weight: 900;
            }}
            """
        )

        root.addWidget(self.title_label)

        self.subtitle_label = QLabel(self._tr("subtitle"))

        self.subtitle_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 13px;
            }}
            """
        )

        root.addWidget(self.subtitle_label)

        # ------------------------------------------------------
        # CARDS
        # ------------------------------------------------------

        grid = QGridLayout()

        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        # ------------------------------------------------------
        # CLEANUP
        # ------------------------------------------------------

        self.cleanup_card = ToolCard(
            "🧹",
            self._tr("cleanup"),
            self._tr("cleanup_desc"),
            self._tr("cleanup_button"),
            BLUE,
        )

        self.cleanup_card.button.clicked.connect(
            self._cleanup
        )

        grid.addWidget(
            self.cleanup_card,
            0,
            0,
        )

        # ------------------------------------------------------
        # STARTUP
        # ------------------------------------------------------

        self.startup_card = ToolCard(
            "🚀",
            self._tr("startup"),
            self._tr("startup_desc"),
            self._tr("startup_button"),
            GREEN,
        )

        self.startup_card.button.clicked.connect(
            self._startup
        )

        grid.addWidget(
            self.startup_card,
            0,
            1,
        )

        # ------------------------------------------------------
        # SECURITY
        # ------------------------------------------------------

        self.security_card = ToolCard(
            "🛡",
            self._tr("security"),
            self._tr("security_desc"),
            self._tr("security_button"),
            PURPLE,
        )

        self.security_card.button.clicked.connect(
            self._security
        )

        grid.addWidget(
            self.security_card,
            1,
            0,
        )

        # ------------------------------------------------------
        # SYSTEM
        # ------------------------------------------------------

        self.system_card = ToolCard(
            "⚙",
            self._tr("system"),
            self._tr("system_desc"),
            self._tr("system_button"),
            ORANGE,
        )

        self.system_card.button.clicked.connect(
            self._system_tools
        )

        grid.addWidget(
            self.system_card,
            1,
            1,
        )

        root.addLayout(grid)

        root.addStretch()


    # ==========================================================
    # ACTIONS
    # ==========================================================

    def _cleanup(self):

        print(
            "[Tools] Cleanup manager requested"
        )

        dialog = CleanupDialog(
            self
        )

        dialog.exec()


    def _startup(self):

        print(
            "[Tools] Startup manager requested"
        )

        dialog = StartupDialog(
            self
        )

        dialog.exec()


    def _security(self):

        print(
            "[Tools] Security diagnostic requested"
        )

        # Открываем встроенную страницу Windows Security вместо
        # неработающей заглушки.
        if self.main_window and hasattr(self.main_window, "_open_uri"):
            self.main_window._open_uri("ms-settings:windowsdefender")
        else:
            QMessageBox.information(
                self,
                self._tr("security"),
                self._tr("security_manual"),
        )


    def _system_tools(self):

        print(
            "[Tools] System tools requested"
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(self._tr("system"))
        dialog.setMinimumWidth(420)

        layout = QVBoxLayout(dialog)

        tools = [
            (self._tr("system_taskmgr"), "taskmgr.exe"),
            (self._tr("system_device_manager"), "devmgmt.msc"),
            (self._tr("system_disk_management"), "diskmgmt.msc"),
            (self._tr("system_services"), "services.msc"),
            (self._tr("system_event_viewer"), "eventvwr.msc"),
            (self._tr("system_system_info"), "msinfo32.exe"),
            (self._tr("system_cmd"), "cmd.exe"),
            (self._tr("system_powershell"), "powershell.exe"),
        ]

        for title, command in tools:
            button = QPushButton(title)
            button.setMinimumHeight(40)
            button.clicked.connect(
                lambda checked=False, cmd=command:
                subprocess.Popen(["cmd.exe", "/c", "start", "", cmd], shell=False)
            )
            layout.addWidget(button)

        close_button = QPushButton(self._tr("system_close"))
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()




