from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QFrame,
    QProgressBar,
)

from app.services.ai_worker import AIWorker


# ==========================================================
# AI ASSISTANT PAGE
# ==========================================================


class AIAssistantPage(QWidget):
    """
    Страница AI Assistant.

    Использует существующий AIWorker:
        analyze_system()

    DiagnosticEngine не изменяется.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.worker = None
        self._language = "ru"

        self._build_ui()

    # ======================================================
    # UI
    # ======================================================

    def _build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25,
        )

        main_layout.setSpacing(18)

        # --------------------------------------------------
        # TITLE
        # --------------------------------------------------

        self.title_label = QLabel(
            self._tr("title")
        )

        self.title_label.setFont(
            QFont(
                "Segoe UI",
                24,
                QFont.Bold,
            )
        )

        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            self.title_label
        )

        # --------------------------------------------------
        # SUBTITLE
        # --------------------------------------------------

        self.subtitle_label = QLabel(
            self._tr("subtitle")
        )

        self.subtitle_label.setStyleSheet(
            """
            QLabel {
                color: #9aa4b2;
                font-size: 14px;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            self.subtitle_label
        )

        # --------------------------------------------------
        # STATUS CARD
        # --------------------------------------------------

        self.status_card = QFrame()

        self.status_card.setObjectName(
            "StatusCard"
        )

        self.status_card.setStyleSheet(
            """
            QFrame#StatusCard {
                background-color: #171b22;
                border: 1px solid #252b35;
                border-radius: 14px;
            }
            """
        )

        status_layout = QVBoxLayout(
            self.status_card
        )

        status_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        # --------------------------------------------------
        # STATUS TITLE
        # --------------------------------------------------

        self.status_label = QLabel(
            self._tr("ready")
        )

        self.status_label.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Bold,
            )
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            """
        )

        status_layout.addWidget(
            self.status_label
        )

        # --------------------------------------------------
        # USER
        # --------------------------------------------------

        self.user_label = QLabel(
            self._tr(
                "user",
                username="—",
            )
        )

        self.user_label.setStyleSheet(
            """
            QLabel {
                color: #9aa4b2;
                font-size: 13px;
                background: transparent;
            }
            """
        )

        status_layout.addWidget(
            self.user_label
        )

        # --------------------------------------------------
        # MESSAGE
        # --------------------------------------------------

        self.message_label = QLabel(
            self._tr("start_message")
        )

        self.message_label.setWordWrap(True)

        self.message_label.setStyleSheet(
            """
            QLabel {
                color: #d7dce3;
                font-size: 14px;
                padding-top: 8px;
                background: transparent;
            }
            """
        )

        status_layout.addWidget(
            self.message_label
        )

        main_layout.addWidget(
            self.status_card
        )

        # --------------------------------------------------
        # METRICS
        # --------------------------------------------------

        metrics_layout = QHBoxLayout()

        metrics_layout.setSpacing(12)

        self.cpu_card = self._create_metric_card(
            "CPU",
            "—",
        )

        self.ram_card = self._create_metric_card(
            "RAM",
            "—",
        )

        self.disk_card = self._create_metric_card(
            "DISK",
            "—",
        )

        self.gpu_card = self._create_metric_card(
            "GPU",
            "—",
        )

        metrics_layout.addWidget(
            self.cpu_card["frame"]
        )

        metrics_layout.addWidget(
            self.ram_card["frame"]
        )

        metrics_layout.addWidget(
            self.disk_card["frame"]
        )

        metrics_layout.addWidget(
            self.gpu_card["frame"]
        )

        main_layout.addLayout(
            metrics_layout
        )

        # --------------------------------------------------
        # ANALYSIS TITLE
        # --------------------------------------------------

        self.analysis_title_label = QLabel(
            self._tr("analysis_title")
        )

        self.analysis_title_label.setFont(
            QFont(
                "Segoe UI",
                16,
                QFont.Bold,
            )
        )

        self.analysis_title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            self.analysis_title_label
        )

        # --------------------------------------------------
        # ANALYSIS TEXT
        # --------------------------------------------------

        self.analysis_text = QTextEdit()

        self.analysis_text.setReadOnly(
            True
        )

        self.analysis_text.setMinimumHeight(
            180
        )

        self.analysis_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #11151b;
                color: #d7dce3;
                border: 1px solid #252b35;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            """
        )

        self.analysis_text.setPlainText(
            self._tr("analysis_ready")
        )

        main_layout.addWidget(
            self.analysis_text
        )

        # --------------------------------------------------
        # PROGRESS
        # --------------------------------------------------

        self.progress = QProgressBar()

        self.progress.setRange(
            0,
            0,
        )

        self.progress.setVisible(
            False
        )

        self.progress.setFixedHeight(
            5
        )

        main_layout.addWidget(
            self.progress
        )

        # --------------------------------------------------
        # BUTTONS
        # --------------------------------------------------

        buttons_layout = QHBoxLayout()

        self.analyze_button = QPushButton(
            self._tr("analyze")
        )

        self.analyze_button.setMinimumHeight(
            46
        )

        self.analyze_button.setCursor(
            Qt.PointingHandCursor
        )

        self.analyze_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #3474f0;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #263246;
                color: #788397;
            }
            """
        )

        self.analyze_button.clicked.connect(
            self.start_analysis
        )

        buttons_layout.addWidget(
            self.analyze_button
        )

        buttons_layout.addStretch()

        main_layout.addLayout(
            buttons_layout
        )

        main_layout.addStretch()

    # ======================================================
    # LANGUAGE
    # ======================================================

    def _tr(self, key, **kwargs):

        translations = {

            # ==================================================
            # RU
            # ==================================================

            "ru": {
                "title": "AI Assistant",
                "subtitle": "Интеллектуальный анализ состояния компьютера",
                "ready": "Готов к анализу",
                "user": "Пользователь: {username}",

                "start_message": (
                    "Нажмите «Проанализировать ПК», чтобы проверить "
                    "состояние системы."
                ),

                "analysis_title": "AI Analysis",

                "analysis_ready": (
                    "AI Assistant готов.\n\n"
                    "Запустите анализ системы."
                ),

                "analyze": "🤖 Проанализировать ПК",
                "analyzing": "Анализирую...",
                "analysis_running": "Выполняется анализ...",

                "collecting": (
                    "AI собирает информацию о состоянии компьютера."
                ),

                "analysis_system_running":
                    "Выполняется анализ системы...",

                "system_good":
                    "✓ Система работает нормально",

                "system_attention":
                    "⚠ Требуется внимание",

                "system_critical":
                    "✕ Обнаружена проблема",

                "system_state":
                    "Состояние системы",

                "analysis_finished":
                    "Анализ завершён.",

                "error":
                    "✕ Ошибка анализа",

                "error_message":
                    "AI Assistant не смог выполнить анализ.",

                "error_details":
                    "Подробности ошибки:",

                "state":
                    "Состояние: {status}",

                "problems":
                    "Обнаружено проблем: {count}",

                "recovered":
                    "Восстановлено проблем: {count}",

                "recommendations_system":
                    "Рекомендации системы:",

                "possible_causes":
                    "Возможные причины",

                "recommendations_ai":
                    "Рекомендации AI:",

                "recommendation":
                    "Рекомендация",

                "analysis_time":
                    "Время анализа: {time:.3f} сек.",
            },

            # ==================================================
            # EN
            # ==================================================

            "en": {
                "title": "AI Assistant",
                "subtitle": "Intelligent computer system analysis",
                "ready": "Ready for analysis",
                "user": "User: {username}",

                "start_message": (
                    "Click «Analyze PC» to check "
                    "the system status."
                ),

                "analysis_title": "AI Analysis",

                "analysis_ready": (
                    "AI Assistant is ready.\n\n"
                    "Start system analysis."
                ),

                "analyze": "🤖 Analyze PC",
                "analyzing": "Analyzing...",
                "analysis_running": "Analysis in progress...",

                "collecting": (
                    "AI is collecting information about the computer."
                ),

                "analysis_system_running":
                    "System analysis in progress...",

                "system_good":
                    "✓ System is working normally",

                "system_attention":
                    "⚠ Attention required",

                "system_critical":
                    "✕ Problem detected",

                "system_state":
                    "System status",

                "analysis_finished":
                    "Analysis completed.",

                "error":
                    "✕ Analysis error",

                "error_message":
                    "AI Assistant could not complete the analysis.",

                "error_details":
                    "Error details:",

                "state":
                    "Status: {status}",

                "problems":
                    "Problems detected: {count}",

                "recovered":
                    "Problems recovered: {count}",

                "recommendations_system":
                    "System recommendations:",

                "possible_causes":
                    "Possible causes",

                "recommendations_ai":
                    "AI recommendations:",

                "recommendation":
                    "Recommendation",

                "analysis_time":
                    "Analysis time: {time:.3f} sec.",
            },

            # ==================================================
            # UK
            # ==================================================

            "uk": {
                "title": "AI Assistant",
                "subtitle": "Інтелектуальний аналіз стану комп'ютера",
                "ready": "Готовий до аналізу",
                "user": "Користувач: {username}",

                "start_message": (
                    "Натисніть «Проаналізувати ПК», щоб перевірити "
                    "стан системи."
                ),

                "analysis_title": "AI-аналіз",

                "analysis_ready": (
                    "AI Assistant готовий.\n\n"
                    "Запустіть аналіз системи."
                ),

                "analyze": "🤖 Проаналізувати ПК",
                "analyzing": "Аналізую...",
                "analysis_running": "Виконується аналіз...",

                "collecting": (
                    "AI збирає інформацію про стан комп'ютера."
                ),

                "analysis_system_running":
                    "Виконується аналіз системи...",

                "system_good":
                    "✓ Система працює нормально",

                "system_attention":
                    "⚠ Потрібна увага",

                "system_critical":
                    "✕ Виявлено проблему",

                "system_state":
                    "Стан системи",

                "analysis_finished":
                    "Аналіз завершено.",

                "error":
                    "✕ Помилка аналізу",

                "error_message":
                    "AI Assistant не зміг виконати аналіз.",

                "error_details":
                    "Подробиці помилки:",

                "state":
                    "Стан: {status}",

                "problems":
                    "Виявлено проблем: {count}",

                "recovered":
                    "Відновлено проблем: {count}",

                "recommendations_system":
                    "Рекомендації системи:",

                "possible_causes":
                    "Можливі причини",

                "recommendations_ai":
                    "Рекомендації AI:",

                "recommendation":
                    "Рекомендація",

                "analysis_time":
                    "Час аналізу: {time:.3f} с.",
            },

            # ==================================================
            # DE
            # ==================================================

            "de": {
                "title": "AI-Assistent",
                "subtitle": "Intelligente Analyse des Computerzustands",
                "ready": "Bereit für die Analyse",
                "user": "Benutzer: {username}",

                "start_message": (
                    "Klicken Sie auf „PC analysieren“, um "
                    "den Systemstatus zu prüfen."
                ),

                "analysis_title": "KI-Analyse",

                "analysis_ready": (
                    "AI-Assistent ist bereit.\n\n"
                    "Starten Sie die Systemanalyse."
                ),

                "analyze": "🤖 PC analysieren",
                "analyzing": "Analyse läuft...",
                "analysis_running": "Analyse wird durchgeführt...",

                "collecting":
                    "Die KI sammelt Informationen über den Computer.",

                "analysis_system_running":
                    "Systemanalyse läuft...",

                "system_good":
                    "✓ System funktioniert normal",

                "system_attention":
                    "⚠ Aufmerksamkeit erforderlich",

                "system_critical":
                    "✕ Problem erkannt",

                "system_state":
                    "Systemstatus",

                "analysis_finished":
                    "Analyse abgeschlossen.",

                "error":
                    "✕ Analysefehler",

                "error_message":
                    "Der AI-Assistent konnte die Analyse nicht durchführen.",

                "error_details":
                    "Fehlerdetails:",

                "state":
                    "Status: {status}",

                "problems":
                    "Erkannte Probleme: {count}",

                "recovered":
                    "Behobene Probleme: {count}",

                "recommendations_system":
                    "Systemempfehlungen:",

                "possible_causes":
                    "Mögliche Ursachen",

                "recommendations_ai":
                    "KI-Empfehlungen:",

                "recommendation":
                    "Empfehlung",

                "analysis_time":
                    "Analysezeit: {time:.3f} Sek.",
            },

            # ==================================================
            # IT
            # ==================================================

            "it": {
                "title": "Assistente AI",
                "subtitle": "Analisi intelligente dello stato del computer",
                "ready": "Pronto per l'analisi",
                "user": "Utente: {username}",

                "start_message": (
                    "Fai clic su «Analizza PC» per controllare "
                    "lo stato del sistema."
                ),

                "analysis_title": "Analisi AI",

                "analysis_ready": (
                    "Assistente AI pronto.\n\n"
                    "Avvia l'analisi del sistema."
                ),

                "analyze": "🤖 Analizza PC",
                "analyzing": "Analisi in corso...",
                "analysis_running": "Analisi in corso...",

                "collecting":
                    "L'AI sta raccogliendo informazioni sul computer.",

                "analysis_system_running":
                    "Analisi del sistema in corso...",

                "system_good":
                    "✓ Il sistema funziona normalmente",

                "system_attention":
                    "⚠ È richiesta attenzione",

                "system_critical":
                    "✕ Problema rilevato",

                "system_state":
                    "Stato del sistema",

                "analysis_finished":
                    "Analisi completata.",

                "error":
                    "✕ Errore di analisi",

                "error_message":
                    "L'Assistente AI non ha potuto completare l'analisi.",

                "error_details":
                    "Dettagli dell'errore:",

                "state":
                    "Stato: {status}",

                "problems":
                    "Problemi rilevati: {count}",

                "recovered":
                    "Problemi risolti: {count}",

                "recommendations_system":
                    "Raccomandazioni del sistema:",

                "possible_causes":
                    "Possibili cause",

                "recommendations_ai":
                    "Raccomandazioni AI:",

                "recommendation":
                    "Raccomandazione",

                "analysis_time":
                    "Tempo di analisi: {time:.3f} sec.",
            },

            # ==================================================
            # ES
            # ==================================================

            "es": {
                "title": "Asistente de IA",
                "subtitle": "Análisis inteligente del estado del ordenador",
                "ready": "Listo para el análisis",
                "user": "Usuario: {username}",

                "start_message": (
                    "Pulsa «Analizar PC» para comprobar "
                    "el estado del sistema."
                ),

                "analysis_title": "Análisis de IA",

                "analysis_ready": (
                    "Asistente de IA listo.\n\n"
                    "Inicia el análisis del sistema."
                ),

                "analyze": "🤖 Analizar PC",
                "analyzing": "Analizando...",
                "analysis_running": "Análisis en curso...",

                "collecting":
                    "La IA está recopilando información del ordenador.",

                "analysis_system_running":
                    "Análisis del sistema en curso...",

                "system_good":
                    "✓ El sistema funciona normalmente",

                "system_attention":
                    "⚠ Se requiere atención",

                "system_critical":
                    "✕ Problema detectado",

                "system_state":
                    "Estado del sistema",

                "analysis_finished":
                    "Análisis completado.",

                "error":
                    "✕ Error de análisis",

                "error_message":
                    "El Asistente de IA no pudo completar el análisis.",

                "error_details":
                    "Detalles del error:",

                "state":
                    "Estado: {status}",

                "problems":
                    "Problemas detectados: {count}",

                "recovered":
                    "Problemas recuperados: {count}",

                "recommendations_system":
                    "Recomendaciones del sistema:",

                "possible_causes":
                    "Posibles causas",

                "recommendations_ai":
                    "Recomendaciones de IA:",

                "recommendation":
                    "Recomendación",

                "analysis_time":
                    "Tiempo de análisis: {time:.3f} s.",
            },

            # ==================================================
            # FR
            # ==================================================

            "fr": {
                "title": "Assistant IA",
                "subtitle": "Analyse intelligente de l'état de l'ordinateur",
                "ready": "Prêt pour l'analyse",
                "user": "Utilisateur : {username}",

                "start_message": (
                    "Cliquez sur « Analyser le PC » pour vérifier "
                    "l'état du système."
                ),

                "analysis_title": "Analyse IA",

                "analysis_ready": (
                    "Assistant IA prêt.\n\n"
                    "Lancez l'analyse du système."
                ),

                "analyze": "🤖 Analyser le PC",
                "analyzing": "Analyse en cours...",
                "analysis_running": "Analyse en cours...",

                "collecting":
                    "L'IA collecte des informations sur l'ordinateur.",

                "analysis_system_running":
                    "Analyse du système en cours...",

                "system_good":
                    "✓ Le système fonctionne normalement",

                "system_attention":
                    "⚠ Une attention est requise",

                "system_critical":
                    "✕ Problème détecté",

                "system_state":
                    "État du système",

                "analysis_finished":
                    "Analyse terminée.",

                "error":
                    "✕ Erreur d'analyse",

                "error_message":
                    "L'Assistant IA n'a pas pu terminer l'analyse.",

                "error_details":
                    "Détails de l'erreur :",

                "state":
                    "État : {status}",

                "problems":
                    "Problèmes détectés : {count}",

                "recovered":
                    "Problèmes résolus : {count}",

                "recommendations_system":
                    "Recommandations du système:",

                "possible_causes":
                    "Causes possibles",

                "recommendations_ai":
                    "Recommandations IA:",

                "recommendation":
                    "Recommandation",

                "analysis_time":
                    "Temps d'analyse : {time:.3f} s.",
            },
        }

        language = getattr(
            self,
            "_language",
            "ru",
        )

        lang = translations.get(
            language,
            translations["ru"],
        )

        text = lang.get(
            key,
            translations["ru"].get(
                key,
                key,
            ),
        )

        try:
            return text.format(**kwargs)

        except (KeyError, ValueError):
            return text

    # ======================================================
    # SET LANGUAGE
    # ======================================================

    def set_language(self, language):

        if language not in (
            "ru",
            "en",
            "uk",
            "de",
            "it",
            "es",
            "fr",
        ):
            language = "ru"

        self._language = language

        # --------------------------------------------------
        # STATIC UI
        # --------------------------------------------------

        self.title_label.setText(
            self._tr("title")
        )

        self.subtitle_label.setText(
            self._tr("subtitle")
        )

        self.analysis_title_label.setText(
            self._tr("analysis_title")
        )

        self.analyze_button.setText(
            self._tr("analyze")
        )

        # --------------------------------------------------
        # DO NOT DESTROY FINISHED ANALYSIS
        # --------------------------------------------------

        if self.worker is None:

            self.status_label.setText(
                self._tr("ready")
            )

            self.user_label.setText(
                self._tr(
                    "user",
                    username="—",
                )
            )

            self.message_label.setText(
                self._tr("start_message")
            )

            current_text = self.analysis_text.toPlainText()

            if (
                not current_text.strip()
                or current_text in {
                    "AI Assistant готов.\n\nЗапустите анализ системы.",
                    "AI Assistant is ready.\n\nStart system analysis.",
                    "AI Assistant ready.\n\nStart system analysis.",
                }
            ):
                self.analysis_text.setPlainText(
                    self._tr("analysis_ready")
                )

        print(
            "[AI Assistant] Language:",
            language,
        )

    # ======================================================
    # METRIC CARD
    # ======================================================

    def _create_metric_card(
        self,
        name: str,
        value: str,
    ) -> dict:

        frame = QFrame()

        frame.setStyleSheet(
            """
            QFrame {
                background-color: #171b22;
                border: 1px solid #252b35;
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            15,
            14,
            15,
            14,
        )

        name_label = QLabel(
            name
        )

        name_label.setStyleSheet(
            """
            QLabel {
                color: #8e99a8;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
            """
        )

        value_label = QLabel(
            value
        )

        value_label.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Bold,
            )
        )

        value_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            """
        )

        layout.addWidget(
            name_label
        )

        layout.addWidget(
            value_label
        )

        return {
            "frame": frame,
            "value": value_label,
        }

    # ======================================================
    # THEME
    # ======================================================

    def set_theme(
        self,
        light: bool,
    ):
        """Apply a complete light/dark theme."""

        if light:

            self.setStyleSheet(
                "QWidget { background:#eef3f8; color:#172033; }"
            )

            self.status_card.setStyleSheet(
                """
                QFrame#StatusCard {
                    background:#ffffff;
                    border:1px solid #d6e0ea;
                    border-radius:14px;
                }
                """
            )

            self.title_label.setStyleSheet(
                "color:#172033;background:transparent;"
            )

            self.subtitle_label.setStyleSheet(
                "color:#64748b;font-size:14px;background:transparent;"
            )

            self.status_label.setStyleSheet(
                "color:#172033;background:transparent;"
            )

            self.user_label.setStyleSheet(
                "color:#64748b;font-size:13px;background:transparent;"
            )

            self.message_label.setStyleSheet(
                "color:#172033;font-size:14px;"
                "padding-top:8px;background:transparent;"
            )

            self.analysis_title_label.setStyleSheet(
                "color:#172033;background:transparent;"
            )

            self.analysis_text.setStyleSheet(
                """
                QTextEdit {
                    background:#ffffff;
                    color:#172033;
                    border:1px solid #d6e0ea;
                    border-radius:12px;
                    padding:12px;
                    font-size:14px;
                }
                """
            )

            self.analyze_button.setStyleSheet(
                """
                QPushButton {
                    background:#168cff;
                    color:#ffffff;
                    border:none;
                    border-radius:10px;
                    padding:10px 20px;
                    font-size:14px;
                    font-weight:600;
                }

                QPushButton:hover {
                    background:#2698ff;
                    color:#ffffff;
                }

                QPushButton:pressed {
                    background:#0f75d5;
                    color:#ffffff;
                }

                QPushButton:disabled {
                    background:#cbd5e1;
                    color:#64748b;
                }
                """
            )

            for card in (
                self.cpu_card,
                self.ram_card,
                self.disk_card,
                self.gpu_card,
            ):

                card["frame"].setStyleSheet(
                    """
                    QFrame {
                        background:#ffffff;
                        border:1px solid #d6e0ea;
                        border-radius:12px;
                    }
                    """
                )

                card["value"].setStyleSheet(
                    "color:#172033;background:transparent;"
                )

                for label in card["frame"].findChildren(QLabel):

                    if label is not card["value"]:

                        label.setStyleSheet(
                            "color:#64748b;"
                            "font-size:12px;"
                            "font-weight:600;"
                            "background:transparent;"
                        )

        else:

            self.setStyleSheet(
                "QWidget { background:#050b18; color:#f4f7ff; }"
            )

            self.title_label.setStyleSheet(
                "color:#ffffff;background:transparent;"
            )

            self.subtitle_label.setStyleSheet(
                "color:#9aa4b2;font-size:14px;background:transparent;"
            )

            self.status_card.setStyleSheet(
                """
                QFrame#StatusCard {
                    background:#171b22;
                    border:1px solid #252b35;
                    border-radius:14px;
                }
                """
            )

            self.status_label.setStyleSheet(
                "color:#ffffff;background:transparent;"
            )

            self.user_label.setStyleSheet(
                "color:#9aa4b2;font-size:13px;background:transparent;"
            )

            self.message_label.setStyleSheet(
                "color:#d7dce3;font-size:14px;"
                "padding-top:8px;background:transparent;"
            )

            self.analysis_title_label.setStyleSheet(
                "color:#ffffff;background:transparent;"
            )

            self.analysis_text.setStyleSheet(
                """
                QTextEdit {
                    background:#11151b;
                    color:#d7dce3;
                    border:1px solid #252b35;
                    border-radius:12px;
                    padding:12px;
                    font-size:14px;
                }
                """
            )

            self.analyze_button.setStyleSheet(
                """
                QPushButton {
                    background:#2563eb;
                    color:white;
                    border:none;
                    border-radius:10px;
                    padding:10px 20px;
                    font-size:14px;
                    font-weight:600;
                }

                QPushButton:hover {
                    background:#3474f0;
                }

                QPushButton:pressed {
                    background:#1d4ed8;
                }

                QPushButton:disabled {
                    background:#263246;
                    color:#788397;
                }
                """
            )

            for card in (
                self.cpu_card,
                self.ram_card,
                self.disk_card,
                self.gpu_card,
            ):

                card["frame"].setStyleSheet(
                    """
                    QFrame {
                        background:#171b22;
                        border:1px solid #252b35;
                        border-radius:12px;
                    }
                    """
                )

                card["value"].setStyleSheet(
                    "color:#ffffff;background:transparent;"
                )

                for label in card["frame"].findChildren(QLabel):

                    if label is not card["value"]:

                        label.setStyleSheet(
                            "color:#8e99a8;"
                            "font-size:12px;"
                            "font-weight:600;"
                            "background:transparent;"
                        )

    # ======================================================
    # START ANALYSIS
    # ======================================================

    def start_analysis(self):

        # --------------------------------------------------
        # PREVENT DUPLICATE ANALYSIS
        # --------------------------------------------------

        if self.worker is not None:

            try:

                if self.worker.isRunning():
                    return

            except RuntimeError:

                self.worker = None

        # --------------------------------------------------
        # UI
        # --------------------------------------------------

        self.analyze_button.setEnabled(
            False
        )

        self.analyze_button.setText(
            self._tr("analyzing")
        )

        self.progress.setVisible(
            True
        )

        self.status_label.setText(
            self._tr("analysis_running")
        )

        self.message_label.setText(
            self._tr("collecting")
        )

        self.analysis_text.setPlainText(
            self._tr("analysis_system_running")
        )

        # --------------------------------------------------
        # CREATE WORKER
        # --------------------------------------------------

        self.worker = AIWorker()

        self.worker.result_ready.connect(
            self.on_analysis_finished
        )

        self.worker.error.connect(
            self.on_analysis_error
        )

        self.worker.finished.connect(
            self._clear_worker_reference
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker.start()

    # ======================================================
    # CLEAR WORKER REFERENCE
    # ======================================================

    def _clear_worker_reference(self):

        self.worker = None

    # ======================================================
    # ANALYSIS FINISHED
    # ======================================================

    def on_analysis_finished(
        self,
        result: dict,
    ):

        self.analyze_button.setEnabled(
            True
        )

        self.analyze_button.setText(
            self._tr("analyze")
        )

        self.progress.setVisible(
            False
        )

        username = result.get(
            "username",
            "Пользователь",
        )

        self.user_label.setText(
            self._tr(
                "user",
                username=username,
            )
        )

        status = result.get(
            "status",
            "good",
        )

        message = result.get(
            "message",
            self._tr("analysis_finished"),
        )

        status_names = {
            "good": self._tr("system_good"),
            "attention": self._tr("system_attention"),
            "critical": self._tr("system_critical"),
        }

        self.status_label.setText(
            status_names.get(
                status,
                self._tr("system_state"),
            )
        )

        self.message_label.setText(
            message
        )

        # --------------------------------------------------
        # DATA
        # --------------------------------------------------

        data = result.get(
            "data",
            {},
        )

        cpu = data.get(
            "cpu",
            {},
        )

        ram = data.get(
            "ram",
            {},
        )

        disk = data.get(
            "disk",
            {},
        )

        gpu = data.get(
            "gpu",
            {},
        )

        # --------------------------------------------------
        # METRICS
        # --------------------------------------------------

        self.cpu_card["value"].setText(
            self._format_percent(
                cpu.get("usage")
            )
        )

        self.ram_card["value"].setText(
            self._format_percent(
                ram.get("usage")
            )
        )

        self.disk_card["value"].setText(
            self._format_percent(
                disk.get("usage")
            )
        )

        gpu_usage = gpu.get(
            "usage"
        )

        if gpu_usage is None:

            self.gpu_card["value"].setText(
                "N/A"
            )

        else:

            self.gpu_card["value"].setText(
                self._format_percent(
                    gpu_usage
                )
            )

        self._display_analysis(
            result
        )

    # ======================================================
    # DISPLAY ANALYSIS
    # ======================================================

    def _display_analysis(
        self,
        result: dict,
    ):

        lines = []

        status = result.get(
            "status",
            "good",
        )

        message = result.get(
            "message",
            "",
        )

        lines.append(
            self._tr(
                "state",
                status=status,
            )
        )

        lines.append("")

        if message:
            lines.append(
                message
            )

        lines.append("")

        # --------------------------------------------------
        # DIAGNOSTICS
        # --------------------------------------------------

        analysis = result.get(
            "analysis",
            {},
        )

        diagnostics = analysis.get(
            "diagnostics",
            {},
        )

        problem_count = diagnostics.get(
            "problem_count",
            0,
        )

        recovered_count = len(
            diagnostics.get(
                "recovered",
                [],
            )
            or []
        )

        lines.append(
            self._tr(
                "problems",
                count=problem_count,
            )
        )

        lines.append(
            self._tr(
                "recovered",
                count=recovered_count,
            )
        )

        # --------------------------------------------------
        # PROBLEMS
        # --------------------------------------------------

        problems = diagnostics.get(
            "problems",
            [],
        )

        if problems:

            lines.append("")

            lines.append(
                self._tr(
                    "recommendations_system"
                )
            )

            for problem in problems[:5]:

                if isinstance(
                    problem,
                    dict,
                ):

                    problem_message = problem.get(
                        "message",
                        self._tr("possible_causes"),
                    )

                    lines.append(
                        f"• {problem_message}"
                    )

        # --------------------------------------------------
        # RECOMMENDATIONS
        # --------------------------------------------------

        recommendations = result.get(
            "recommendations",
            [],
        )

        if recommendations:

            lines.append("")

            lines.append(
                self._tr(
                    "recommendations_ai"
                )
            )

            for recommendation in recommendations[:5]:

                if not isinstance(
                    recommendation,
                    dict,
                ):
                    continue

                title = recommendation.get(
                    "title",
                    self._tr("recommendation"),
                )

                recommendation_message = recommendation.get(
                    "message",
                    "",
                )

                lines.append(
                    f"• {title}: {recommendation_message}"
                )

        # --------------------------------------------------
        # TIMING
        # --------------------------------------------------

        analysis_time = analysis.get(
            "analysis_time",
            0,
        )

        try:

            analysis_time = float(
                analysis_time
            )

        except (
            TypeError,
            ValueError,
        ):

            analysis_time = 0.0

        lines.append("")

        lines.append(
            self._tr(
                "analysis_time",
                time=analysis_time,
            )
        )

        self.analysis_text.setPlainText(
            "\n".join(lines)
        )

    # ======================================================
    # ERROR
    # ======================================================

    def on_analysis_error(
        self,
        message: str,
    ):

        self.analyze_button.setEnabled(
            True
        )

        self.analyze_button.setText(
            self._tr("analyze")
        )

        self.progress.setVisible(
            False
        )

        self.status_label.setText(
            self._tr("error")
        )

        self.message_label.setText(
            self._tr("error_message")
        )

        self.analysis_text.setPlainText(
            self._tr("error_details")
            + "\n\n"
            + str(message)
        )

    # ======================================================
    # FORMAT
    # ======================================================

    @staticmethod
    def _format_percent(
        value,
    ) -> str:

        if value is None:
            return "N/A"

        try:

            return f"{float(value):.0f}%"

        except (
            TypeError,
            ValueError,
        ):

            return "N/A"

    # ======================================================
    # SHUTDOWN
    # ======================================================

    def shutdown(
        self,
        timeout=15000,
    ):

        print(
            "[AI Assistant] Shutdown started"
        )

        worker = self.worker

        if worker is None:

            print(
                "[AI Assistant] No active worker"
            )

            return True

        try:

            if worker.isRunning():

                print(
                    "[AI Assistant] Stopping AIWorker..."
                )

                result = worker.stop(
                    timeout=timeout
                )

                if result:

                    print(
                        "[AI Assistant] AIWorker stopped"
                    )

                else:

                    print(
                        "[AI Assistant] WARNING: "
                        "AIWorker did not stop"
                    )

                return result

        except RuntimeError:

            self.worker = None

            return True

        self.worker = None

        return True