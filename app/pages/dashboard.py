import os
import time
from collections import deque

import psutil

from PySide6.QtCore import QTimer, Qt, QThread, Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QMessageBox,
    QSizePolicy,
)

from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap

from app.services.system_info import (
    get_memory_info,
    get_system_info,
    get_motherboard_info,
    get_bios_info,
)

from app.services.gpu_info import get_cached_gpu_info
from app.services.ai_analyzer import AIAnalyzer
from app.services.cleanup_service import scan_temp_files, delete_temp_files
class SystemMonitorIllustration(QWidget):
    """Небольшая декоративная иллюстрация монитора для карточки системы."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 120)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Область монитора
        monitor_w = min(170, w - 20)
        monitor_h = min(92, h - 28)

        x = (w - monitor_w) / 2
        y = max(4, (h - monitor_h - 18) / 2)

        # Корпус монитора
        painter.setPen(
            QPen(QColor("#29415f"), 2)
        )
        painter.setBrush(
            QBrush(QColor("#091528"))
        )

        painter.drawRoundedRect(
            int(x),
            int(y),
            int(monitor_w),
            int(monitor_h),
            9,
            9,
        )

        # Экран
        screen_margin = 8

        painter.setPen(
            QPen(QColor("#168cff"), 1)
        )
        painter.setBrush(
            QBrush(QColor("#050b18"))
        )

        painter.drawRoundedRect(
            int(x + screen_margin),
            int(y + screen_margin),
            int(monitor_w - screen_margin * 2),
            int(monitor_h - screen_margin * 2),
            5,
            5,
        )

        # Условные линии интерфейса на экране
        painter.setPen(
            QPen(QColor("#22d3ee"), 2)
        )

        line_x = x + 18
        line_y = y + 25

        for i, length in enumerate((72, 52, 86)):
            painter.drawLine(
                int(line_x),
                int(line_y + i * 12),
                int(line_x + length),
                int(line_y + i * 12),
            )

        # Маленькие индикаторы
        for i, color in enumerate(
            ("#22d3ee", "#22e889", "#a970ff")
        ):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(
                int(x + monitor_w - 30),
                int(y + 23 + i * 13),
                5,
                5,
            )

        # Подставка
        painter.setPen(
            QPen(QColor("#29415f"), 2)
        )

        center_x = x + monitor_w / 2

        painter.drawLine(
            int(center_x),
            int(y + monitor_h),
            int(center_x),
            int(y + monitor_h + 12),
        )

        painter.drawLine(
            int(center_x - 28),
            int(y + monitor_h + 12),
            int(center_x + 28),
            int(y + monitor_h + 12),
        )

        painter.end()
from app.widgets.dashboard_widgets import (
    CardFrame,
    PerformanceGauge,
    ResourceOverview,
    RealtimeGraph,
)


BG = "#050b18"
TEXT = "#f4f7ff"
MUTED = "#8ea3bd"
BORDER = "#1d3152"


class AIWorker(QThread):
    result_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, analyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        try:
            if self._stop_requested:
                return

            result = self.analyzer.analyze()

            if self._stop_requested:
                print("[AIWorker] Result ignored because shutdown started")
                return

            if result:
                self.result_ready.emit(result)

        except Exception as exc:
            if not self._stop_requested:
                self.error.emit(str(exc))

    def stop(self, timeout=15000):
        if not self.isRunning():
            return True

        print("[AIWorker] Stop requested")
        self.request_stop()
        print("[AIWorker] Waiting for thread...")

        finished = self.wait(timeout)

        if finished:
            print("[AIWorker] Thread stopped")
            return True

        print(
            "[AIWorker] WARNING: "
            f"thread did not finish within {timeout / 1000:.0f} seconds"
        )
        return False


class DashboardPage(QWidget):

    TRANSLATIONS = {
        "ru": {
            "system_info": "Информация о системе",
            "board": "Материнская плата",
            "bios": "BIOS",
            "uptime": "Время работы",
            "system": "Система",
            "launch": "Запуск",
            "current_session": "текущий сеанс",
            "details": "ⓘ  Подробная информация",

            "quick_actions": "Быстрые действия",
            "quick_optimize": "Быстрая оптимизация",
            "quick_optimize_desc": "Улучшить систему в один клик",
            "cleanup": "Очистка",
            "cleanup_desc": "Удалить временные файлы и мусор",
            "startup": "Автозагрузка",
            "startup_desc": "Управление автозагрузкой",
            "security": "Безопасность",
            "security_desc": "Проверить состояние системы",

            "ai_title": "AI-помощник",
            "ai_open": "Анализ системы  ›",
            "hello": "Привет, {username}! 👋",
            "ai_description": "Анализирую состояние вашей системы...",
            "ai_analyzing": "●  Анализирую систему...",
            "ai_checking": "Проверяю состояние компьютера...",
            "ai_check": "●  Проверка системы",
            "ai_details": "✦  Показать детали",
            "ai_cleanup": "Проверить временные файлы",
            "ai_analyzed": "Я проанализировал состояние вашей системы.",
            "ai_good": "●  Система работает стабильно",
            "ai_attention": "●  Требуется внимание",
            "ai_critical": "●  Обнаружены проблемы",
            "ai_unknown": "●  Статус неизвестен",
            "recommendations": "Рекомендации: {count}",
            "recommendation": "Рекомендация",
            "no_problems": "✓ Проблем не обнаружено.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Диск",

            "temp_found": (
                "Найдено временных файлов: {megabytes:.1f} МБ.\n"
                "Их можно удалить."
            ),
            "delete_found": "Удалить найденное",
            "temp_not_found": "Временные файлы для удаления не найдены.",
            "cleanup_title": "Очистка временных файлов",
            "cleanup_question": "Удалить найденные временные файлы?",
            "cleanup_info": (
                "Будут удалены только файлы из системных "
                "TEMP/TMP каталогов, доступные приложению."
            ),
            "deleting": "Удаление...",
            "cleanup_done": "●  Очистка завершена",
            "deleted": (
                "Удалено: {files} файлов • {megabytes:.1f} МБ\n"
                "Папок удалено: {folders}\n"
                "Пропущено: {skipped} • Ошибок: {errors}"
            ),
            "check_again": "Повторно проверить",
            "cleanup_error": "●  Ошибка очистки",
            "cleanup_error_text": "Не удалось выполнить очистку:\n{error}",
            "retry": "Повторить",

            "ai_error": "Не удалось выполнить анализ системы.",
            "ai_error_status": "●  Ошибка AI-анализа",

            "last_scan": "◷  Последнее сканирование:  —",
            "updates": "↻  Проверить обновления",
            "protected": "✓  Система защищена",
            "monitor_error": "⚠  Ошибка мониторинга: {error}",

            "today": "Сегодня",
            "day": "дн.",
            "hour": "ч.",
            "minute": "мин.",
            "unknown": "—",
            "launch_session": "текущий сеанс",
        },

        "en": {
            "system_info": "System Information",
            "board": "Motherboard",
            "bios": "BIOS",
            "uptime": "Uptime",
            "system": "System",
            "launch": "Launch",
            "current_session": "current session",
            "details": "ⓘ  Detailed information",

            "quick_actions": "Quick Actions",
            "quick_optimize": "Quick Optimization",
            "quick_optimize_desc": "Improve the system in one click",
            "cleanup": "Cleanup",
            "cleanup_desc": "Remove temporary files and junk",
            "startup": "Startup",
            "startup_desc": "Manage startup applications",
            "security": "Security",
            "security_desc": "Check system security",

            "ai_title": "AI Assistant",
            "ai_open": "System analysis  ›",
            "hello": "Hello, {username}! 👋",
            "ai_description": "Analyzing your system...",
            "ai_analyzing": "●  Analyzing system...",
            "ai_checking": "Checking computer status...",
            "ai_check": "●  System check",
            "ai_details": "✦  Show details",
            "ai_cleanup": "Check temporary files",
            "ai_analyzed": "I analyzed the state of your system.",
            "ai_good": "●  System is running normally",
            "ai_attention": "●  Attention required",
            "ai_critical": "●  Problems detected",
            "ai_unknown": "●  Status unknown",
            "recommendations": "Recommendations: {count}",
            "recommendation": "Recommendation",
            "no_problems": "✓ No problems detected.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Disk",

            "temp_found": (
                "Temporary files found: {megabytes:.1f} MB.\n"
                "They can be deleted."
            ),
            "delete_found": "Delete found files",
            "temp_not_found": "No temporary files found for deletion.",
            "cleanup_title": "Temporary File Cleanup",
            "cleanup_question": "Delete the found temporary files?",
            "cleanup_info": (
                "Only files from system TEMP/TMP directories "
                "accessible to the application will be deleted."
            ),
            "deleting": "Deleting...",
            "cleanup_done": "●  Cleanup completed",
            "deleted": (
                "Deleted: {files} files • {megabytes:.1f} MB\n"
                "Folders deleted: {folders}\n"
                "Skipped: {skipped} • Errors: {errors}"
            ),
            "check_again": "Check again",
            "cleanup_error": "●  Cleanup error",
            "cleanup_error_text": "Cleanup failed:\n{error}",
            "retry": "Retry",

            "ai_error": "System analysis could not be completed.",
            "ai_error_status": "●  AI analysis error",

            "last_scan": "◷  Last scan:  —",
            "updates": "↻  Check for updates",
            "protected": "✓  System protected",
            "monitor_error": "⚠  Monitoring error: {error}",

            "today": "Today",
            "day": "d.",
            "hour": "h.",
            "minute": "min.",
            "unknown": "—",
            "launch_session": "current session",
        },

        "uk": {
            "system_info": "Інформація про систему",
            "board": "Материнська плата",
            "bios": "BIOS",
            "uptime": "Час роботи",
            "system": "Система",
            "launch": "Запуск",
            "current_session": "поточний сеанс",
            "details": "ⓘ  Детальна інформація",

            "quick_actions": "Швидкі дії",
            "quick_optimize": "Швидка оптимізація",
            "quick_optimize_desc": "Покращити систему одним натисканням",
            "cleanup": "Очищення",
            "cleanup_desc": "Видалити тимчасові файли та сміття",
            "startup": "Автозавантаження",
            "startup_desc": "Керування автозавантаженням",
            "security": "Безпека",
            "security_desc": "Перевірити стан системи",

            "ai_title": "AI-помічник",
            "ai_open": "Аналіз системи  ›",
            "hello": "Вітаю, {username}! 👋",
            "ai_description": "Аналізую стан вашої системи...",
            "ai_analyzing": "●  Аналізую систему...",
            "ai_checking": "Перевіряю стан комп'ютера...",
            "ai_check": "●  Перевірка системи",
            "ai_details": "✦  Показати деталі",
            "ai_cleanup": "Перевірити тимчасові файли",
            "ai_analyzed": "Я проаналізував стан вашої системи.",
            "ai_good": "●  Система працює стабільно",
            "ai_attention": "●  Потрібна увага",
            "ai_critical": "●  Виявлено проблеми",
            "ai_unknown": "●  Статус невідомий",
            "recommendations": "Рекомендації: {count}",
            "recommendation": "Рекомендація",
            "no_problems": "✓ Проблем не виявлено.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Диск",

            "temp_found": (
                "Знайдено тимчасових файлів: {megabytes:.1f} МБ.\n"
                "Їх можна видалити."
            ),
            "delete_found": "Видалити знайдене",
            "temp_not_found": "Тимчасових файлів для видалення не знайдено.",
            "cleanup_title": "Очищення тимчасових файлів",
            "cleanup_question": "Видалити знайдені тимчасові файли?",
            "cleanup_info": (
                "Буде видалено лише файли із системних "
                "TEMP/TMP каталогів, доступні застосунку."
            ),
            "deleting": "Видалення...",
            "cleanup_done": "●  Очищення завершено",
            "deleted": (
                "Видалено: {files} файлів • {megabytes:.1f} МБ\n"
                "Папок видалено: {folders}\n"
                "Пропущено: {skipped} • Помилок: {errors}"
            ),
            "check_again": "Перевірити повторно",
            "cleanup_error": "●  Помилка очищення",
            "cleanup_error_text": "Не вдалося виконати очищення:\n{error}",
            "retry": "Повторити",

            "ai_error": "Не вдалося виконати аналіз системи.",
            "ai_error_status": "●  Помилка AI-аналізу",

            "last_scan": "◷  Останнє сканування:  —",
            "updates": "↻  Перевірити оновлення",
            "protected": "✓  Система захищена",
            "monitor_error": "⚠  Помилка моніторингу: {error}",

            "today": "Сьогодні",
            "day": "дн.",
            "hour": "год.",
            "minute": "хв.",
            "unknown": "—",
            "launch_session": "поточний сеанс",
        },

        "de": {
            "system_info": "Systeminformationen",
            "board": "Mainboard",
            "bios": "BIOS",
            "uptime": "Laufzeit",
            "system": "System",
            "launch": "Start",
            "current_session": "aktuelle Sitzung",
            "details": "ⓘ  Detaillierte Informationen",

            "quick_actions": "Schnellaktionen",
            "quick_optimize": "Schnelloptimierung",
            "quick_optimize_desc": "System mit einem Klick verbessern",
            "cleanup": "Bereinigung",
            "cleanup_desc": "Temporäre Dateien und Datenmüll entfernen",
            "startup": "Autostart",
            "startup_desc": "Autostart verwalten",
            "security": "Sicherheit",
            "security_desc": "Systemstatus prüfen",

            "ai_title": "KI-Assistent",
            "ai_open": "Systemanalyse  ›",
            "hello": "Hallo, {username}! 👋",
            "ai_description": "Systemstatus wird analysiert...",
            "ai_analyzing": "●  System wird analysiert...",
            "ai_checking": "Computerstatus wird geprüft...",
            "ai_check": "●  Systemprüfung",
            "ai_details": "✦  Details anzeigen",
            "ai_cleanup": "Temporäre Dateien prüfen",
            "ai_analyzed": "Ich habe den Zustand Ihres Systems analysiert.",
            "ai_good": "●  System arbeitet stabil",
            "ai_attention": "●  Aufmerksamkeit erforderlich",
            "ai_critical": "●  Probleme erkannt",
            "ai_unknown": "●  Status unbekannt",
            "recommendations": "Empfehlungen: {count}",
            "recommendation": "Empfehlung",
            "no_problems": "✓ Keine Probleme erkannt.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Datenträger",

            "temp_found": (
                "Temporäre Dateien gefunden: {megabytes:.1f} MB.\n"
                "Sie können gelöscht werden."
            ),
            "delete_found": "Gefundene Dateien löschen",
            "temp_not_found": "Keine temporären Dateien zum Löschen gefunden.",
            "cleanup_title": "Bereinigung temporärer Dateien",
            "cleanup_question": "Gefundene temporäre Dateien löschen?",
            "cleanup_info": (
                "Es werden nur Dateien aus den für die Anwendung "
                "zugänglichen TEMP/TMP-Verzeichnissen gelöscht."
            ),
            "deleting": "Wird gelöscht...",
            "cleanup_done": "●  Bereinigung abgeschlossen",
            "deleted": (
                "Gelöscht: {files} Dateien • {megabytes:.1f} MB\n"
                "Gelöschte Ordner: {folders}\n"
                "Übersprungen: {skipped} • Fehler: {errors}"
            ),
            "check_again": "Erneut prüfen",
            "cleanup_error": "●  Bereinigungsfehler",
            "cleanup_error_text": "Bereinigung fehlgeschlagen:\n{error}",
            "retry": "Erneut versuchen",

            "ai_error": "Die Systemanalyse konnte nicht durchgeführt werden.",
            "ai_error_status": "●  KI-Analysefehler",

            "last_scan": "◷  Letzter Scan:  —",
            "updates": "↻  Nach Updates suchen",
            "protected": "✓  System geschützt",
            "monitor_error": "⚠  Überwachungsfehler: {error}",

            "today": "Heute",
            "day": "T.",
            "hour": "Std.",
            "minute": "Min.",
            "unknown": "—",
            "launch_session": "aktuelle Sitzung",
        },

        "it": {
            "system_info": "Informazioni di sistema",
            "board": "Scheda madre",
            "bios": "BIOS",
            "uptime": "Tempo di attività",
            "system": "Sistema",
            "launch": "Avvio",
            "current_session": "sessione corrente",
            "details": "ⓘ  Informazioni dettagliate",

            "quick_actions": "Azioni rapide",
            "quick_optimize": "Ottimizzazione rapida",
            "quick_optimize_desc": "Migliora il sistema con un clic",
            "cleanup": "Pulizia",
            "cleanup_desc": "Rimuovi file temporanei e spazzatura",
            "startup": "Avvio automatico",
            "startup_desc": "Gestisci l'avvio automatico",
            "security": "Sicurezza",
            "security_desc": "Controlla lo stato del sistema",

            "ai_title": "Assistente AI",
            "ai_open": "Analisi del sistema  ›",
            "hello": "Ciao, {username}! 👋",
            "ai_description": "Analizzo lo stato del sistema...",
            "ai_analyzing": "●  Analisi del sistema...",
            "ai_checking": "Controllo lo stato del computer...",
            "ai_check": "●  Controllo del sistema",
            "ai_details": "✦  Mostra dettagli",
            "ai_cleanup": "Controlla i file temporanei",
            "ai_analyzed": "Ho analizzato lo stato del sistema.",
            "ai_good": "●  Il sistema funziona stabilmente",
            "ai_attention": "●  È necessaria attenzione",
            "ai_critical": "●  Problemi rilevati",
            "ai_unknown": "●  Stato sconosciuto",
            "recommendations": "Raccomandazioni: {count}",
            "recommendation": "Raccomandazione",
            "no_problems": "✓ Nessun problema rilevato.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Disco",

            "temp_found": (
                "File temporanei trovati: {megabytes:.1f} MB.\n"
                "Possono essere eliminati."
            ),
            "delete_found": "Elimina elementi trovati",
            "temp_not_found": "Nessun file temporaneo da eliminare.",
            "cleanup_title": "Pulizia dei file temporanei",
            "cleanup_question": "Eliminare i file temporanei trovati?",
            "cleanup_info": (
                "Verranno eliminati solo i file dalle cartelle "
                "TEMP/TMP di sistema accessibili all'applicazione."
            ),
            "deleting": "Eliminazione...",
            "cleanup_done": "●  Pulizia completata",
            "deleted": (
                "Eliminati: {files} file • {megabytes:.1f} MB\n"
                "Cartelle eliminate: {folders}\n"
                "Saltati: {skipped} • Errori: {errors}"
            ),
            "check_again": "Controlla di nuovo",
            "cleanup_error": "●  Errore di pulizia",
            "cleanup_error_text": "Pulizia non riuscita:\n{error}",
            "retry": "Riprova",

            "ai_error": "Impossibile completare l'analisi del sistema.",
            "ai_error_status": "●  Errore analisi AI",

            "last_scan": "◷  Ultima scansione:  —",
            "updates": "↻  Controlla aggiornamenti",
            "protected": "✓  Sistema protetto",
            "monitor_error": "⚠  Errore monitoraggio: {error}",

            "today": "Oggi",
            "day": "g.",
            "hour": "h.",
            "minute": "min.",
            "unknown": "—",
            "launch_session": "sessione corrente",
        },

        "es": {
            "system_info": "Información del sistema",
            "board": "Placa base",
            "bios": "BIOS",
            "uptime": "Tiempo de actividad",
            "system": "Sistema",
            "launch": "Inicio",
            "current_session": "sesión actual",
            "details": "ⓘ  Información detallada",

            "quick_actions": "Acciones rápidas",
            "quick_optimize": "Optimización rápida",
            "quick_optimize_desc": "Mejora el sistema con un clic",
            "cleanup": "Limpieza",
            "cleanup_desc": "Eliminar archivos temporales y basura",
            "startup": "Inicio automático",
            "startup_desc": "Gestionar programas de inicio",
            "security": "Seguridad",
            "security_desc": "Comprobar el estado del sistema",

            "ai_title": "Asistente de IA",
            "ai_open": "Análisis del sistema  ›",
            "hello": "¡Hola, {username}! 👋",
            "ai_description": "Analizando el estado del sistema...",
            "ai_analyzing": "●  Analizando el sistema...",
            "ai_checking": "Comprobando el estado del equipo...",
            "ai_check": "●  Comprobación del sistema",
            "ai_details": "✦  Mostrar detalles",
            "ai_cleanup": "Comprobar archivos temporales",
            "ai_analyzed": "He analizado el estado del sistema.",
            "ai_good": "●  El sistema funciona con normalidad",
            "ai_attention": "●  Se requiere atención",
            "ai_critical": "●  Se han detectado problemas",
            "ai_unknown": "●  Estado desconocido",
            "recommendations": "Recomendaciones: {count}",
            "recommendation": "Recomendación",
            "no_problems": "✓ No se han detectado problemas.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Disco",

            "temp_found": (
                "Archivos temporales encontrados: {megabytes:.1f} MB.\n"
                "Se pueden eliminar."
            ),
            "delete_found": "Eliminar encontrados",
            "temp_not_found": "No se encontraron archivos temporales para eliminar.",
            "cleanup_title": "Limpieza de archivos temporales",
            "cleanup_question": "¿Eliminar los archivos temporales encontrados?",
            "cleanup_info": (
                "Solo se eliminarán archivos de los directorios "
                "TEMP/TMP del sistema accesibles para la aplicación."
            ),
            "deleting": "Eliminando...",
            "cleanup_done": "●  Limpieza completada",
            "deleted": (
                "Eliminados: {files} archivos • {megabytes:.1f} MB\n"
                "Carpetas eliminadas: {folders}\n"
                "Omitidos: {skipped} • Errores: {errors}"
            ),
            "check_again": "Comprobar de nuevo",
            "cleanup_error": "●  Error de limpieza",
            "cleanup_error_text": "No se pudo realizar la limpieza:\n{error}",
            "retry": "Reintentar",

            "ai_error": "No se pudo completar el análisis del sistema.",
            "ai_error_status": "●  Error de análisis de IA",

            "last_scan": "◷  Último análisis:  —",
            "updates": "↻  Buscar actualizaciones",
            "protected": "✓  Sistema protegido",
            "monitor_error": "⚠  Error de monitorización: {error}",

            "today": "Hoy",
            "day": "d.",
            "hour": "h.",
            "minute": "min.",
            "unknown": "—",
            "launch_session": "sesión actual",
        },

        "fr": {
            "system_info": "Informations système",
            "board": "Carte mère",
            "bios": "BIOS",
            "uptime": "Temps de fonctionnement",
            "system": "Système",
            "launch": "Démarrage",
            "current_session": "session actuelle",
            "details": "ⓘ  Informations détaillées",

            "quick_actions": "Actions rapides",
            "quick_optimize": "Optimisation rapide",
            "quick_optimize_desc": "Améliorer le système en un clic",
            "cleanup": "Nettoyage",
            "cleanup_desc": "Supprimer les fichiers temporaires et inutiles",
            "startup": "Démarrage automatique",
            "startup_desc": "Gérer les programmes au démarrage",
            "security": "Sécurité",
            "security_desc": "Vérifier l'état du système",

            "ai_title": "Assistant IA",
            "ai_open": "Analyse du système  ›",
            "hello": "Bonjour, {username} ! 👋",
            "ai_description": "Analyse de l'état du système...",
            "ai_analyzing": "●  Analyse du système...",
            "ai_checking": "Vérification de l'état de l'ordinateur...",
            "ai_check": "●  Vérification du système",
            "ai_details": "✦  Afficher les détails",
            "ai_cleanup": "Vérifier les fichiers temporaires",
            "ai_analyzed": "J'ai analysé l'état de votre système.",
            "ai_good": "●  Le système fonctionne normalement",
            "ai_attention": "●  Attention requise",
            "ai_critical": "●  Problèmes détectés",
            "ai_unknown": "●  État inconnu",
            "recommendations": "Recommandations : {count}",
            "recommendation": "Recommandation",
            "no_problems": "✓ Aucun problème détecté.",
            "cpu": "CPU",
            "ram": "RAM",
            "disk": "Disque",

            "temp_found": (
                "Fichiers temporaires trouvés : {megabytes:.1f} Mo.\n"
                "Ils peuvent être supprimés."
            ),
            "delete_found": "Supprimer les éléments trouvés",
            "temp_not_found": "Aucun fichier temporaire à supprimer.",
            "cleanup_title": "Nettoyage des fichiers temporaires",
            "cleanup_question": "Supprimer les fichiers temporaires trouvés ?",
            "cleanup_info": (
                "Seuls les fichiers des répertoires TEMP/TMP système "
                "accessibles à l'application seront supprimés."
            ),
            "deleting": "Suppression...",
            "cleanup_done": "●  Nettoyage terminé",
            "deleted": (
                "Supprimés : {files} fichiers • {megabytes:.1f} Mo\n"
                "Dossiers supprimés : {folders}\n"
                "Ignorés : {skipped} • Erreurs : {errors}"
            ),
            "check_again": "Vérifier à nouveau",
            "cleanup_error": "●  Erreur de nettoyage",
            "cleanup_error_text": "Échec du nettoyage :\n{error}",
            "retry": "Réessayer",

            "ai_error": "Impossible de terminer l'analyse du système.",
            "ai_error_status": "●  Erreur d'analyse IA",

            "last_scan": "◷  Dernière analyse :  —",
            "updates": "↻  Vérifier les mises à jour",
            "protected": "✓  Système protégé",
            "monitor_error": "⚠  Erreur de surveillance : {error}",

            "today": "Aujourd'hui",
            "day": "j.",
            "hour": "h",
            "minute": "min.",
            "unknown": "—",
            "launch_session": "session actuelle",
        },
    }

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)

        self.main_window = (
            main_window if main_window is not None else parent
        )

        self.setObjectName("DashboardPage")

        self.setStyleSheet(
            f"""
            QWidget#DashboardPage {{
                background: {BG};
                color: {TEXT};
            }}

            QLabel {{
                color: {TEXT};
            }}
            """
        )

        self._closing = False

        self.ui_language = "ru"

        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        self.gpu_history = deque(maxlen=60)
        self.disk_history = deque(maxlen=60)

        self.ai_analyzer = AIAnalyzer()
        self.ai_worker = None

        self._system_info_cache = {}
        self._motherboard_cache = {}
        self._bios_cache = {}

        self._system_info_loaded = False
        self._last_uptime_update = 0.0
        self._last_ai_result = None

        self._build_ui()
        self._load_static_system_info()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(700)

        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.update_ai_panel)
        self.ai_timer.start(30000)

        self.update_dashboard()
        QTimer.singleShot(500, self.update_ai_panel)

    # ==========================================================
    # TRANSLATION
    # ==========================================================

    def _tr(self, key, **kwargs):
        language = (
            self.ui_language
            if self.ui_language in self.TRANSLATIONS
            else "ru"
        )

        text = self.TRANSLATIONS[language].get(
            key,
            self.TRANSLATIONS["ru"].get(key, key),
        )

        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text

    def set_language(self, language):
        """
        Переключает язык Dashboard.

        Важно:
        dashboard_widgets.py пока содержит собственные русские
        строки, поэтому здесь мы не вызываем set_language()
        у дочерних виджетов, если такого метода нет.
        """

        language = str(language or "ru").lower().strip()

        if language not in self.TRANSLATIONS:
            language = "ru"

        self.ui_language = language

        self._refresh_static_texts()

        if self._last_ai_result:
            self._apply_ai_result(
                self._last_ai_result,
                remember=False,
            )
        else:
            self.ai_hello.setText(
                self._tr("hello", username="Пользователь")
            )
            self.ai_description.setText(
                self._tr("ai_description")
            )
            self.ai_status.setText(
                self._tr("ai_check")
            )
            self.ai_recommendations.setText(
                self._tr("recommendations", count=0)
            )

    def _refresh_static_texts(self):
        if hasattr(self, "performance"):
            if hasattr(self.performance, "set_language"):
                try:
                    self.performance.set_language(self.ui_language)
                except Exception:
                    pass

        if hasattr(self, "resources"):
            if hasattr(self.resources, "set_language"):
                try:
                    self.resources.set_language(self.ui_language)
                except Exception:
                    pass

        if hasattr(self, "realtime"):
            if hasattr(self.realtime, "set_language"):
                try:
                    self.realtime.set_language(self.ui_language)
                except Exception:
                    pass

        if hasattr(self, "_system_header"):
            self._system_header.setText(
                self._tr("system_info")
            )

        if hasattr(self, "_details_label"):
            self._details_label.setText(
                self._tr("details")
            )

        if hasattr(self, "_quick_title"):
            self._quick_title.setText(
                self._tr("quick_actions")
            )

        if hasattr(self, "_quick_action_widgets"):
            action_keys = [
                ("quick_optimize", "quick_optimize_desc"),
                ("cleanup", "cleanup_desc"),
                ("startup", "startup_desc"),
                ("security", "security_desc"),
            ]

            for widget, (title_key, desc_key) in zip(
                self._quick_action_widgets,
                action_keys,
            ):
                if hasattr(widget, "_title_label"):
                    widget._title_label.setText(
                        self._tr(title_key)
                    )

                if hasattr(widget, "_subtitle_label"):
                    widget._subtitle_label.setText(
                        self._tr(desc_key)
                    )

        if hasattr(self, "ai_title"):
            self.ai_title.setText(
                self._tr("ai_title")
            )

        if hasattr(self, "ai_open_label"):
            self.ai_open_label.setText(
                self._tr("ai_open")
            )

        if hasattr(self, "ai_details"):
            self.ai_details.setText(
                self._tr("ai_details")
            )

        if hasattr(self, "ai_cleanup_button"):
            self.ai_cleanup_button.setText(
                self._tr("ai_cleanup")
            )

        if hasattr(self, "status_scan"):
            self.status_scan.setText(
                self._tr("last_scan")
            )

        if hasattr(self, "status_update"):
            self.status_update.setText(
                self._tr("updates")
            )

        if hasattr(self, "status_protect"):
            self.status_protect.setText(
                self._tr("protected")
            )

        self._refresh_system_info_labels()

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _label(self, text, size=9, color=TEXT, bold=False):
        label = QLabel(text)

        weight = 800 if bold else 400

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: {size}px;
                font-weight: {weight};
                background: transparent;
                border: none;
            }}
            """
        )

        return label

    # ==========================================================
    # MAIN UI
    # ==========================================================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.setColumnStretch(0, 5)
        grid.setColumnStretch(1, 4)

        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 0)

        self.performance = PerformanceGauge()
        self.performance.on_optimize = self._run_quick_optimization
        grid.addWidget(self.performance, 0, 0)

        self.resources = ResourceOverview()
        self.resources.on_more = self._open_monitoring
        grid.addWidget(self.resources, 0, 1)

        self.system_info = self._build_system_info()
        grid.addWidget(self.system_info, 1, 0)

        self.realtime = RealtimeGraph()
        grid.addWidget(self.realtime, 1, 1)

        self._quick_card = self._build_quick_actions()
        grid.addWidget(self._quick_card, 2, 0)

        self._ai_card = self._build_ai_panel()
        grid.addWidget(self._ai_card, 2, 1)

        root.addLayout(grid, 1)

        self.status_bar = self._build_status_bar()
        root.addWidget(self.status_bar)

        self._apply_responsive_layout()

    # ==========================================================
    # QUICK OPTIMIZATION
    # ==========================================================

    def _run_quick_optimization(self):
        """Запускает полноценную безопасную оптимизацию."""
        if self._closing or not self.main_window:
            return

        optimize_page = getattr(
            self.main_window,
            "optimize",
            None,
        )

        if (
            optimize_page is not None
            and hasattr(optimize_page, "quick_optimize")
        ):
            self.main_window.open_page(optimize_page)
            QTimer.singleShot(
                150,
                optimize_page.quick_optimize,
            )
        else:
            self._handle_action("quick_optimize")

    def _open_monitoring(self):
        """Открывает страницу подробного мониторинга."""
        if self._closing or not self.main_window:
            return

        page = getattr(
            self.main_window,
            "monitoring",
            None,
        )

        if page is not None:
            self.main_window.open_page(page)

    # ==========================================================
    # SYSTEM INFO
    # ==========================================================

    def _build_system_info(self):
        card = CardFrame()

        card.setMinimumHeight(185)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            18,
            14,
            18,
            12,
        )
        lay.setSpacing(6)

        self._system_header = self._label(
            self._tr("system_info"),
            12,
            TEXT,
            True,
        )

        lay.addWidget(self._system_header)

        content = QHBoxLayout()
        content.setSpacing(18)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(5)

        self.board = self._label(
            f"{self._tr('board')}:  —",
            9,
            MUTED,
        )

        self.bios = self._label(
            f"{self._tr('bios')}:  —",
            9,
            MUTED,
        )

        self.uptime = self._label(
            f"{self._tr('uptime')}:  —",
            9,
            MUTED,
        )

        self.arch = self._label(
            f"{self._tr('system')}:  —",
            9,
            MUTED,
        )

        self.launch = self._label(
            f"{self._tr('launch')}:  "
            f"{self._tr('launch_session')}",
            9,
            MUTED,
        )

        info_lay.addWidget(self.board)
        info_lay.addWidget(self.bios)
        info_lay.addWidget(self.uptime)
        info_lay.addWidget(self.arch)
        info_lay.addWidget(self.launch)

        self._details_label = self._label(
            self._tr("details"),
            9,
            "#168cff",
            True,
        )

        self._details_label.setCursor(
            Qt.PointingHandCursor
        )

        self._details_label.mousePressEvent = (
            lambda event: self._open_hardware_details()
        )

        info_lay.addWidget(self._details_label)
        info_lay.addStretch(1)

        content.addLayout(info_lay, 3)

        self._monitor_visual = QLabel()
        self._monitor_visual.setAlignment(Qt.AlignCenter)
        self._monitor_visual.setMinimumWidth(180)
        self._monitor_visual.setMaximumWidth(230)
        self._monitor_visual.setMinimumHeight(105)

        monitor_pixmap = QPixmap(
            "app/pages/system_monitor_dashboard.png"
        )

        self._monitor_visual.setPixmap(
            monitor_pixmap.scaled(
                220,
                120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        


        content.addWidget(self._monitor_visual, 2)

        lay.addLayout(content)

        return card
    def _refresh_system_info_labels(self):
        if not hasattr(self, "board"):
            return

        self.board.setText(
            self._tr("board") + ":  —"
        )

        self.bios.setText(
            self._tr("bios") + ":  —"
        )

        self.uptime.setText(
            self._tr("uptime") + ":  —"
        )

        self.arch.setText(
            self._tr("system") + ":  —"
        )

        self.launch.setText(
            self._tr("launch")
            + ":  "
            + self._tr("launch_session")
        )

        if self._system_info_loaded:
            self._update_system_info_text()

    def _update_system_info_text(self):
        system = self._system_info_cache or {}

        try:
            motherboard = self._motherboard_cache or {}

            manufacturer = motherboard.get(
                "manufacturer",
                self._tr("unknown"),
            )

            product = motherboard.get(
                "product",
                self._tr("unknown"),
            )

            if (
                manufacturer != self._tr("unknown")
                and product != self._tr("unknown")
            ):
                self.board.setText(
                    f"{self._tr('board')}:  "
                    f"{manufacturer} {product}"
                )
            else:
                self.board.setText(
                    f"{self._tr('board')}:  —"
                )

        except Exception:
            self.board.setText(
                f"{self._tr('board')}:  —"
            )

        try:
            bios = self._bios_cache or {}

            bios_manufacturer = bios.get(
                "manufacturer",
                self._tr("unknown"),
            )

            bios_version = bios.get(
                "version",
                self._tr("unknown"),
            )

            self.bios.setText(
                f"{self._tr('bios')}:  "
                f"{bios_manufacturer} {bios_version}"
            )

        except Exception:
            self.bios.setText(
                f"{self._tr('bios')}:  —"
            )

        try:
            boot = time.time() - psutil.boot_time()

            days = int(boot // 86400)
            hours = int((boot % 86400) // 3600)
            mins = int((boot % 3600) // 60)

            self.uptime.setText(
                f"{self._tr('uptime')}:  "
                f"{days} {self._tr('day')} "
                f"{hours} {self._tr('hour')} "
                f"{mins} {self._tr('minute')}"
            )

        except Exception:
            self.uptime.setText(
                f"{self._tr('uptime')}:  —"
            )

        self.arch.setText(
            f"{self._tr('system')}:  "
            f"{system.get('machine', '—')} / "
            f"{system.get('system', '—')} "
            f"{system.get('release', '')}"
        )

        self.launch.setText(
            f"{self._tr('launch')}:  "
            f"{self._tr('launch_session')}"
        )

    def _open_hardware_details(self):
        if self._closing or not self.main_window:
            return

        page = getattr(
            self.main_window,
            "hardware",
            None,
        )

        if page is not None:
            self.main_window.open_page(page)

    # ==========================================================
    # QUICK ACTIONS
    # ==========================================================

    def _action(
        self,
        action_id,
        title,
        subtitle,
        color,
    ):
        frame = QFrame()

        frame.setCursor(
            Qt.PointingHandCursor
        )

        frame.setStyleSheet(
            f"""
            QFrame#DashboardQuickAction {{
                background: #0a1730;
                border: 1px solid {color};
                border-radius: 10px;
            }}

            QFrame#DashboardQuickAction:hover {{
                background: #10233f;
            }}
            """
        )

        frame.setObjectName(
            "DashboardQuickAction"
        )

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(
            10,
            7,
            10,
            7,
        )
        lay.setSpacing(3)

        icon = QLabel("◆")
        icon.setAlignment(
            Qt.AlignCenter
        )
        icon.setStyleSheet(
            f"""
            color: {color};
            font-size: 20px;
            background: transparent;
            border: none;
            """
        )

        title_label = self._label(
            title,
            10,
            TEXT,
            True,
        )
        title_label.setAlignment(
            Qt.AlignCenter
        )

        subtitle_label = self._label(
            subtitle,
            8,
            MUTED,
        )
        subtitle_label.setAlignment(
            Qt.AlignCenter
        )
        subtitle_label.setWordWrap(True)

        frame._action_id = action_id
        frame._title_label = title_label
        frame._subtitle_label = subtitle_label

        lay.addWidget(icon)
        lay.addWidget(title_label)
        lay.addWidget(subtitle_label)

        frame.mousePressEvent = (
            lambda event, aid=action_id:
            self._handle_action(aid)
        )

        return frame      



    def _build_quick_actions(self):
        card = CardFrame()

        card.setMinimumHeight(125)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            14,
            10,
            14,
            10,
        )
        lay.setSpacing(7)

        self._quick_title = self._label(
            self._tr("quick_actions"),
            16,
            TEXT,
            True,
        )

        lay.addWidget(
            self._quick_title
        )

        row = QHBoxLayout()
        row.setSpacing(7)

        actions = [
            (
                "quick_optimize",
                self._tr("quick_optimize"),
                self._tr("quick_optimize_desc"),
                "#168cff",
            ),
            (
                "cleanup",
                self._tr("cleanup"),
                self._tr("cleanup_desc"),
                "#18d47b",
            ),
            (
                "startup",
                self._tr("startup"),
                self._tr("startup_desc"),
                "#8e4cff",
            ),
            (
                "security",
                self._tr("security"),
                self._tr("security_desc"),
                "#ff9f43",
            ),
        ]

        self._quick_action_widgets = []

        for action in actions:
            widget = self._action(*action)

            self._quick_action_widgets.append(
                widget
            )

            row.addWidget(
                widget,
                1,
            )

        lay.addLayout(row)

        return card

    def _handle_action(self, action_id):
        print(
            f"[Dashboard] Quick action clicked: "
            f"{action_id}"
        )

        if self._closing:
            return

        if not self.main_window:
            print(
                "[Dashboard] "
                "MainWindow reference is missing"
            )
            return

        if action_id == "quick_optimize":
            optimize_page = getattr(
                self.main_window,
                "optimize",
                None,
            )

            if optimize_page is not None:
                self.main_window.open_page(
                    optimize_page
                )

        elif action_id == "cleanup":
            tools = getattr(
                self.main_window,
                "tools",
                None,
            )

            if tools is not None and hasattr(
                tools,
                "_cleanup",
            ):
                tools._cleanup()

        elif action_id == "startup":
            tools = getattr(
                self.main_window,
                "tools",
                None,
            )

            if tools is not None and hasattr(
                tools,
                "_startup",
            ):
                tools._startup()

        elif action_id == "security":
            tools = getattr(
                self.main_window,
                "tools",
                None,
            )

            if tools is not None and hasattr(
                tools,
                "_security",
            ):
                tools._security()

    # ==========================================================
    # AI PANEL
    # ==========================================================

    def _build_ai_panel(self):
        card = CardFrame()

        self.ai_card = card

        card.setMinimumHeight(125)
        card.setMaximumHeight(190)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            14,
            9,
            14,
            9,
        )
        lay.setSpacing(6)

        # ==================================================
        # HEADER
        # ==================================================
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)

        self.ai_title = self._label(
            self._tr("ai_title"),
            15,
            TEXT,
            True,
        )

        head.addWidget(self.ai_title)
        head.addStretch()

        self.ai_open_label = self._label(
            self._tr("ai_open"),
            9,
            "#168cff",
            True,
        )

        head.addWidget(
            self.ai_open_label
        )

        lay.addLayout(head)

        # ==================================================
        # AI STATUS AREA
        # ==================================================
        bubble = QFrame()

        self.ai_bubble = bubble

        bubble.setStyleSheet(
            """
            QFrame {
                background: #0b172a;
                border: 1px solid #1d3152;
                border-radius: 10px;
            }
            """
        )

        bl = QVBoxLayout(bubble)

        bl.setContentsMargins(
            11,
            7,
            11,
            7,
        )

        bl.setSpacing(2)

        self.ai_hello = self._label(
            self._tr(
                "hello",
                username="Пользователь",
            ),
            11,
            TEXT,
            True,
        )

        bl.addWidget(
            self.ai_hello
        )

        self.ai_description = self._label(
            self._tr("ai_description"),
            8,
            MUTED,
        )

        self.ai_description.setWordWrap(
            True
        )

        bl.addWidget(
            self.ai_description
        )

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 1, 0, 0)

        self.ai_status = self._label(
            self._tr("ai_check"),
            8,
            "#18d47b",
            True,
        )

        status_row.addWidget(
            self.ai_status
        )

        status_row.addStretch()

        self.ai_recommendations = self._label(
            self._tr(
                "recommendations",
                count=0,
            ),
            8,
            MUTED,
            True,
        )

        self.ai_recommendations.setWordWrap(
            True
        )

        status_row.addWidget(
            self.ai_recommendations
        )

        bl.addLayout(
            status_row
        )

        lay.addWidget(
            bubble,
            1,
        )

        # ==================================================
        # ACTION BUTTONS
        # ==================================================
        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(7)

        self.ai_details = QPushButton(
            self._tr("ai_details")
        )

        self.ai_details.setCursor(
            Qt.PointingHandCursor
        )

        self.ai_details.setMinimumHeight(
            28
        )

        self.ai_details.setStyleSheet(
            """
            QPushButton {
                color: white;
                background: #2548ff;
                border: 1px solid #7c36ff;
                border-radius: 8px;
                padding: 5px 8px;
                font-size: 9px;
                font-weight: 800;
            }

            QPushButton:hover {
                background: #3158ff;
            }

            QPushButton:pressed {
                background: #1d3fe0;
            }
            """
        )

        self.ai_details.clicked.connect(
            self.update_ai_panel
        )

        buttons.addWidget(
            self.ai_details,
            1,
        )

        self.ai_cleanup_button = QPushButton(
            self._tr("ai_cleanup")
        )

        self.ai_cleanup_button.setCursor(
            Qt.PointingHandCursor
        )

        self.ai_cleanup_button.setMinimumHeight(
            28
        )

        self.ai_cleanup_button.setStyleSheet(
            """
            QPushButton {
                color: white;
                background: #126b4a;
                border: 1px solid #18d47b;
                border-radius: 8px;
                padding: 5px 8px;
                font-size: 9px;
                font-weight: 800;
            }

            QPushButton:hover {
                background: #16845a;
            }

            QPushButton:pressed {
                background: #0d563b;
            }

            QPushButton:disabled {
                color: #718096;
                background: #172235;
                border: 1px solid #263750;
            }
            """
        )

        self.ai_cleanup_button.clicked.connect(
            self._scan_cleanup
        )

        buttons.addWidget(
            self.ai_cleanup_button,
            1,
        )

        lay.addLayout(
            buttons
        )

        return card

    # ==========================================================
    # THEME
    # ==========================================================

    def set_theme(self, light: bool):
        """Apply selected theme to the Dashboard AI panel."""

        if not hasattr(
            self,
            "ai_card",
        ):
            return

        if light:
            card_bg = "#ffffff"
            border = "#d6e0ea"
            bubble_bg = "#f8fafc"
            text = "#172033"
            muted = "#64748b"

            self.ai_card.setStyleSheet(
                f"""
                QFrame#CardFrame {{
                    background:{card_bg};
                    border:1px solid {border};
                    border-radius:14px;
                }}
                """
            )

            self.ai_bubble.setStyleSheet(
                f"""
                QFrame {{
                    background:{bubble_bg};
                    border:1px solid {border};
                    border-radius:9px;
                }}
                """
            )

            self.ai_open_label.setStyleSheet(
                """
                color:#168cff;
                font-size:9px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_hello.setStyleSheet(
                f"""
                color:{text};
                font-size:11px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_description.setStyleSheet(
                f"""
                color:{muted};
                font-size:8px;
                font-weight:400;
                background:transparent;
                border:none;
                """
            )

            self.ai_status.setStyleSheet(
                """
                color:#16a34a;
                font-size:8px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_recommendations.setStyleSheet(
                f"""
                color:{muted};
                font-size:8px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_details.setStyleSheet(
                """
                QPushButton {
                    color:white;
                    background:#168cff;
                    border:1px solid #168cff;
                    border-radius:8px;
                    padding:6px;
                    font-size:9px;
                    font-weight:800;
                }

                QPushButton:hover {
                    background:#2698ff;
                    border-color:#2698ff;
                    color:white;
                }

                QPushButton:pressed {
                    background:#0f75d5;
                    border-color:#0f75d5;
                    color:white;
                }
                """
            )

            self.ai_cleanup_button.setStyleSheet(
                """
                QPushButton {
                    color:white;
                    background:#16a34a;
                    border:1px solid #16a34a;
                    border-radius:8px;
                    padding:6px;
                    font-size:9px;
                    font-weight:800;
                }

                QPushButton:hover {
                    background:#22b65a;
                    border-color:#22b65a;
                    color:white;
                }

                QPushButton:pressed {
                    background:#15803d;
                    border-color:#15803d;
                    color:white;
                }

                QPushButton:disabled {
                    color:#64748b;
                    background:#e2e8f0;
                    border:1px solid #cbd5e1;
                }
                """
            )

        else:
            self.ai_card.setStyleSheet(
                """
                QFrame#CardFrame {
                    background:#0a1428;
                    border:1px solid #1d3152;
                    border-radius:14px;
                }
                """
            )

            self.ai_bubble.setStyleSheet(
                """
                QFrame {
                    background:#111d32;
                    border:1px solid #1d3152;
                    border-radius:9px;
                }
                """
            )

            self.ai_open_label.setStyleSheet(
                """
                color:#168cff;
                font-size:9px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_hello.setStyleSheet(
                """
                color:#f4f7ff;
                font-size:11px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_description.setStyleSheet(
                """
                color:#8ea3bd;
                font-size:8px;
                font-weight:400;
                background:transparent;
                border:none;
                """
            )

            self.ai_status.setStyleSheet(
                """
                color:#18d47b;
                font-size:8px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_recommendations.setStyleSheet(
                """
                color:#8ea3bd;
                font-size:8px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            self.ai_details.setStyleSheet(
                """
                QPushButton {
                    color:white;
                    background:#2548ff;
                    border:1px solid #7c36ff;
                    border-radius:8px;
                    padding:6px;
                    font-size:9px;
                    font-weight:800;
                }

                QPushButton:hover {
                    background:#3158ff;
                }

                QPushButton:pressed {
                    background:#1d3fe0;
                }
                """
            )

            self.ai_cleanup_button.setStyleSheet(
                """
                QPushButton {
                    color:white;
                    background:#126b4a;
                    border:1px solid #18d47b;
                    border-radius:8px;
                    padding:6px;
                    font-size:9px;
                    font-weight:800;
                }

                QPushButton:hover {
                    background:#16845a;
                }

                QPushButton:pressed {
                    background:#0d563b;
                }

                QPushButton:disabled {
                    color:#718096;
                    background:#172235;
                    border:1px solid #263750;
                }
                """
            )
                    # Apply theme to Dashboard widgets
        if hasattr(self, "performance") and hasattr(self.performance, "set_theme"):
            self.performance.set_theme(light)

        if hasattr(self, "resources") and hasattr(self.resources, "set_theme"):
            self.resources.set_theme(light)

        if hasattr(self, "realtime") and hasattr(self.realtime, "set_theme"):
            self.realtime.set_theme(light)

    # ==========================================================
    # AI ANALYSIS
    # ==========================================================

    def update_ai_panel(self):
        if self._closing:
            return

        if self.ai_worker is not None:
            if self.ai_worker.isRunning():
                print(
                    "[Dashboard] "
                    "AI worker already running"
                )
                return

            self.ai_worker = None

        self.ai_status.setText(
            self._tr("ai_analyzing")
        )

        self.ai_description.setText(
            self._tr("ai_checking")
        )
        # ?????????????? ???? AI ? ?????? Dashboard
        try:
            self.ai_analyzer.set_language(self.ui_language)
            print(
                "[Dashboard] AI language synchronized:",
                self.ui_language
            )
        except Exception as exc:
            print(
                "[Dashboard] AI language sync error:",
                exc
            )

        worker = AIWorker(
            self.ai_analyzer,
            self,
        )

        self.ai_worker = worker

        worker.result_ready.connect(
            self._apply_ai_result
        )

        worker.error.connect(
            self._handle_ai_error
        )

        worker.finished.connect(
            self._ai_worker_finished
        )

        print(
            "[Dashboard] Starting AI analysis..."
        )

        worker.start()

    def _ai_worker_finished(self):
        worker = self.sender()

        print(
            "[Dashboard] AI worker finished"
        )

        if worker is self.ai_worker:
            self.ai_worker = None

        if worker is not None:
            worker.deleteLater()

    def _apply_ai_result(
        self,
        result,
        remember=True,
    ):
        if self._closing:
            return

        try:
            if not result:
                return

            if remember:
                self._last_ai_result = result

            username = (
                result.get(
                    "username",
                    "Пользователь",
                )
                or "Пользователь"
            )

            status = result.get(
                "status",
                "good",
            )

            recommendations = result.get(
                "recommendations",
                [],
            )

            if not isinstance(
                recommendations,
                list,
            ):
                recommendations = []

            data = result.get(
                "data",
                {},
            )

            if not isinstance(
                data,
                dict,
            ):
                data = {}

            cpu_data = data.get(
                "cpu",
                {},
            )

            ram_data = data.get(
                "ram",
                {},
            )

            disk_data = data.get(
                "disk",
                {},
            )

            try:
                cpu = float(
                    cpu_data.get(
                        "usage",
                        0,
                    )
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                cpu = 0.0

            try:
                ram = float(
                    ram_data.get(
                        "usage",
                        0,
                    )
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                ram = 0.0

            try:
                disk = float(
                    disk_data.get(
                        "usage",
                        0,
                    )
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                disk = 0.0

            self.ai_hello.setText(
                self._tr(
                    "hello",
                    username=username,
                )
            )

            message = result.get(
                "message",
                self._tr("ai_analyzed"),
            )

            if not isinstance(
                message,
                str,
            ):
                message = str(message)

            # Перевод стандартных сообщений AI
            message_translations = {
                "Система работает стабильно":
                    self._tr("ai_good"),
                "Система работает\nстабильно":
                    self._tr("ai_good"),
                "Я проанализировал состояние вашей системы.":
                    self._tr("ai_analyzed"),
                "Я проанализировал состояние системы.":
                    self._tr("ai_analyzed"),
            }

            message = message_translations.get(
                message,
                message,
            )

            message += (
                "\n\n"
                f"{self._tr('cpu')}: {cpu:.0f}%  •  "
                f"{self._tr('ram')}: {ram:.0f}%  •  "
                f"{self._tr('disk')}: {disk:.0f}%"
            )

            self.ai_description.setText(
                message
            )

            status_text = {
                "good": self._tr(
                    "ai_good"
                ),
                "attention": self._tr(
                    "ai_attention"
                ),
                "critical": self._tr(
                    "ai_critical"
                ),
            }.get(
                status,
                self._tr("ai_unknown"),
            )

            self.ai_status.setText(
                status_text
            )

            if recommendations:
                text = ""

                for item in recommendations:
                    if isinstance(
                        item,
                        dict,
                    ):
                        title = item.get(
                            "title",
                            self._tr(
                                "recommendation"
                            ),
                        )

                        rec_message = item.get(
                            "message",
                            "",
                        )

                        text += (
                            f"• {title}\n"
                            f"  {rec_message}\n"
                        )

                    else:
                        text += (
                            f"• {item}\n"
                        )

                self.ai_recommendations.setText(
                    text
                )

            else:
                self.ai_recommendations.setText(
                    self._tr(
                        "no_problems"
                    )
                )

            print(
                "[AI] "
                f"{username} | status={status} | "
                f"CPU={cpu:.1f}% | "
                f"RAM={ram:.1f}% | "
                f"DISK={disk:.1f}%"
            )

        except Exception as exc:
            print(
                "[Dashboard] "
                f"AI result error: {exc}"
            )

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def _scan_cleanup(self):
        if self._closing:
            return

        try:
            result = scan_temp_files()

            files = int(
                result.get(
                    "files",
                    0,
                )
                or 0
            )

            folders = int(
                result.get(
                    "folders",
                    0,
                )
                or 0
            )

            megabytes = float(
                result.get(
                    "megabytes",
                    0,
                )
                or 0
            )

            print(
                "[Dashboard] Cleanup result:"
                f" files={files}"
                f" folders={folders}"
                f" size_mb={megabytes:.1f}"
            )

            if megabytes > 0:
                self.ai_recommendations.setText(
                    self._tr(
                        "temp_found",
                        megabytes=megabytes,
                    )
                )

                self.ai_cleanup_button.setText(
                    self._tr(
                        "delete_found"
                    )
                )

                self.ai_cleanup_button.setEnabled(
                    True
                )

                self.ai_cleanup_button.show()

                try:
                    self.ai_cleanup_button.clicked.disconnect()
                except (
                    TypeError,
                    RuntimeError,
                ):
                    pass

                self.ai_cleanup_button.clicked.connect(
                    self._confirm_cleanup_delete
                )

            else:
                self.ai_recommendations.setText(
                    self._tr(
                        "temp_not_found"
                    )
                )

                self.ai_cleanup_button.hide()

        except Exception as exc:
            self._cleanup_error(
                str(exc)
            )

    def _confirm_cleanup_delete(self):
        if self._closing:
            return

        box = QMessageBox(self)

        box.setWindowTitle(
            self._tr("cleanup_title")
        )

        box.setText(
            self._tr("cleanup_question")
        )

        box.setInformativeText(
            self._tr("cleanup_info")
        )

        box.setStandardButtons(
            QMessageBox.Yes
            | QMessageBox.No
        )

        box.setDefaultButton(
            QMessageBox.No
        )

        if (
            box.exec()
            != QMessageBox.Yes
        ):
            return

        self._delete_cleanup()

    def _delete_cleanup(self):
        if self._closing:
            return

        self.ai_cleanup_button.setEnabled(
            False
        )

        self.ai_cleanup_button.setText(
            self._tr("deleting")
        )

        try:
            result = delete_temp_files(
                dry_run=False
            )

            deleted_files = int(
                result.get(
                    "deleted_files",
                    0,
                )
                or 0
            )

            deleted_folders = int(
                result.get(
                    "deleted_folders",
                    0,
                )
                or 0
            )

            deleted_megabytes = float(
                result.get(
                    "deleted_megabytes",
                    0,
                )
                or 0
            )

            skipped = int(
                result.get(
                    "skipped",
                    0,
                )
                or 0
            )

            errors = int(
                result.get(
                    "errors",
                    0,
                )
                or 0
            )

            self.ai_status.setText(
                self._tr(
                    "cleanup_done"
                )
            )

            self.ai_recommendations.setText(
                self._tr(
                    "deleted",
                    files=deleted_files,
                    megabytes=deleted_megabytes,
                    folders=deleted_folders,
                    skipped=skipped,
                    errors=errors,
                )
            )

            self.ai_cleanup_button.setText(
                self._tr(
                    "check_again"
                )
            )

            self.ai_cleanup_button.setEnabled(
                True
            )

            self.ai_cleanup_button.show()

            try:
                self.ai_cleanup_button.clicked.disconnect()
            except (
                TypeError,
                RuntimeError,
            ):
                pass

            self.ai_cleanup_button.clicked.connect(
                self._scan_cleanup
            )

        except Exception as exc:
            self._cleanup_error(
                str(exc)
            )

    def _cleanup_error(self, error):
        print(
            f"[Dashboard] Cleanup error: {error}"
        )

        self.ai_status.setText(
            self._tr(
                "cleanup_error"
            )
        )

        self.ai_recommendations.setText(
            self._tr(
                "cleanup_error_text",
                error=error,
            )
        )

        self.ai_cleanup_button.setText(
            self._tr("retry")
        )

        self.ai_cleanup_button.setEnabled(
            True
        )

        self.ai_cleanup_button.show()

        try:
            self.ai_cleanup_button.clicked.disconnect()
        except (
            TypeError,
            RuntimeError,
        ):
            pass

        self.ai_cleanup_button.clicked.connect(
            self._scan_cleanup
        )

    # ==========================================================
    # AI ERROR
    # ==========================================================

    def _handle_ai_error(self, error):
        if self._closing:
            return

        try:
            self.ai_hello.setText(
                self._tr("ai_title")
            )

            self.ai_description.setText(
                self._tr("ai_error")
            )

            self.ai_status.setText(
                self._tr(
                    "ai_error_status"
                )
            )

            self.ai_recommendations.setText(
                str(error)
            )

            print(
                f"[Dashboard] AI error: {error}"
            )

        except Exception as exc:
            print(
                "[Dashboard] "
                f"AI error handler failed: {exc}"
            )

    # ==========================================================
    # STATUS BAR
    # ==========================================================

    def _build_status_bar(self):
        card = QFrame()

        if (
            hasattr(
                self,
                "main_window",
            )
            and getattr(
                self.main_window,
                "_light_theme",
                False,
            )
        ):
            status_bg = "#ffffff"
            status_border = "#d6e0ea"
        else:
            status_bg = "#091528"
            status_border = "#162945"

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {status_bg};
                border: 1px solid {status_border};
                border-radius: 10px;
            }}
            """
        )

        lay = QHBoxLayout(card)

        lay.setContentsMargins(
            16,
            7,
            16,
            7,
        )

        self.status_scan = self._label(
            self._tr("last_scan"),
            9,
            MUTED,
        )

        self.status_update = self._label(
            self._tr("updates"),
            9,
            MUTED,
        )

        self.status_protect = self._label(
            self._tr("protected"),
            9,
            "#18d47b",
            True,
        )

        lay.addWidget(
            self.status_scan
        )

        lay.addStretch()

        lay.addWidget(
            self.status_update
        )

        lay.addSpacing(20)

        lay.addWidget(
            self.status_protect
        )

        return card

    # ==========================================================
    # RESPONSIVE
    # ==========================================================

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        width = self.width()
        height = self.height()

        compact = (
            width < 1120
            or height < 700
        )

        very_compact = (
            width < 1000
            or height < 640
        )

        if hasattr(
            self,
            "performance",
        ):
            if very_compact:
                gauge_size = 108
            elif compact:
                gauge_size = 120
            else:
                gauge_size = 135

            self.performance.gauge.setMinimumSize(
                gauge_size,
                gauge_size,
            )

            self.performance.optimize.setMinimumHeight(
                34 if compact else 40
            )

        if hasattr(
            self,
            "resources",
        ):
            if very_compact:
                resource_size = 62
            elif compact:
                resource_size = 72
            else:
                resource_size = 82

            for gauge in self.resources.gauges.values():
                gauge.setMinimumSize(
                    resource_size,
                    86 if compact else 96,
                )

        if hasattr(
            self,
            "system_info",
        ):
            self.system_info.setMinimumHeight(
                175
                if very_compact
                else 190
                if compact
                else 205
            )

        if hasattr(
            self,
            "realtime",
        ):
            self.realtime.setMinimumHeight(
                210
                if very_compact
                else 235
                if compact
                else 255
            )

        if hasattr(
            self,
            "_quick_card",
        ):
            self._quick_card.setMinimumHeight(
                125
                if very_compact
                else 135
                if compact
                else 145
            )

        if hasattr(
            self,
            "_ai_card",
        ):
            self._ai_card.setMinimumHeight(
                125
            )

            self._ai_card.setMaximumHeight(
                175
                if very_compact
                else 185
                if compact
                else 190
            )

    # ==========================================================
    # STATIC SYSTEM INFO
    # ==========================================================

    def _load_static_system_info(self):
        if self._closing:
            return

        try:
            print(
                "[Dashboard] "
                "Loading static system information..."
            )

            self._system_info_cache = (
                get_system_info()
                or {}
            )

            self._motherboard_cache = (
                get_motherboard_info()
                or {}
            )

            self._bios_cache = (
                get_bios_info()
                or {}
            )

            self._system_info_loaded = True

            self._update_system_info_text()

            print(
                "[Dashboard] "
                "Static system information loaded"
            )

        except Exception as exc:
            print(
                "[Dashboard] "
                f"Static system info error: {exc}"
            )

    # ==========================================================
    # DASHBOARD UPDATE
    # ==========================================================

    def update_dashboard(self):
        if self._closing:
            return

        try:
            cpu = float(
                psutil.cpu_percent(
                    interval=None
                )
            )

            mem = psutil.virtual_memory()

            ram_percent = float(
                mem.percent
            )

            ram_used = (
                float(mem.used)
                / (1024 ** 3)
            )

            ram_total = (
                float(mem.total)
                / (1024 ** 3)
            )

            try:
                system_drive = os.environ.get(
                    "SystemDrive",
                    "C:",
                )

                disk = psutil.disk_usage(
                    system_drive
                ).percent

            except Exception:
                disk = 0.0

            gpu = (
                get_cached_gpu_info()
                or {}
            )

            gpu_usage = gpu.get(
                "usage"
            )

            try:
                if gpu_usage is not None:
                    gpu_usage = float(
                        gpu_usage
                    )

            except (
                TypeError,
                ValueError,
            ):
                gpu_usage = None

            if gpu_usage is not None:
                gpu_usage = max(
                    0.0,
                    min(
                        100.0,
                        gpu_usage,
                    ),
                )

            load_components = [
                cpu,
                ram_percent,
            ]

            if gpu_usage is not None:
                load_components.append(
                    gpu_usage
                )

            average_load = (
                sum(load_components)
                / len(load_components)
                if load_components
                else 0.0
            )

            performance = max(
                0.0,
                min(
                    100.0,
                    100.0 - average_load,
                ),
            )

            self.performance.setValue(
                performance
            )

            subtitles = {
                "CPU": "",
                "GPU": (
                    f"{gpu_usage:.1f}%"
                    if gpu_usage is not None
                    else "—"
                ),
                "RAM": (
                    f"{ram_used:.1f} / "
                    f"{ram_total:.1f} GB"
                ),
                "Диск": "",
            }

            self.resources.set_values(
                cpu,
                gpu_usage,
                ram_percent,
                disk,
                subtitles,
            )

            self.realtime.add(
                {
                    "CPU": cpu,
                    "GPU": gpu_usage,
                    "RAM": ram_percent,
                    "Диск": disk,
                }
            )

            self.cpu_history.append(
                cpu
            )

            self.ram_history.append(
                ram_percent
            )

            if gpu_usage is not None:
                self.gpu_history.append(
                    gpu_usage
                )

            self.disk_history.append(
                disk
            )

            self._update_system_info_text()

            self.status_scan.setText(
                f"•  "
                f"{self._tr('today')}, "
                f"{time.strftime('%H:%M:%S')}"
            )

        except Exception as exc:
            print(
                "[Dashboard] "
                f"Monitoring error: {exc}"
            )

            if hasattr(
                self,
                "status_scan",
            ):
                self.status_scan.setText(
                    self._tr(
                        "monitor_error",
                        error=exc,
                    )
                )

    # ==========================================================
    # SHUTDOWN
    # ==========================================================

    def shutdown(self):
        if self._closing:
            print(
                "[Dashboard] "
                "Shutdown already in progress"
            )
            return

        print(
            "[Dashboard] Shutdown started"
        )

        self._closing = True

        try:
            if (
                hasattr(
                    self,
                    "timer",
                )
                and self.timer is not None
            ):
                self.timer.stop()

        except Exception as exc:
            print(
                "[Dashboard] "
                f"Timer shutdown error: {exc}"
            )

        try:
            if (
                hasattr(
                    self,
                    "ai_timer",
                )
                and self.ai_timer is not None
            ):
                self.ai_timer.stop()

        except Exception as exc:
            print(
                "[Dashboard] "
                f"AI timer shutdown error: {exc}"
            )

        try:
            worker = self.ai_worker

            if worker is not None:

                if worker.isRunning():
                    print(
                        "[Dashboard] "
                        "Waiting for AI worker..."
                    )

                    worker.stop(
                        timeout=15000
                    )

                if not worker.isRunning():
                    print(
                        "[Dashboard] "
                        "AI worker finished"
                    )

                    self.ai_worker = None

                    worker.deleteLater()

                else:
                    print(
                        "[Dashboard] WARNING: "
                        "AI worker is still running"
                    )

        except Exception as exc:
            print(
                "[Dashboard] "
                f"AI worker shutdown error: {exc}"
            )

        print(
            "[Dashboard] Shutdown complete"
        )

    def closeEvent(self, event):
        try:
            self.shutdown()

        except Exception as exc:
            print(
                "[Dashboard] "
                f"Close error: {exc}"
            )

        event.accept()


