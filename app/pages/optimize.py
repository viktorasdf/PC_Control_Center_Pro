# -*- coding: utf-8 -*-

import psutil

from PySide6.QtCore import QTimer, Qt
from app.services.cleanup_worker import CleanupWorker
from app.services.startup_service import scan_startup

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QProgressBar,
    QMessageBox,
)


class OptimizePage(QWidget):

    SUPPORTED_LANGUAGES = ("ru", "uk", "en", "de", "it", "es", "fr")

    TRANSLATIONS = {
        "ru": {
            "title": "Оптимизация",
            "subtitle": "Анализ состояния системы и безопасная оптимизация",
            "system_status": "⚡ Состояние системы",
            "analysis": "🔍 Анализ",
            "checking": "Проверка системы...",
            "temp_check": "Временные файлы: проверка...\nАвтозагрузка: проверка...",
            "actions": "🛠 Оптимизация",
            "actions_info": "Доступные операции будут выполняться только после подтверждения.",
            "refresh": "↻  Обновить анализ",
            "optimize": "⚡  Быстрая оптимизация",
            "normal": "✓ Система работает нормально.\n\nКритических проблем, требующих немедленной оптимизации, не обнаружено.",
            "high_cpu": "Высокая нагрузка CPU",
            "high_ram": "Высокое использование RAM",
            "low_disk": "На диске мало свободного места",
            "problems": "⚠ Обнаружены потенциальные проблемы:",
            "scan_temp": "Временные файлы: сканирование...\nАвтозагрузка: сканирование...",
            "refresh_scanning": "⌛  Сканирование...",
            "temp_result": "Временные файлы: {files:,} шт. • {mb:.1f} МБ\nАвтозагрузка: {startup} активных элементов",
            "disabled": " • {count} отключено",
            "safe_cleanup": "\n\n• Можно безопасно очистить временные файлы: около {mb:.1f} МБ.",
            "cleanup_done": "✓ Безопасная очистка завершена.\n\nУдалено временных файлов: {files:,}.\nОсвобождено: {mb:.1f} МБ.",
            "skipped": "\nПропущено занятых/недоступных: {count}.",
            "cleanup_error": "⚠ Не удалось выполнить операцию очистки:\n{message}",
            "analysis_error": "Ошибка анализа системы:\n{error}",
            "no_files_title": "Оптимизация",
            "no_files": "Временных файлов для безопасного удаления не найдено.\n\nАвтозагрузка и системные настройки автоматически не изменяются.",
            "confirm_title": "Подтверждение оптимизации",
            "confirm_text": "Будет выполнена только безопасная очистка временных файлов.\n\nНайдено: {files:,} файлов\nРазмер: около {mb:.1f} МБ\n\nПрограммы автозагрузки, службы и настройки Windows автоматически изменяться не будут.\n\nПродолжить?",
            "cleanup_running": "Очистка временных файлов выполняется...\n\nЗанятые и недоступные файлы будут пропущены.",
        },
        "uk": {
            "title": "Оптимізація",
            "subtitle": "Аналіз стану системи та безпечна оптимізація",
            "system_status": "⚡ Стан системи",
            "analysis": "🔍 Аналіз",
            "checking": "Перевірка системи...",
            "temp_check": "Тимчасові файли: перевірка...\nАвтозавантаження: перевірка...",
            "actions": "🛠 Оптимізація",
            "actions_info": "Доступні операції виконуватимуться лише після підтвердження.",
            "refresh": "↻  Оновити аналіз",
            "optimize": "⚡  Швидка оптимізація",
            "normal": "✓ Система працює нормально.\n\nКритичних проблем, що потребують негайної оптимізації, не виявлено.",
            "high_cpu": "Високе навантаження CPU",
            "high_ram": "Високе використання RAM",
            "low_disk": "На диску мало вільного місця",
            "problems": "⚠ Виявлено потенційні проблеми:",
            "scan_temp": "Тимчасові файли: сканування...\nАвтозавантаження: сканування...",
            "refresh_scanning": "⌛  Сканування...",
            "temp_result": "Тимчасові файли: {files:,} шт. • {mb:.1f} МБ\nАвтозавантаження: {startup} активних елементів",
            "disabled": " • {count} вимкнено",
            "safe_cleanup": "\n\n• Можна безпечно очистити тимчасові файли: близько {mb:.1f} МБ.",
            "cleanup_done": "✓ Безпечне очищення завершено.\n\nВидалено тимчасових файлів: {files:,}.\nЗвільнено: {mb:.1f} МБ.",
            "skipped": "\nПропущено зайнятих/недоступних: {count}.",
            "cleanup_error": "⚠ Не вдалося виконати операцію очищення:\n{message}",
            "analysis_error": "Помилка аналізу системи:\n{error}",
            "no_files_title": "Оптимізація",
            "no_files": "Тимчасових файлів для безпечного видалення не знайдено.\n\nАвтозавантаження та системні налаштування автоматично не змінюються.",
            "confirm_title": "Підтвердження оптимізації",
            "confirm_text": "Буде виконано лише безпечне очищення тимчасових файлів.\n\nЗнайдено: {files:,} файлів\nРозмір: близько {mb:.1f} МБ\n\nПрограми автозавантаження, служби та налаштування Windows автоматично змінюватися не будуть.\n\nПродовжити?",
            "cleanup_running": "Виконується очищення тимчасових файлів...\n\nЗайняті та недоступні файли буде пропущено.",
        },
        "en": {
            "title": "Optimization",
            "subtitle": "Analyze system status and perform safe optimization",
            "system_status": "⚡ System status",
            "analysis": "🔍 Analysis",
            "checking": "Checking system...",
            "temp_check": "Temporary files: checking...\nStartup: checking...",
            "actions": "🛠 Optimization",
            "actions_info": "Available operations will be performed only after confirmation.",
            "refresh": "↻  Refresh analysis",
            "optimize": "⚡  Quick optimization",
            "normal": "✓ The system is operating normally.\n\nNo critical issues requiring immediate optimization were detected.",
            "high_cpu": "High CPU load",
            "high_ram": "High RAM usage",
            "low_disk": "Low free disk space",
            "problems": "⚠ Potential problems detected:",
            "scan_temp": "Temporary files: scanning...\nStartup: scanning...",
            "refresh_scanning": "⌛  Scanning...",
            "temp_result": "Temporary files: {files:,} • {mb:.1f} MB\nStartup: {startup} active items",
            "disabled": " • {count} disabled",
            "safe_cleanup": "\n\n• Temporary files can be safely cleaned: about {mb:.1f} MB.",
            "cleanup_done": "✓ Safe cleanup completed.\n\nTemporary files deleted: {files:,}.\nFreed: {mb:.1f} MB.",
            "skipped": "\nSkipped busy/inaccessible files: {count}.",
            "cleanup_error": "⚠ Cleanup operation failed:\n{message}",
            "analysis_error": "System analysis error:\n{error}",
            "no_files_title": "Optimization",
            "no_files": "No temporary files were found for safe deletion.\n\nStartup programs and system settings will not be changed automatically.",
            "confirm_title": "Optimization confirmation",
            "confirm_text": "Only safe temporary file cleanup will be performed.\n\nFound: {files:,} files\nSize: about {mb:.1f} MB\n\nStartup programs, services, and Windows settings will not be changed automatically.\n\nContinue?",
            "cleanup_running": "Temporary file cleanup is in progress...\n\nBusy and inaccessible files will be skipped.",
        },
        "de": {
            "title": "Optimierung",
            "subtitle": "Systemstatus analysieren und sicher optimieren",
            "system_status": "⚡ Systemstatus",
            "analysis": "🔍 Analyse",
            "checking": "System wird überprüft...",
            "temp_check": "Temporäre Dateien: Prüfung...\nAutostart: Prüfung...",
            "actions": "🛠 Optimierung",
            "actions_info": "Verfügbare Vorgänge werden erst nach Bestätigung ausgeführt.",
            "refresh": "↻  Analyse aktualisieren",
            "optimize": "⚡  Schnelle Optimierung",
            "normal": "✓ Das System arbeitet normal.\n\nEs wurden keine kritischen Probleme festgestellt, die eine sofortige Optimierung erfordern.",
            "scan_temp": "Temporäre Dateien: Scan...\nAutostart: Scan...",
            "refresh_scanning": "⌛  Scan läuft...",
            "temp_result": "Temporäre Dateien: {files:,} • {mb:.1f} MB\nAutostart: {startup} aktive Elemente",
            "disabled": " • {count} deaktiviert",
            "safe_cleanup": "\n\n• Temporäre Dateien können sicher bereinigt werden: etwa {mb:.1f} MB.",
            "cleanup_done": "✓ Sichere Bereinigung abgeschlossen.\n\nGelöschte temporäre Dateien: {files:,}.\nFreigegeben: {mb:.1f} MB.",
            "skipped": "\nBelegte/nicht zugängliche Dateien übersprungen: {count}.",
            "cleanup_error": "⚠ Bereinigung konnte nicht ausgeführt werden:\n{message}",
            "analysis_error": "Fehler bei der Systemanalyse:\n{error}",
            "high_cpu": "Hohe CPU-Auslastung",
            "high_ram": "Hohe RAM-Auslastung",
            "low_disk": "Wenig freier Speicherplatz auf dem Datenträger",
            "problems": "⚠ Potenzielle Probleme erkannt:",
            "no_files_title": "Optimierung",
            "no_files": "Keine temporären Dateien zur sicheren Löschung gefunden.\n\nAutostart-Programme und Systemeinstellungen werden nicht automatisch geändert.",
            "confirm_title": "Optimierung bestätigen",
            "confirm_text": "Es wird nur eine sichere Bereinigung temporärer Dateien durchgeführt.\n\nGefunden: {files:,} Dateien\nGröße: etwa {mb:.1f} MB\n\nAutostart-Programme, Dienste und Windows-Einstellungen werden nicht automatisch geändert.\n\nFortfahren?",
            "cleanup_button_running": "⌛  Bereinigung...",
            "cleanup_running": "Bereinigung temporärer Dateien läuft...\n\nBelegte und nicht zugängliche Dateien werden übersprungen.",
        },
        "it": {
            "title": "Ottimizzazione",
            "subtitle": "Analisi dello stato del sistema e ottimizzazione sicura",
            "system_status": "⚡ Stato del sistema",
            "analysis": "🔍 Analisi",
            "checking": "Controllo del sistema...",
            "temp_check": "File temporanei: controllo...\nAvvio automatico: controllo...",
            "actions": "🛠 Ottimizzazione",
            "actions_info": "Le operazioni disponibili verranno eseguite solo dopo la conferma.",
            "refresh": "↻  Aggiorna analisi",
            "optimize": "⚡  Ottimizzazione rapida",
            "normal": "✓ Il sistema funziona normalmente.\n\nNon sono stati rilevati problemi critici che richiedano un'ottimizzazione immediata.",
            "scan_temp": "File temporanei: scansione...\nAvvio automatico: scansione...",
            "refresh_scanning": "⌛  Scansione...",
            "temp_result": "File temporanei: {files:,} • {mb:.1f} MB\nAvvio automatico: {startup} elementi attivi",
            "disabled": " • {count} disabilitati",
            "safe_cleanup": "\n\n• È possibile pulire in sicurezza i file temporanei: circa {mb:.1f} MB.",
            "cleanup_done": "✓ Pulizia sicura completata.\n\nFile temporanei eliminati: {files:,}.\nSpazio liberato: {mb:.1f} MB.",
            "skipped": "\nFile occupati/non accessibili ignorati: {count}.",
            "cleanup_error": "⚠ Impossibile eseguire l'operazione di pulizia:\n{message}",
            "analysis_error": "Errore nell'analisi del sistema:\n{error}",
            "high_cpu": "Elevato utilizzo della CPU",
            "high_ram": "Elevato utilizzo della RAM",
            "low_disk": "Poco spazio libero sul disco",
            "problems": "⚠ Rilevati potenziali problemi:",
            "no_files_title": "Ottimizzazione",
            "no_files": "Non sono stati trovati file temporanei da eliminare in sicurezza.\n\nI programmi di avvio e le impostazioni di sistema non verranno modificati automaticamente.",
            "confirm_title": "Conferma ottimizzazione",
            "confirm_text": "Verrà eseguita solo una pulizia sicura dei file temporanei.\n\nTrovati: {files:,} file\nDimensione: circa {mb:.1f} MB\n\nI programmi di avvio, i servizi e le impostazioni di Windows non verranno modificati automaticamente.\n\nContinuare?",
            "cleanup_button_running": "⌛  Pulizia...",
            "cleanup_running": "Pulizia dei file temporanei in corso...\n\nI file occupati e non accessibili verranno ignorati.",
        },
        "es": {
            "title": "Optimización",
            "subtitle": "Analizar el estado del sistema y realizar una optimización segura",
            "system_status": "⚡ Estado del sistema",
            "analysis": "🔍 Análisis",
            "checking": "Comprobando el sistema...",
            "temp_check": "Archivos temporales: comprobando...\nInicio automático: comprobando...",
            "actions": "🛠 Optimización",
            "actions_info": "Las operaciones disponibles se ejecutarán solo después de la confirmación.",
            "refresh": "↻  Actualizar análisis",
            "optimize": "⚡  Optimización rápida",
            "normal": "✓ El sistema funciona con normalidad.\n\nNo se han detectado problemas críticos que requieran una optimización inmediata.",
            "scan_temp": "Archivos temporales: escaneando...\nInicio automático: escaneando...",
            "refresh_scanning": "⌛  Escaneando...",
            "temp_result": "Archivos temporales: {files:,} • {mb:.1f} MB\nInicio automático: {startup} elementos activos",
            "disabled": " • {count} deshabilitados",
            "safe_cleanup": "\n\n• Se pueden limpiar de forma segura los archivos temporales: unos {mb:.1f} MB.",
            "cleanup_done": "✓ Limpieza segura completada.\n\nArchivos temporales eliminados: {files:,}.\nLiberado: {mb:.1f} MB.",
            "skipped": "\nArchivos ocupados/no accesibles omitidos: {count}.",
            "cleanup_error": "⚠ No se pudo realizar la operación de limpieza:\n{message}",
            "analysis_error": "Error de análisis del sistema:\n{error}",
            "high_cpu": "Alta carga de CPU",
            "high_ram": "Alto uso de RAM",
            "low_disk": "Poco espacio libre en el disco",
            "problems": "⚠ Se han detectado posibles problemas:",
            "no_files_title": "Optimización",
            "no_files": "No se encontraron archivos temporales para eliminar de forma segura.\n\nLos programas de inicio y la configuración del sistema no se modificarán automáticamente.",
            "confirm_title": "Confirmar optimización",
            "confirm_text": "Solo se realizará una limpieza segura de los archivos temporales.\n\nEncontrados: {files:,} archivos\nTamaño: unos {mb:.1f} MB\n\nLos programas de inicio, servicios y configuraciones de Windows no se modificarán automáticamente.\n\n¿Continuar?",
            "cleanup_button_running": "⌛  Limpiando...",
            "cleanup_running": "La limpieza de archivos temporales está en curso...\n\nLos archivos ocupados y no accesibles se omitirán.",
        },
        "fr": {
            "title": "Optimisation",
            "subtitle": "Analyser l’état du système et effectuer une optimisation sûre",
            "system_status": "⚡ État du système",
            "analysis": "🔍 Analyse",
            "checking": "Vérification du système...",
            "temp_check": "Fichiers temporaires : vérification...\nDémarrage automatique : vérification...",
            "actions": "🛠 Optimisation",
            "actions_info": "Les opérations disponibles seront exécutées uniquement après confirmation.",
            "refresh": "↻  Actualiser l’analyse",
            "optimize": "⚡  Optimisation rapide",
            "normal": "✓ Le système fonctionne normalement.\n\nAucun problème critique nécessitant une optimisation immédiate n'a été détecté.",
            "scan_temp": "Fichiers temporaires : analyse...\nDémarrage automatique : analyse...",
            "refresh_scanning": "⌛  Analyse...",
            "temp_result": "Fichiers temporaires : {files:,} • {mb:.1f} Mo\nDémarrage automatique : {startup} éléments actifs",
            "disabled": " • {count} désactivés",
            "safe_cleanup": "\n\n• Les fichiers temporaires peuvent être nettoyés en toute sécurité : environ {mb:.1f} Mo.",
            "cleanup_done": "✓ Nettoyage sécurisé terminé.\n\nFichiers temporaires supprimés : {files:,}.\nEspace libéré : {mb:.1f} Mo.",
            "skipped": "\nFichiers occupés/inaccessibles ignorés : {count}.",
            "cleanup_error": "⚠ Impossible d’effectuer l’opération de nettoyage :\n{message}",
            "analysis_error": "Erreur d’analyse du système :\n{error}",
            "high_cpu": "Charge CPU élevée",
            "high_ram": "Utilisation élevée de la RAM",
            "low_disk": "Espace libre insuffisant sur le disque",
            "problems": "⚠ Problèmes potentiels détectés :",
            "no_files_title": "Optimisation",
            "no_files": "Aucun fichier temporaire à supprimer en toute sécurité n’a été trouvé.\n\nLes programmes de démarrage et les paramètres système ne seront pas modifiés automatiquement.",
            "confirm_title": "Confirmation de l’optimisation",
            "confirm_text": "Seul un nettoyage sécurisé des fichiers temporaires sera effectué.\n\nTrouvé : {files:,} fichiers\nTaille : environ {mb:.1f} Mo\n\nLes programmes de démarrage, les services et les paramètres Windows ne seront pas modifiés automatiquement.\n\nContinuer ?",
            "cleanup_button_running": "⌛  Nettoyage...",
            "cleanup_running": "Nettoyage des fichiers temporaires en cours...\n\nLes fichiers occupés et inaccessibles seront ignorés.",
        },
    }

    def _tr(self, key, **kwargs):
        language = getattr(self, "ui_language", "ru")

        translations = self.TRANSLATIONS.get(
            language,
            self.TRANSLATIONS["ru"],
        )

        text = translations.get(
           key,
           self.TRANSLATIONS["ru"].get(key, key),
        )

        if kwargs:
            text = text.format(**kwargs)

        return text

    def set_language(self, language):
        language = str(language or "ru")

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        if hasattr(self, "title_label"):
            self.title_label.setText(self._tr("title"))

        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(self._tr("subtitle"))

        if hasattr(self, "status_title_label"):
            self.status_title_label.setText(
                self._tr("system_status")
            )

        if hasattr(self, "analysis_title_label"):
            self.analysis_title_label.setText(
                self._tr("analysis")
            )

        if hasattr(self, "actions_title_label"):
            self.actions_title_label.setText(
                self._tr("actions")
            )

        if hasattr(self, "actions_info"):
            self.actions_info.setText(
                self._tr("actions_info")
            )

        if hasattr(self, "refresh_button"):
            self.refresh_button.setText(
                self._tr("refresh")
            )

        if hasattr(self, "optimize_button"):
            self.optimize_button.setText(
                self._tr("optimize")
            )

        if hasattr(self, "analysis_label"):
            self.analysis_label.setText(
                self._tr("checking")
            )

        if hasattr(self, "cleanup_label"):
            self.cleanup_label.setText(
                self._tr("temp_check")
            )
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui_language = "ru"

        self.setObjectName("OptimizePage")

        self._cleanup_worker = None
        self._cleanup_scan = {}
        self._startup_scan = {}

        self.setStyleSheet("""
            QWidget#OptimizePage {
                background: #050b18;
            }

            QFrame {
                background: #091528;
                border: 1px solid #182c4a;
                border-radius: 12px;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QPushButton {
                background: #168cff;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #2698ff;
            }

            QPushButton:pressed {
                background: #0d72d8;
            }

            QProgressBar {
                background: #071020;
                border: 1px solid #182c4a;
                border-radius: 6px;
                height: 10px;
                text-align: center;
            }

            QProgressBar::chunk {
                background: #168cff;
                border-radius: 5px;
            }
        """)

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            28,
            24,
            28,
            24,
        )

        self.main_layout.setSpacing(16)

        # ======================================================
        # TITLE
        # ======================================================

        self.title_label = QLabel("Оптимизация")

        self.title_label.setStyleSheet("""
            QLabel {
                color: #F4F7FF;
                font-size: 30px;
                font-weight: 800;
            }
        """)

        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(
            "Анализ состояния системы и безопасная оптимизация"
        )

        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #8EA3BD;
                font-size: 13px;
            }
        """)

        self.main_layout.addWidget(self.subtitle_label)

        # ======================================================
        # SYSTEM STATUS
        # ======================================================

        self.status_card = QFrame()

        status_layout = QVBoxLayout(
            self.status_card
        )

        status_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        status_layout.setSpacing(10)

        self.status_title_label = QLabel(
            "⚡ Состояние системы"
        )

        self.status_title_label.setStyleSheet("""
            QLabel {
                color: #22D3EE;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        status_layout.addWidget(self.status_title_label)

        # CPU

        self.cpu_label = QLabel(
            "CPU: 0%"
        )

        self.cpu_label.setStyleSheet(
            "color: #F4F7FF; font-size: 13px;"
        )

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)

        status_layout.addWidget(
            self.cpu_label
        )

        status_layout.addWidget(
            self.cpu_bar
        )

        # RAM

        self.ram_label = QLabel(
            "RAM: 0%"
        )

        self.ram_label.setStyleSheet(
            "color: #F4F7FF; font-size: 13px;"
        )

        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)

        status_layout.addWidget(
            self.ram_label
        )

        status_layout.addWidget(
            self.ram_bar
        )

        # DISK

        self.disk_label = QLabel(
            "Disk: 0%"
        )

        self.disk_label.setStyleSheet(
            "color: #F4F7FF; font-size: 13px;"
        )

        self.disk_bar = QProgressBar()
        self.disk_bar.setRange(0, 100)

        status_layout.addWidget(
            self.disk_label
        )

        status_layout.addWidget(
            self.disk_bar
        )

        self.main_layout.addWidget(
            self.status_card
        )

        # ======================================================
        # ANALYSIS
        # ======================================================

        self.analysis_card = QFrame()

        analysis_layout = QVBoxLayout(
            self.analysis_card
        )

        analysis_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        analysis_layout.setSpacing(8)

        self.analysis_title_label = QLabel(
            "🔍 Анализ"
        )

        self.analysis_title_label.setStyleSheet("""
            QLabel {
                color: #A970FF;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        analysis_layout.addWidget(
            self.analysis_title_label
        )

        self.analysis_label = QLabel(
            "Проверка системы..."
        )

        self.analysis_label.setWordWrap(True)

        self.analysis_label.setStyleSheet("""
            QLabel {
                color: #AEBBD0;
                font-size: 13px;
                padding-top: 4px;
            }
        """)

        analysis_layout.addWidget(
            self.analysis_label
        )

        self.cleanup_label = QLabel(
            "Временные файлы: проверка...\nАвтозагрузка: проверка..."
        )
        self.cleanup_label.setWordWrap(True)
        self.cleanup_label.setStyleSheet("""
            QLabel {
                color: #8EA3BD;
                font-size: 12px;
                padding-top: 2px;
            }
        """)
        analysis_layout.addWidget(self.cleanup_label)

        self.main_layout.addWidget(
            self.analysis_card
        )

        # ======================================================
        # ACTIONS
        # ======================================================

        actions_card = QFrame()

        actions_layout = QVBoxLayout(
            actions_card
        )

        actions_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        actions_layout.setSpacing(10)

        self.actions_title_label = QLabel(
            "🛠 Оптимизация"
        )

        self.actions_title_label.setStyleSheet("""
            QLabel {
                color: #79FF21;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        actions_layout.addWidget(
            self.actions_title_label
        )

        self.actions_info = QLabel(
            "Доступные операции будут выполняться "
            "только после подтверждения."
        )

        self.actions_info.setWordWrap(True)

        self.actions_info.setStyleSheet("""
            QLabel {
                color: #8EA3BD;
                font-size: 12px;
            }
        """)

        actions_layout.addWidget(
            self.actions_info
        )

        buttons = QHBoxLayout()

        self.refresh_button = QPushButton(
            "↻  Обновить анализ"
        )

        
        self.refresh_button.clicked.connect(
            self.run_full_analysis
        )

        buttons.addWidget(
            self.refresh_button
        )

        self.optimize_button = QPushButton(
            "⚡  Быстрая оптимизация"
        )

        self.optimize_button.clicked.connect(
            self.quick_optimize
        )

        buttons.addWidget(
            self.optimize_button
        )

        buttons.addStretch()

        actions_layout.addLayout(
            buttons
        )

        self.main_layout.addWidget(
            actions_card
        )

        self.main_layout.addStretch()

        # ======================================================
        # TIMER
        # ======================================================

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_system
        )

        self.timer.start(3000)

        self.run_full_analysis()

    # ==========================================================
    # FULL ANALYSIS
    # ==========================================================

    def run_full_analysis(self):
        """Обновляет показатели и запускает безопасное сканирование."""
        self.update_system()

        self.cleanup_label.setText(self._tr("scan_temp"))
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText(self._tr("refresh_scanning"))

        try:
            self._startup_scan = scan_startup()
        except Exception as exc:
            self._startup_scan = {
                "count": 0,
                "disabled_count": 0,
                "error": str(exc),
            }

        self._start_cleanup_worker("scan")

    def _start_cleanup_worker(self, operation):
        if self._cleanup_worker is not None and self._cleanup_worker.isRunning():
            return

        self._cleanup_worker = CleanupWorker(operation, self)
        self._cleanup_worker.scan_finished.connect(self._cleanup_scan_finished)
        self._cleanup_worker.delete_finished.connect(self._cleanup_delete_finished)
        self._cleanup_worker.error.connect(self._cleanup_error)
        self._cleanup_worker.finished.connect(self._cleanup_worker_finished)
        self._cleanup_worker.start()

    def _cleanup_scan_finished(self, result):
        self._cleanup_scan = result or {}

        mb = float(
            self._cleanup_scan.get("megabytes", 0) or 0
        )
        files = int(
            self._cleanup_scan.get("files", 0) or 0
        )
        startup_count = int(
            self._startup_scan.get("count", 0) or 0
        )
        disabled_count = int(
            self._startup_scan.get("disabled_count", 0) or 0
        )

        text = self._tr(
            "temp_result",
            files=files,
            mb=mb,
            startup=startup_count,
        )

        if disabled_count:
            text += self._tr(
                "disabled",
                count=disabled_count,
            )

        self.cleanup_label.setText(text)
        self.refresh_button.setText(self._tr("refresh"))
        self.refresh_button.setEnabled(True)

        if files:
           self.analysis_label.setText(
            self.analysis_label.text()
            + self._tr("safe_cleanup", mb=mb)
        )

    def _cleanup_delete_finished(self, result):
        deleted = int(
            (result or {}).get("deleted_files", 0) or 0
        )
        mb = float(
            (result or {}).get("deleted_megabytes", 0) or 0
        )
        skipped = int(
            (result or {}).get("skipped", 0) or 0
        )

        text = self._tr(
            "cleanup_done",
            files=deleted,
            mb=mb,
        )

        if skipped:
            text += self._tr(
                "skipped",
                count=skipped,
            )

        self.analysis_label.setText(text)
        self.optimize_button.setEnabled(True)
        self.optimize_button.setText(
            self._tr("optimize")
        )

        self.run_full_analysis()

    def _cleanup_error(self, message): 
        self.analysis_label.setText(
            self._tr(
                "cleanup_error",
                message=message,
            )
        )

        self.refresh_button.setEnabled(True)
        self.refresh_button.setText(
            self._tr("refresh")
        )

        self.optimize_button.setEnabled(True)
        self.optimize_button.setText(
            self._tr("optimize")
        )

    def _cleanup_worker_finished(self):
        worker = self._cleanup_worker
        if worker is not None:
            worker.deleteLater()
        self._cleanup_worker = None

    # ==========================================================
    # SYSTEM UPDATE
    # ==========================================================

    def update_system(self):

        try:

            cpu = psutil.cpu_percent(
                interval=None
            )

            memory = psutil.virtual_memory()

            disk = psutil.disk_usage(
                "C:\\"
            )

            ram = memory.percent
            disk_percent = disk.percent

            self.cpu_label.setText(
                f"CPU: {cpu:.1f}%"
            )

            self.cpu_bar.setValue(
                int(cpu)
            )

            self.ram_label.setText(
                f"RAM: {ram:.1f}%"
            )

            self.ram_bar.setValue(
                int(ram)
            )

            self.disk_label.setText(
                f"Disk: {disk_percent:.1f}%"
            )

            self.disk_bar.setValue(
                int(disk_percent)
            )

            # --------------------------------------------------
            # ANALYSIS
            # --------------------------------------------------

            problems = []

            if cpu >= 85:
                problems.append(self._tr("high_cpu"))

            if ram >= 85:
                problems.append(self._tr("high_ram"))

            if disk_percent >= 90:
                problems.append(self._tr("low_disk"))

            if not problems:
                self.analysis_label.setText(
                    self._tr("normal")
                )
            else:
                self.analysis_label.setText(
                    self._tr("problems")
                    + "\n\n"
                    + "\n".join(
                        f"• {problem}"
                        for problem in problems
                    )
                )

        except Exception as exc:
            self.analysis_label.setText(
                self._tr(
                    "analysis_error",
                    error=exc,
                )
            )

    # ==========================================================
    # QUICK OPTIMIZATION
    # ==========================================================

    def quick_optimize(self):
        """Выполняет только безопасную очистку временных файлов."""

        if (
            self._cleanup_worker is not None
            and self._cleanup_worker.isRunning()
        ):
            return

        if not self._cleanup_scan:
            self.run_full_analysis()
            return

        mb = float(
            self._cleanup_scan.get("megabytes", 0) or 0
        )
        files = int(
            self._cleanup_scan.get("files", 0) or 0
        )

        if files <= 0:
            QMessageBox.information(
                self,
                self._tr("no_files_title"),
                self._tr("no_files"),
            )
            return

        result = QMessageBox.question(
            self,
            self._tr("confirm_title"),
            self._tr(
                "confirm_text",
                files=files,
                mb=mb,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        self.optimize_button.setEnabled(False)
        self.optimize_button.setText(
            self._tr("cleanup_button_running")
        )

        self.analysis_label.setText(
            self._tr("cleanup_running")
        )

        self._start_cleanup_worker("delete")

    # ==========================================================
    # SHUTDOWN
    # ==========================================================

    def shutdown(self):

        print(
            "[Optimize] Shutdown started"
        )

        try:

            if self.timer is not None:
                self.timer.stop()

            if self._cleanup_worker is not None and self._cleanup_worker.isRunning():
                self._cleanup_worker.stop(5000)

        except Exception as exc:

            print(
                f"[Optimize] Timer shutdown error: {exc}"
            )

        print(
            "[Optimize] Shutdown complete"
        )

    # ==========================================================
    # CLOSE EVENT
    # ==========================================================

    def closeEvent(
        self,
        event,
    ):

        self.shutdown()

        event.accept()















