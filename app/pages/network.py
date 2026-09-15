import base64
import ctypes
import json
import locale
import os
import re
import socket
import subprocess
import time

import psutil

from PySide6.QtCore import Qt, QTimer, QProcess
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QPushButton,
)


class NetworkPage(QWidget):
    """
    Страница сетевых интерфейсов.

    Показывает:
        - Wi-Fi
        - Ethernet
        - Bluetooth
        - Loopback
        - другие интерфейсы

    Bluetooth:
        - определяет физический Bluetooth-адаптер;
        - получает InstanceId;
        - получает MAC;
        - показывает реальное состояние;
        - позволяет включать / выключать физический адаптер;
        - работает с уже отключённым адаптером;
        - не запускает UAC при каждом нажатии.
    """

    # Bluetooth discovery is relatively expensive (CIM/PowerShell + ConfigMgr).
    # Keep it cached so the 3-5s UI refresh does not repeatedly hit Windows PnP.
    BLUETOOTH_DISCOVERY_TTL = 10.0
    SUPPORTED_LANGUAGES = ("ru", "uk", "en", "de", "it", "es", "fr")

    TRANSLATIONS = {
        "network": {
            "ru": "\u0421\u0435\u0442\u044c",
            "uk": "\u041c\u0435\u0440\u0435\u0436\u0430",
            "en": "Network",
            "de": "Netzwerk",
            "it": "Rete",
            "es": "Red",
            "fr": "R\u00e9seau",
        },
        "subtitle": {
            "ru": "\u0421\u0435\u0442\u0435\u0432\u044b\u0435 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u044b \u0438 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435",
            "uk": "\u041c\u0435\u0440\u0435\u0436\u0435\u0432\u0456 \u0456\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0438 \u0442\u0430 \u043f\u0456\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043d\u044f",
            "en": "Network interfaces and connectivity",
            "de": "Netzwerkschnittstellen und Verbindung",
            "it": "Interfacce di rete e connettivit\u00e0",
            "es": "Interfaces de red y conectividad",
            "fr": "Interfaces r\u00e9seau et connectivit\u00e9",
        },
        "refresh": {
            "ru": "\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c",
            "uk": "\u041e\u043d\u043e\u0432\u0438\u0442\u0438",
            "en": "Refresh",
            "de": "Aktualisieren",
            "it": "Aggiorna",
            "es": "Actualizar",
            "fr": "Actualiser",
        },
        "wifi": {
            "ru": "Wi-Fi", "uk": "Wi-Fi", "en": "Wi-Fi",
            "de": "Wi-Fi", "it": "Wi-Fi", "es": "Wi-Fi", "fr": "Wi-Fi",
        },
        "bluetooth": {
            "ru": "Bluetooth", "uk": "Bluetooth", "en": "Bluetooth",
            "de": "Bluetooth", "it": "Bluetooth", "es": "Bluetooth", "fr": "Bluetooth",
        },
        "ethernet": {
            "ru": "Ethernet", "uk": "Ethernet", "en": "Ethernet",
            "de": "Ethernet", "it": "Ethernet", "es": "Ethernet", "fr": "Ethernet",
        },
        "loopback": {
            "ru": "Loopback", "uk": "Loopback", "en": "Loopback",
            "de": "Loopback", "it": "Loopback", "es": "Loopback", "fr": "Loopback",
        },
        "other": {
            "ru": "\u0414\u0440\u0443\u0433\u043e\u0435",
            "uk": "\u0406\u043d\u0448\u0435",
            "en": "Other",
            "de": "Andere",
            "it": "Altro",
            "es": "Otro",
            "fr": "Autre",
        },
        "ipv4": {
            "ru": "IPv4", "uk": "IPv4", "en": "IPv4",
            "de": "IPv4", "it": "IPv4", "es": "IPv4", "fr": "IPv4",
        },
        "mac": {
            "ru": "MAC", "uk": "MAC", "en": "MAC",
            "de": "MAC", "it": "MAC", "es": "MAC", "fr": "MAC",
        },
        "unknown": {
            "ru": "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e",
            "uk": "\u041d\u0435\u0432\u0456\u0434\u043e\u043c\u043e",
            "en": "Unknown",
            "de": "Unbekannt",
            "it": "Sconosciuto",
            "es": "Desconocido",
            "fr": "Inconnu",
        },
        "enabled": {
            "ru": "\u0412\u043a\u043b\u044e\u0447\u0451\u043d",
            "uk": "\u0423\u0432\u0456\u043c\u043a\u043d\u0435\u043d\u043e",
            "en": "Enabled",
            "de": "Aktiviert",
            "it": "Attivato",
            "es": "Activado",
            "fr": "Activ\u00e9",
        },
        "disabled": {
            "ru": "\u0412\u044b\u043a\u043b\u044e\u0447\u0435\u043d",
            "uk": "\u0412\u0438\u043c\u043a\u043d\u0435\u043d\u043e",
            "en": "Disabled",
            "de": "Deaktiviert",
            "it": "Disattivato",
            "es": "Desactivado",
            "fr": "D\u00e9sactiv\u00e9",
        },
        "connected": {
            "ru": "\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0451\u043d",
            "uk": "\u041f\u0456\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e",
            "en": "Connected",
            "de": "Verbunden",
            "it": "Connesso",
            "es": "Conectado",
            "fr": "Connect\u00e9",
        },
        "disconnected": {
            "ru": "\u041e\u0442\u043a\u043b\u044e\u0447\u0451\u043d",
            "uk": "\u0412\u0456\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e",
            "en": "Disconnected",
            "de": "Getrennt",
            "it": "Disconnesso",
            "es": "Desconectado",
            "fr": "D\u00e9connect\u00e9",
        },
        "wait": {
            "ru": "\u041f\u043e\u0434\u043e\u0436\u0434\u0438\u0442\u0435...",
            "uk": "\u0417\u0430\u0447\u0435\u043a\u0430\u0439\u0442\u0435...",
            "en": "Please wait...",
            "de": "Bitte warten...",
            "it": "Attendere...",
            "es": "Espere...",
            "fr": "Veuillez patienter...",
        },
        "enable": {
            "ru": "\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c",
            "uk": "\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438",
            "en": "Enable",
            "de": "Aktivieren",
            "it": "Attiva",
            "es": "Activar",
            "fr": "Activer",
        },
        "disable": {
            "ru": "\u0412\u044b\u043a\u043b\u044e\u0447\u0438\u0442\u044c",
            "uk": "\u0412\u0438\u043c\u043a\u043d\u0443\u0442\u0438",
            "en": "Disable",
            "de": "Deaktivieren",
            "it": "Disattiva",
            "es": "Desactivar",
            "fr": "D\u00e9sactiver",
        },
        "adapter_not_found": {
            "ru": "\u0424\u0438\u0437\u0438\u0447\u0435\u0441\u043a\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d",
            "uk": "\u0424\u0456\u0437\u0438\u0447\u043d\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440 \u043d\u0435 \u0437\u043d\u0430\u0439\u0434\u0435\u043d\u043e",
            "en": "Physical Bluetooth adapter not found",
            "de": "Physischer Bluetooth-Adapter wurde nicht gefunden",
            "it": "Adattatore Bluetooth fisico non trovato",
            "es": "No se encontr\u00f3 el adaptador Bluetooth f\u00edsico",
            "fr": "Adaptateur Bluetooth physique introuvable",
        },
        "interfaces_not_found": {
            "ru": "\u0421\u0435\u0442\u0435\u0432\u044b\u0435 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u044b \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b",
            "uk": "\u041c\u0435\u0440\u0435\u0436\u0435\u0432\u0456 \u0456\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0438 \u043d\u0435 \u0437\u043d\u0430\u0439\u0434\u0435\u043d\u043e",
            "en": "No network interfaces found",
            "de": "Keine Netzwerkschnittstellen gefunden",
            "it": "Nessuna interfaccia di rete trovata",
            "es": "No se encontraron interfaces de red",
            "fr": "Aucune interface r\u00e9seau trouv\u00e9e",
        },
        "not_determined": {
            "ru": "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d",
            "uk": "\u041d\u0435 \u0432\u0438\u0437\u043d\u0430\u0447\u0435\u043d\u043e",
            "en": "Not determined",
            "de": "Nicht bestimmt",
            "it": "Non determinato",
            "es": "No determinado",
            "fr": "Non d\u00e9termin\u00e9",
        },
        "unavailable": {
            "ru": "\u041d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e",
            "uk": "\u041d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e",
            "en": "Unavailable",
            "de": "Nicht verf\u00fcgbar",
            "it": "Non disponibile",
            "es": "No disponible",
            "fr": "Indisponible",
        },
        "retry": {
            "ru": "\u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u044c",
            "uk": "\u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u0438",
            "en": "Retry",
            "de": "Wiederholen",
            "it": "Riprova",
            "es": "Reintentar",
            "fr": "R\u00e9essayer",
        },
        "tooltip_wait": {
            "ru": "\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435 \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u044f Bluetooth...",
            "uk": "\u0417\u043c\u0456\u043d\u0430 \u0441\u0442\u0430\u043d\u0443 Bluetooth...",
            "en": "Changing Bluetooth state...",
            "de": "Bluetooth-Status wird ge\u00e4ndert...",
            "it": "Modifica dello stato Bluetooth...",
            "es": "Cambiando el estado de Bluetooth...",
            "fr": "Modification de l\u2019\u00e9tat du Bluetooth...",
        },
        "tooltip_adapter": {
            "ru": "\u0424\u0438\u0437\u0438\u0447\u0435\u0441\u043a\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d",
            "uk": "\u0424\u0456\u0437\u0438\u0447\u043d\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440 \u043d\u0435 \u0437\u043d\u0430\u0439\u0434\u0435\u043d\u043e",
            "en": "Physical Bluetooth adapter not found",
            "de": "Physischer Bluetooth-Adapter wurde nicht gefunden",
            "it": "Adattatore Bluetooth fisico non trovato",
            "es": "No se encontr\u00f3 el adaptador Bluetooth f\u00edsico",
            "fr": "Adaptateur Bluetooth physique introuvable",
        },
        "tooltip_retry": {
            "ru": "\u041f\u043e\u0432\u0442\u043e\u0440\u043d\u043e \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 Bluetooth",
            "uk": "\u041f\u043e\u0432\u0442\u043e\u0440\u043d\u043e \u0432\u0438\u0437\u043d\u0430\u0447\u0438\u0442\u0438 \u0441\u0442\u0430\u043d Bluetooth",
            "en": "Retry Bluetooth detection",
            "de": "Bluetooth-Erkennung wiederholen",
            "it": "Ripetere il rilevamento Bluetooth",
            "es": "Repetir detecci\u00f3n de Bluetooth",
            "fr": "Relancer la d\u00e9tection de Bluetooth",
        },
        "tooltip_disable": {
            "ru": "\u0412\u044b\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0444\u0438\u0437\u0438\u0447\u0435\u0441\u043a\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440",
            "uk": "\u0412\u0438\u043c\u043a\u043d\u0443\u0442\u0438 \u0444\u0456\u0437\u0438\u0447\u043d\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440",
            "en": "Disable physical Bluetooth adapter",
            "de": "Physischen Bluetooth-Adapter deaktivieren",
            "it": "Disattiva adattatore Bluetooth fisico",
            "es": "Desactivar adaptador Bluetooth f\u00edsico",
            "fr": "D\u00e9sactiver l\u2019adaptateur Bluetooth physique",
        },
        "tooltip_enable": {
            "ru": "\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0444\u0438\u0437\u0438\u0447\u0435\u0441\u043a\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440",
            "uk": "\u0423\u0432\u0456\u043c\u043a\u043d\u0443\u0442\u0438 \u0444\u0456\u0437\u0438\u0447\u043d\u0438\u0439 Bluetooth-\u0430\u0434\u0430\u043f\u0442\u0435\u0440",
            "en": "Enable physical Bluetooth adapter",
            "de": "Physischen Bluetooth-Adapter aktivieren",
            "it": "Attiva adattatore Bluetooth fisico",
            "es": "Activar adaptador Bluetooth f\u00edsico",
            "fr": "Activer l\u2019adaptateur Bluetooth physique",
        },
    }

    BLUETOOTH_CACHE_TTL = 5.0
    BLUETOOTH_MAC_TTL = 60.0
    BLUETOOTH_TIMEOUT = 8.0
    BLUETOOTH_CONTROL_TIMEOUT = 20.0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("NetworkPage")

        # =========================================================
        # LANGUAGE
        # =========================================================
        self.ui_language = "ru"

        # =========================================================
        # STATE
        # =========================================================

        self._is_shutting_down = False

        self._bluetooth_instance_id = None
        self._bluetooth_name = "Bluetooth"
        self._bluetooth_discovery_time = 0.0
        self._bluetooth_last_error = None

        self._bluetooth_state_cache = None
        self._bluetooth_cache_time = 0.0

        self._bluetooth_mac_cache = None
        self._bluetooth_mac_time = 0.0

        self._bluetooth_control_in_progress = False

        self._bluetooth_process = None
        self._bluetooth_target_state = None
        self._bluetooth_instance_id_for_control = None
        self._bluetooth_verify_attempts = 0

        self._bluetooth_watchdog_token = 0
        self._bluetooth_last_log_signature = None
        self._bluetooth_last_log_error = None
        self._last_interfaces_signature = None

        # =========================================================
        # MAIN LAYOUT
        # =========================================================

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        self.main_layout.setSpacing(15)

        # =========================================================
        # HEADER
        # =========================================================

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title_label = QLabel("Сеть")
        self.title_label.setObjectName("NetworkTitle")
        self.title_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: 700;
            """
        )

        self.subtitle_label = QLabel(
            "Сетевые интерфейсы и подключение"
        )
        self.subtitle_label.setStyleSheet(
            """
            font-size: 13px;
            color: #888888;
            """
        )

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)
        header_layout.addStretch()

        self.refresh_button = QPushButton(self._tr("refresh"))
        self.refresh_button.setCursor(
            Qt.PointingHandCursor
        )
        self.refresh_button.setMinimumHeight(34)

        self.refresh_button.clicked.connect(
            lambda: self.update_network(force=True)
        )

        header_layout.addWidget(
            self.refresh_button
        )

        self.main_layout.addLayout(
            header_layout
        )

        # =========================================================
        # SCROLL AREA
        # =========================================================

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(
            QFrame.NoFrame
        )

        self.cards_container = QWidget()

        self.cards_layout = QVBoxLayout(
            self.cards_container
        )

        self.cards_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.cards_container
        )

        self.main_layout.addWidget(
            self.scroll_area
        )

        # =========================================================
        # TIMER
        # =========================================================

        self.timer = QTimer(self)
        self.timer.setInterval(5000)

        self.timer.timeout.connect(
            lambda: self.update_network(force=False)
        )

        self.timer.start()

        # =========================================================
        # FIRST LOAD
        # =========================================================

        QTimer.singleShot(
            100,
            lambda: self.update_network(force=False),
        )

    # =============================================================
    # ADMIN CHECK
    # =============================================================

    def _is_admin(self):
        """
        Проверяет, запущена ли программа с правами администратора.
        """

        if os.name != "nt":
            return False

        try:
            return bool(
                ctypes.windll.shell32.IsUserAnAdmin()
            )
        except Exception as e:
            print(
                "[Network] Admin check error:",
                repr(e),
            )
            return False

    # =============================================================
    # LANGUAGE
    # =============================================================

    def _tr(self, key):
        lang = getattr(self, "ui_language", "ru")

        if lang not in self.SUPPORTED_LANGUAGES:
            lang = "ru"

        return self.TRANSLATIONS.get(
            key,
            {}
        ).get(
            lang,
            key
        )

    def set_language(self, language):
        import traceback

        print("\n" + "=" * 80)
        print("[LANG][NETWORK] NetworkPage.set_language()")
        print(
            "[LANG][NETWORK] requested =",
            repr(language)
        )
        print(
            "[LANG][NETWORK] previous  =",
            repr(getattr(self, "ui_language", None))
        )
        print("[LANG][NETWORK] CALL STACK:")
        print(
            "".join(
                traceback.format_stack(limit=12)
            )
        )
        print("=" * 80)

        language = str(language or "ru")

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        if hasattr(self, "title_label"):
            self.title_label.setText(
                self._tr("network")
            )

        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(
                self._tr("subtitle")
            )

        if hasattr(self, "refresh_button"):
            self.refresh_button.setText(
                self._tr("refresh")
            )

        print(
            "[NetworkPage] Language:",
            language
        )

        # Обновляем карточки после смены языка.
        if not getattr(
            self,
            "_is_shutting_down",
            False
        ):
            try:
                self.update_network(
                    force=True
                )
            except Exception as exc:
                print(
                    "[NetworkPage] Language refresh error:",
                    repr(exc)
                )

    # =============================================================
    # POWERSHELL
    # =============================================================

    def _run_powershell(
        self,
        script,
        timeout=None,
    ):
        if self._is_shutting_down:
            return None

        if timeout is None:
            timeout = self.BLUETOOTH_CONTROL_TIMEOUT

        try:
            encoded = base64.b64encode(
                script.encode("utf-16le")
            ).decode("ascii")

            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-EncodedCommand",
                    encoded,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            return {
                "returncode": result.returncode,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
            }

        except subprocess.TimeoutExpired:
            print(
                "[Network] PowerShell timeout."
            )
            return None

        except Exception as e:
            print(
                "[Network] PowerShell error:",
                repr(e),
            )
            return None

    # =============================================================
    # FIND PHYSICAL BLUETOOTH ADAPTER
    # =============================================================

    def _find_bluetooth_instance_id(self):
        """
        Ищет физический Bluetooth USB-адаптер.

        Для данного компьютера ожидается:

            Qualcomm Atheros QCA9377 Bluetooth 4.1

        InstanceId:

            USB\\VID_0CF3&PID_E360\\...

        """

        if self._is_shutting_down:
            return self._bluetooth_instance_id

        now = time.monotonic()
        if (
            self._bluetooth_instance_id
            and (now - self._bluetooth_discovery_time)
            < self.BLUETOOTH_DISCOVERY_TTL
        ):
            return self._bluetooth_instance_id

        script = r'''
$ErrorActionPreference = "SilentlyContinue"

$devices = @(
    Get-CimInstance Win32_PnPEntity |
    Where-Object {
        $_.PNPDeviceID
    } |
    Select-Object Name, Status, PNPDeviceID, Service, ConfigManagerErrorCode
)

$devices | ConvertTo-Json -Compress
'''

        try:
            result = self._run_powershell(
                script,
                timeout=self.BLUETOOTH_TIMEOUT,
            )

            if not result:
                if self._bluetooth_last_error != "pnp_no_result":
                    print("[Bluetooth] PnP search returned no result.")
                    self._bluetooth_last_error = "pnp_no_result"
                return self._bluetooth_instance_id

            if result.get("returncode", -1) != 0:
                error_text = str(result.get("stderr", "") or "").strip()
                signature = ("pnp_failed", error_text)
                if self._bluetooth_last_error != signature:
                    print("[Bluetooth] PnP search failed:", error_text)
                    self._bluetooth_last_error = signature
                return self._bluetooth_instance_id

            output = (
                result.get("stdout", "") or ""
            ).strip()

            if not output:
                if self._bluetooth_last_error != "pnp_empty":
                    print("[Bluetooth] PnP output is empty.")
                    self._bluetooth_last_error = "pnp_empty"
                return self._bluetooth_instance_id

            data = json.loads(output)

            if isinstance(data, dict):
                data = [data]

            candidates = []

            for dev in data:
                if not isinstance(dev, dict):
                    continue

                name = str(
                    dev.get("Name") or ""
                )

                pnp_id = str(
                    dev.get("PNPDeviceID") or ""
                )

                service = str(
                    dev.get("Service") or ""
                )

                status = str(
                    dev.get("Status") or ""
                )

                error_code = dev.get(
                    "ConfigManagerErrorCode"
                )

                pnp_upper = pnp_id.upper()
                name_upper = name.upper()
                service_upper = service.upper()

                # -------------------------------------------------
                # Только USB
                # -------------------------------------------------

                if not pnp_upper.startswith("USB\\"):
                    continue

                # -------------------------------------------------
                # Исключаем виртуальные Bluetooth устройства
                # -------------------------------------------------

                if (
                    pnp_upper.startswith("BTH\\")
                    or pnp_upper.startswith("BTHENUM\\")
                    or pnp_upper.startswith("SWD\\RADIO\\")
                    or "BTHPAN" in pnp_upper
                    or "BTHLE" in pnp_upper
                    or "BTHBRB" in pnp_upper
                ):
                    continue

                # -------------------------------------------------
                # Физический Bluetooth
                # -------------------------------------------------

                is_bluetooth = (
                    service_upper == "BTHUSB"
                    or "BLUETOOTH" in name_upper
                    or "QCA9377" in name_upper
                    or "QUALCOMM" in name_upper
                )

                if not is_bluetooth:
                    continue

                candidates.append(
                    {
                        "name": name,
                        "pnp_id": pnp_id,
                        "service": service,
                        "status": status,
                        "error": error_code,
                    }
                )

            if not candidates:
                self._bluetooth_discovery_time = time.monotonic()
                if self._bluetooth_last_log_error != "not_found":
                    print("[Bluetooth] Physical adapter not found.")
                    self._bluetooth_last_log_error = "not_found"
                return self._bluetooth_instance_id

            # -----------------------------------------------------
            # Приоритет Qualcomm / QCA9377
            # -----------------------------------------------------

            selected = None

            for item in candidates:
                text = (
                    item["name"]
                    + " "
                    + item["pnp_id"]
                    + " "
                    + item["service"]
                ).upper()

                if (
                    "QCA9377" in text
                    or "QUALCOMM" in text
                ):
                    selected = item
                    break

            if selected is None:
                selected = candidates[0]

            new_instance_id = selected["pnp_id"]
            new_name = selected["name"] or "Bluetooth"
            changed = (
                new_instance_id != self._bluetooth_instance_id
                or new_name != self._bluetooth_name
            )

            self._bluetooth_instance_id = new_instance_id
            self._bluetooth_name = new_name
            self._bluetooth_discovery_time = time.monotonic()
            self._bluetooth_last_log_error = None

            if changed:
                print(
                    "[Bluetooth] Adapter:",
                    self._bluetooth_name,
                    "| InstanceId:",
                    self._bluetooth_instance_id,
                )

            return self._bluetooth_instance_id

        except json.JSONDecodeError as e:
            print(
                "[Bluetooth] JSON error:",
                repr(e),
            )
            return self._bluetooth_instance_id

        except Exception as e:
            print(
                "[Bluetooth] Find adapter error:",
                repr(e),
            )
            return self._bluetooth_instance_id

    # =============================================================
    # BLUETOOTH STATE
    # =============================================================

    def _get_bluetooth_state(
        self,
        instance_id=None,
        force=False,
    ):
        """
        Получает реальное состояние физического Bluetooth
        через Windows Configuration Manager.

        True  = включён
        False = выключен
        None  = неизвестно
        """

        if self._is_shutting_down:
            return None

        if instance_id:
            instance_id = str(
                instance_id
            ).strip()
        else:
            instance_id = (
                self._bluetooth_instance_id
            )

        if not instance_id:
            return None

        # ---------------------------------------------------------
        # CACHE
        # ---------------------------------------------------------

        now = time.monotonic()

        if not force:
            if (
                self._bluetooth_state_cache is not None
                and (
                    now
                    - self._bluetooth_cache_time
                    < self.BLUETOOTH_CACHE_TTL
                )
            ):
                return self._bluetooth_state_cache

        # ---------------------------------------------------------
        # Configuration Manager
        # ---------------------------------------------------------

        try:
            cfgmgr32 = ctypes.WinDLL(
                "cfgmgr32.dll"
            )

            CM_Locate_DevNodeW = (
                cfgmgr32.CM_Locate_DevNodeW
            )

            CM_Locate_DevNodeW.argtypes = [
                ctypes.POINTER(ctypes.c_ulong),
                ctypes.c_wchar_p,
                ctypes.c_ulong,
            ]

            CM_Locate_DevNodeW.restype = (
                ctypes.c_ulong
            )

            CM_Get_DevNode_Status = (
                cfgmgr32.CM_Get_DevNode_Status
            )

            CM_Get_DevNode_Status.argtypes = [
                ctypes.POINTER(ctypes.c_ulong),
                ctypes.POINTER(ctypes.c_ulong),
                ctypes.c_ulong,
                ctypes.c_ulong,
            ]

            CM_Get_DevNode_Status.restype = (
                ctypes.c_ulong
            )

            devinst = ctypes.c_ulong(0)

            locate_result = CM_Locate_DevNodeW(
                ctypes.byref(devinst),
                instance_id,
                0,
            )

            if locate_result != 0:
                self._bluetooth_state_cache = None
                self._bluetooth_cache_time = 0.0
                return None

            status = ctypes.c_ulong(0)
            problem = ctypes.c_ulong(0)

            status_result = CM_Get_DevNode_Status(
                ctypes.byref(status),
                ctypes.byref(problem),
                devinst,
                0,
            )

            if status_result != 0:
                self._bluetooth_state_cache = None
                self._bluetooth_cache_time = 0.0
                return None

            CM_PROB_DISABLED = 22
            DN_STARTED = 0x00000008

            # -----------------------------------------------------
            # Explicitly disabled
            # -----------------------------------------------------

            if problem.value == CM_PROB_DISABLED:
                state = False

            # -----------------------------------------------------
            # Device started
            # -----------------------------------------------------

            elif status.value & DN_STARTED:
                state = True

            # -----------------------------------------------------
            # Exists but isn't started
            # -----------------------------------------------------

            else:
                state = False

            previous = self._bluetooth_state_cache
            self._bluetooth_state_cache = state
            self._bluetooth_cache_time = time.monotonic()

            if previous != state:
                print("[Bluetooth] State changed:", state)

            return state

        except Exception as e:
            print(
                "[Bluetooth] ConfigMgr state error:",
                repr(e),
            )

            self._bluetooth_state_cache = None
            self._bluetooth_cache_time = 0.0

            return None

    # =============================================================
    # BLUETOOTH MAC
    # =============================================================

    def _get_bluetooth_address(self):
        """
        Получает MAC физического Bluetooth-радиомодуля.
        """

        if self._is_shutting_down:
            return None

        now = time.monotonic()

        if (
            self._bluetooth_mac_cache
            and (
                now - self._bluetooth_mac_time
                < self.BLUETOOTH_MAC_TTL
            )
        ):
            return self._bluetooth_mac_cache

        script = r'''
$ErrorActionPreference = "SilentlyContinue"

Get-CimInstance Win32_PnPEntity |
    Where-Object {
        $_.PNPDeviceID -like 'SWD\RADIO\BLUETOOTH_*'
    } |
    Select-Object Name, PNPDeviceID |
    ConvertTo-Json -Compress
'''

        try:
            result = self._run_powershell(
                script,
                timeout=self.BLUETOOTH_TIMEOUT,
            )

            if not result:
                return None

            if result.get("returncode", -1) != 0:
                return None

            output = (
                result.get("stdout", "") or ""
            ).strip()

            if not output:
                return None

            data = json.loads(output)

            if isinstance(data, dict):
                data = [data]

            if not isinstance(data, list):
                return None

            for item in data:
                if not isinstance(item, dict):
                    continue

                pnp_id = str(
                    item.get("PNPDeviceID") or ""
                ).strip()

                match = re.search(
                    r"BLUETOOTH_([0-9A-Fa-f]{12})",
                    pnp_id,
                    re.IGNORECASE,
                )

                if not match:
                    continue

                mac = match.group(1).upper()

                formatted_mac = ":".join(
                    mac[i:i + 2]
                    for i in range(0, 12, 2)
                )

                previous_mac = self._bluetooth_mac_cache
                self._bluetooth_mac_cache = formatted_mac
                self._bluetooth_mac_time = time.monotonic()

                if previous_mac != formatted_mac:
                    print("[Bluetooth] MAC:", formatted_mac)

                return formatted_mac

            return None

        except Exception as e:
            print(
                "[Bluetooth] MAC error:",
                repr(e),
            )
            return None

    # =============================================================
    # NETWORK INTERFACES
    # =============================================================

    def _get_network_interfaces(self):
        interfaces = []

        # =========================================================
        # NORMAL NETWORK INTERFACES
        # =========================================================

        try:
            addresses = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
        except Exception as e:
            print(
                "[Network] psutil error:",
                repr(e),
            )
            addresses = {}
            stats = {}

        try:
            for name, addr_list in addresses.items():

                name_text = str(name)

                interface_type = (
                    self._detect_interface_type(
                        name_text
                    )
                )

                if interface_type == "bluetooth":
                    continue

                ipv4 = "—"

                for addr in addr_list:
                    if (
                        getattr(
                            addr,
                            "family",
                            None,
                        )
                        == socket.AF_INET
                    ):
                        ipv4 = (
                            getattr(
                                addr,
                                "address",
                                None,
                            )
                            or "—"
                        )
                        break

                stat = stats.get(name)

                is_up = bool(
                    stat.isup
                    if stat is not None
                    else False
                )

                interfaces.append(
                    {
                        "name": name_text,
                        "type": interface_type,
                        "ipv4": ipv4,
                        "up": is_up,
                        "unknown": False,
                        "instance_id": None,
                        "bluetooth_address": "—",
                    }
                )

        except Exception as e:
            print(
                "[Network] Interface enumeration error:",
                repr(e),
            )

        # =========================================================
        # BLUETOOTH
        # =========================================================

        bluetooth_instance_id = None
        bluetooth_state = None
        bluetooth_address = None

        try:
            bluetooth_instance_id = (
                self._find_bluetooth_instance_id()
            )
        except Exception as e:
            print(
                "[Bluetooth] InstanceId error:",
                repr(e),
            )

            bluetooth_instance_id = (
                self._bluetooth_instance_id
            )

        if bluetooth_instance_id:

            try:
                bluetooth_state = (
                    self._get_bluetooth_state(
                        bluetooth_instance_id
                    )
                )
            except Exception as e:
                print(
                    "[Bluetooth] State error:",
                    repr(e),
                )

                bluetooth_state = None

        try:
            bluetooth_address = (
                self._get_bluetooth_address()
            )
        except Exception as e:
            print(
                "[Bluetooth] MAC error:",
                repr(e),
            )

        if not bluetooth_address:
            bluetooth_address = self._tr("not_determined")

        # =========================================================
        # ADD BLUETOOTH CARD
        # =========================================================

        interfaces.append(
            {
                "name": (
                    self._bluetooth_name
                    or "Bluetooth"
                ),
                "type": "bluetooth",
                "ipv4": "—",
                "up": (
                    bool(bluetooth_state)
                    if bluetooth_state is not None
                    else False
                ),
                "unknown": (
                    bluetooth_state is None
                ),
                "instance_id": (
                    bluetooth_instance_id
                    or self._bluetooth_instance_id
                ),
                "bluetooth_address":
                    bluetooth_address,
            }
        )

        bluetooth_signature = (
            self._bluetooth_name,
            bluetooth_instance_id,
            bluetooth_state,
            bluetooth_address,
        )

        # Не засоряем консоль одинаковыми сообщениями каждые 3 секунды.
        # Полная информация выводится только при изменении состояния/адаптера.
        if bluetooth_signature != self._bluetooth_last_log_signature:
            print("[Network] Bluetooth interface updated.")
            print("[Network] Bluetooth name:", self._bluetooth_name)
            print("[Network] Bluetooth InstanceId:", bluetooth_instance_id)
            print("[Network] Bluetooth state:", bluetooth_state)
            print("[Network] Bluetooth MAC:", bluetooth_address)
            self._bluetooth_last_log_signature = bluetooth_signature

        # =========================================================
        # SORT
        # =========================================================

        try:
            interfaces.sort(
                key=lambda item:
                self._type_order(
                    item["type"]
                )
            )
        except Exception as e:
            print(
                "[Network] Sort error:",
                repr(e),
            )

        return interfaces

    # =============================================================
    # UPDATE
    # =============================================================

    def update_network(self, force=False):
        if self._is_shutting_down:
            return

        # Не перерисовываем карточку во время операции.
        if self._bluetooth_control_in_progress:
            return

        try:
            # Manual refresh bypasses the normal discovery/state caches.
            if force:
                self._bluetooth_discovery_time = 0.0
                self._bluetooth_state_cache = None
                self._bluetooth_cache_time = 0.0
                self._bluetooth_mac_time = 0.0

            interfaces = self._get_network_interfaces()

            # Не перерисовываем неизменившиеся карточки каждые 5 секунд.
            signature = tuple(
                (
                    item.get("name"),
                    item.get("type"),
                    item.get("ipv4"),
                    item.get("up"),
                    item.get("unknown"),
                    item.get("instance_id"),
                    item.get("bluetooth_address"),
                )
                for item in interfaces
            )
            if signature == self._last_interfaces_signature and not force:
                return
            self._last_interfaces_signature = signature

            self._clear_cards()

            if not interfaces:
                empty = QLabel(self._tr("interfaces_not_found"))

                empty.setAlignment(
                    Qt.AlignCenter
                )

                empty.setStyleSheet(
                    """
                    color: #888888;
                    font-size: 14px;
                    padding: 40px;
                    """
                )

                self.cards_layout.insertWidget(
                    0,
                    empty,
                )

                return

            for interface in interfaces:

                card = (
                    self._create_interface_card(
                        interface
                    )
                )

                self.cards_layout.insertWidget(
                    self.cards_layout.count() - 1,
                    card,
                )

        except Exception as e:
            print(
                "[Network] update_network error:",
                repr(e),
            )

    # =============================================================
    # TYPE DETECTION
    # =============================================================

    def _detect_interface_type(self, name):

        name_lower = str(
            name or ""
        ).lower()

        if (
            "loopback" in name_lower
            or "pseudo-interface" in name_lower
            or name_lower == "lo"
        ):
            return "loopback"

        if (
            "bluetooth" in name_lower
            or "bth" in name_lower
            or "bt-" in name_lower
        ):
            return "bluetooth"

        if (
            "wi-fi" in name_lower
            or "wifi" in name_lower
            or "wireless" in name_lower
            or "wlan" in name_lower
            or "беспровод" in name_lower
        ):
            return "wifi"

        if (
            "ethernet" in name_lower
            or "lan" in name_lower
            or "local area" in name_lower
            or "локальн" in name_lower
            or "realtek" in name_lower
            or "gigabit" in name_lower
        ):
            return "ethernet"

        return "other"

    # =============================================================
    # TYPE ORDER
    # =============================================================

    def _type_order(self, interface_type):

        order = {
            "wifi": 0,
            "bluetooth": 1,
            "ethernet": 2,
            "loopback": 3,
            "other": 4,
        }

        return order.get(
            interface_type,
            99,
        )

    # =============================================================
    # CREATE CARD
    # =============================================================

    def _create_interface_card(self, interface):

        card = QFrame()
        card.setObjectName(
            "NetworkCard"
        )

        card.setMinimumHeight(110)

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            16,
            12,
            16,
            12,
        )

        layout.setSpacing(15)

        # =========================================================
        # ICON
        # =========================================================

        icon = QLabel(
            self._get_icon(
                interface["type"]
            )
        )

        icon.setFixedWidth(38)

        icon.setAlignment(
            Qt.AlignCenter
        )

        icon.setStyleSheet(
            "font-size: 25px;"
        )

        layout.addWidget(icon)

        # =========================================================
        # NAME
        # =========================================================

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        print(
            "[Network][UI] RAW INTERFACE NAME:",
            repr(interface.get("name"))
        )
        print(
            "[Network][UI] TRANSLATED INTERFACE NAME:",
            repr(self._get_interface_name(interface.get("name")))
        )

        name_label = QLabel(
            self._get_interface_name(interface["name"])
        )

        name_label.setStyleSheet(
            """
            font-size: 15px;
            font-weight: 600;
            """
        )

        type_label = QLabel(
            self._get_type_name(
                interface["type"]
            )
        )

        type_label.setStyleSheet(
            """
            font-size: 12px;
            color: #888888;
            """
        )

        info_layout.addWidget(
            name_label
        )

        info_layout.addWidget(
            type_label
        )

        # Bluetooth MAC

        if interface["type"] == "bluetooth":

            address = interface.get(
                "bluetooth_address",
                "—",
            )

            address_label = QLabel(
                f"{self._tr('mac')}: {address}"
            )

            address_label.setStyleSheet(
                """
                font-size: 11px;
                color: #777777;
                """
            )

            info_layout.addWidget(
                address_label
            )

        layout.addLayout(
            info_layout
        )

        layout.addStretch()

        # =========================================================
        # IPV4
        # =========================================================

        ip_layout = QVBoxLayout()
        ip_layout.setSpacing(3)

        ip_title = QLabel("IPv4")

        ip_title.setAlignment(
            Qt.AlignRight
        )

        self.title_label.setStyleSheet(
            """
            font-size: 11px;
            color: #888888;
            """
        )

        ip_label = QLabel(
            interface.get(
                "ipv4",
                "—",
            )
        )

        ip_label.setAlignment(
            Qt.AlignRight
        )

        ip_label.setStyleSheet(
            """
            font-size: 14px;
            font-weight: 500;
            """
        )

        ip_layout.addWidget(
            ip_title
        )

        ip_layout.addWidget(
            ip_label
        )

        layout.addLayout(
            ip_layout
        )

        # =========================================================
        # STATUS
        # =========================================================

        is_unknown = interface.get(
            "unknown",
            False,
        )

        if interface["type"] == "bluetooth":

            if is_unknown:
                status_text = self._tr('unknown')

            elif interface["up"]:
                status_text = self._tr('enabled')

            else:
                status_text = self._tr('disabled')

        else:

            if interface["up"]:
                status_text = self._tr('connected')

            else:
                status_text = self._tr('disconnected')



        status = QLabel(
            status_text
        )

        status.setAlignment(
            Qt.AlignCenter
        )

        status.setMinimumWidth(105)

        if is_unknown:

            status.setStyleSheet(
                """
                color: #d6a84f;
                font-size: 12px;
                font-weight: 600;
                """
            )

        elif interface["up"]:

            status.setStyleSheet(
                """
                color: #55c97b;
                font-size: 12px;
                font-weight: 600;
                """
            )

        else:

            status.setStyleSheet(
                """
                color: #888888;
                font-size: 12px;
                font-weight: 600;
                """
            )

        layout.addWidget(status)

            # =========================================================
        # BLUETOOTH BUTTON
        # =========================================================
        if interface["type"] == "bluetooth":

            instance_id = (
                interface.get("instance_id")
                or self._bluetooth_instance_id
            )

            bluetooth_button = QPushButton()
            bluetooth_button.setObjectName(
                "BluetoothEnableButton"
            )
            bluetooth_button.setCursor(
                Qt.PointingHandCursor
            )
            bluetooth_button.setMinimumHeight(34)
            bluetooth_button.setMinimumWidth(125)

            bluetooth_state = interface.get("up")
            is_unknown = interface.get("unknown", False)

            print(
                "[Network][UI] Bluetooth button:",
                "state=", bluetooth_state,
                "unknown=", is_unknown,
                "busy=", self._bluetooth_control_in_progress,
                "InstanceId=", instance_id,
            )

            # -----------------------------------------------------
            # ОПЕРАЦИЯ УЖЕ ИДЁТ
            # -----------------------------------------------------
            if self._bluetooth_control_in_progress:

                bluetooth_button.setText(
                    self._tr("please_wait")
                )

                bluetooth_button.setEnabled(
                    False
                )

                bluetooth_button.setToolTip(
                    "Изменение состояния Bluetooth..."
                )

            # -----------------------------------------------------
            # INSTANCE ID НЕ НАЙДЕН
            # -----------------------------------------------------
            elif not instance_id:

                bluetooth_button.setText(
                    self._tr("unavailable")
                )

                bluetooth_button.setEnabled(
                    False
                )

                bluetooth_button.setToolTip(
                    "Физический Bluetooth-адаптер не найден"
                )

            # -----------------------------------------------------
            # СОСТОЯНИЕ НЕИЗВЕСТНО
            # -----------------------------------------------------
            elif is_unknown or bluetooth_state is None:

                bluetooth_button.setText(
                    self._tr("retry")
                )

                bluetooth_button.setEnabled(
                    True
                )

                bluetooth_button.setToolTip(
                    "Повторно определить состояние Bluetooth"
                )

                bluetooth_button.clicked.connect(
                    lambda checked=False,
                    iid=instance_id:
                    self._force_refresh_bluetooth(iid)
                )

            # -----------------------------------------------------
            # BLUETOOTH ВКЛЮЧЁН
            # -----------------------------------------------------
            elif bluetooth_state is True:

                bluetooth_button.setText(
                    self._tr("disable")
                )

                bluetooth_button.setEnabled(
                    True
                )

                bluetooth_button.setToolTip(
                    "Выключить физический Bluetooth-адаптер"
                )

                bluetooth_button.clicked.connect(
                    lambda checked=False,
                    iid=instance_id:
                    self._set_bluetooth_enabled(
                        False,
                        iid,
                    )
                )

            # -----------------------------------------------------
            # BLUETOOTH ВЫКЛЮЧЕН
            # -----------------------------------------------------
            else:

                bluetooth_button.setText(
                    self._tr("enable")
                )

                bluetooth_button.setEnabled(
                    True
                )

                bluetooth_button.setToolTip(
                    "Включить физический Bluetooth-адаптер"
                )

                bluetooth_button.clicked.connect(
                    lambda checked=False,
                    iid=instance_id:
                    self._set_bluetooth_enabled(
                        True,
                        iid,
                    )
                )

            layout.addWidget(
                bluetooth_button
            )

        return card

    # =============================================================
    # BLUETOOTH CONTROL
    # =============================================================

    def _set_bluetooth_enabled(
        self,
        enabled: bool,
        instance_id=None,
    ):
        """
        Включает или выключает физический Bluetooth-адаптер.

        Используется pnputil.exe.

        Требуются права администратора.
        """

        if self._is_shutting_down:
            return

        if self._bluetooth_control_in_progress:
            print(
                "[Network] Bluetooth control already in progress."
            )
            return

        physical = str(
            instance_id
            or self._bluetooth_instance_id
            or ""
        ).strip()

        if not physical:

            print(
                "[Network] Bluetooth CONTROL: "
                "InstanceId отсутствует."
            )

            return

        if not physical.upper().startswith("USB\\"):

            print(
                "[Network] Bluetooth CONTROL: "
                "неверный физический InstanceId:",
                physical,
            )

            return

        # =========================================================
        # ADMIN
        # =========================================================

        if not self._is_admin():

            print(
                "[Network] Bluetooth CONTROL:"
            )

            print(
                "[Network] ПРОГРАММА НЕ ЗАПУЩЕНА "
                "ОТ АДМИНИСТРАТОРА."
            )

            print(
                "[Network] PnP operation requires "
                "administrator privileges."
            )

            # Ничего не оставляем в busy.
            self._bluetooth_control_in_progress = False

            return

        # =========================================================
        # START CONTROL
        # =========================================================

        self._bluetooth_control_in_progress = True

        self._bluetooth_target_state = bool(
            enabled
        )

        self._bluetooth_instance_id_for_control = (
            physical
        )

        self._bluetooth_verify_attempts = 0

        self._bluetooth_watchdog_token += 1

        # Сбрасываем cache.

        self._bluetooth_state_cache = None
        self._bluetooth_cache_time = 0.0

        try:
            self.timer.stop()
        except Exception:
            pass

        print(
            "[Network] ========================================"
        )

        print(
            "[Network] Bluetooth CONTROL:",
            "ENABLE" if enabled else "DISABLE",
        )

        print(
            "[Network] Bluetooth InstanceId:",
            physical,
        )

        print(
            "[Network] Administrator:",
            self._is_admin(),
        )

        print(
            "[Network] ========================================"
        )

        self._start_bluetooth_pnp_fallback(
            bool(enabled),
            physical,
        )

        # Обновляем UI сразу,
        # чтобы кнопка стала self._tr("please_wait")
        

    # =============================================================
    # START PNP PROCESS
    # =============================================================

    def _start_bluetooth_pnp_fallback(
        self,
        enabled,
        instance_id,
    ):
        """
        Запускает pnputil.exe без второго UAC.

        Приложение уже должно быть запущено от администратора.
        """

        if self._is_shutting_down:
            return

        # ---------------------------------------------------------
        # Если старый процесс остался
        # ---------------------------------------------------------

        if self._bluetooth_process is not None:

            try:
                if (
                    self._bluetooth_process.state()
                    != QProcess.NotRunning
                ):
                    print(
                        "[Network] Previous Bluetooth "
                        "process still running."
                    )

                    return

            except Exception:
                pass

            try:
                self._bluetooth_process.deleteLater()
            except Exception:
                pass

            self._bluetooth_process = None

        # ---------------------------------------------------------
        # Создаём QProcess
        # ---------------------------------------------------------

        process = QProcess(self)

        self._bluetooth_process = process

        process.setProcessChannelMode(
            QProcess.SeparateChannels
        )

        process.started.connect(
            self._bluetooth_process_started
        )

        process.readyReadStandardOutput.connect(
            self._bluetooth_process_stdout
        )

        process.readyReadStandardError.connect(
            self._bluetooth_process_stderr
        )

        process.errorOccurred.connect(
            self._bluetooth_process_error
        )

        process.finished.connect(
            self._bluetooth_control_finished
        )

        # ---------------------------------------------------------
        # COMMAND
        # ---------------------------------------------------------

        if enabled:

            program = "pnputil.exe"

            arguments = [
                "/enable-device",
                instance_id,
            ]

        else:

            program = "pnputil.exe"

            arguments = [
                "/disable-device",
                instance_id,
                "/force",
            ]

        print(
            "[Network] PnP command:",
            program,
            " ".join(arguments),
        )

        try:

            process.start(
                program,
                arguments,
            )

        except Exception as e:

            print(
                "[Network] Failed to start PnP:",
                repr(e),
            )

            self._bluetooth_process = None

            try:
                process.deleteLater()
            except Exception:
                pass

            self._finish_bluetooth_control(
                False
            )

            return

        # ---------------------------------------------------------
        # WATCHDOG
        # ---------------------------------------------------------

        token = self._bluetooth_watchdog_token

        QTimer.singleShot(
            int(
                self.BLUETOOTH_CONTROL_TIMEOUT
                * 1000
            ),
            lambda tok=token:
            self._bluetooth_process_watchdog(
                tok
            ),
        )

    # =============================================================
    # PROCESS STARTED
    # =============================================================

    def _bluetooth_process_started(self):

        print(
            "[Network] Bluetooth PnP process started."
        )

    # =============================================================
    # PNP OUTPUT DECODING
    # =============================================================

    @staticmethod
    def _decode_pnp_output(data):
        """
        Декодирует вывод pnputil для Windows с разными кодировками.

        На русской Windows pnputil часто использует OEM-кодировку
        (обычно CP866), поэтому UTF-8 здесь давал ``����``.
        """
        if not data:
            return ""

        candidates = []
        preferred = locale.getpreferredencoding(False)

        for encoding in ("utf-8", preferred, "cp866", "cp1251"):
            if encoding and encoding not in candidates:
                candidates.append(encoding)

        best_text = ""
        best_score = None

        for encoding in candidates:
            try:
                text = data.decode(encoding, errors="replace")
            except Exception:
                continue

            replacement_count = text.count("�")
            control_count = sum(
                1
                for char in text
                if ord(char) < 32 and char not in "\r\n\t"
            )
            score = replacement_count * 100 + control_count

            if best_score is None or score < best_score:
                best_score = score
                best_text = text

            if replacement_count == 0 and control_count == 0:
                return text

        return best_text

    # =============================================================
    # PROCESS STDOUT
    # =============================================================

    def _bluetooth_process_stdout(self):

        process = self._bluetooth_process

        if process is None:
            return

        try:

            data = bytes(
                process.readAllStandardOutput()
            )

            if data:

                text = self._decode_pnp_output(data).strip()

                if text:

                    print(
                        "[Bluetooth PnP STDOUT]",
                        text,
                    )

        except Exception as e:

            print(
                "[Network] stdout read error:",
                repr(e),
            )

    # =============================================================
    # PROCESS STDERR
    # =============================================================

    def _bluetooth_process_stderr(self):

        process = self._bluetooth_process

        if process is None:
            return

        try:

            data = bytes(
                process.readAllStandardError()
            )

            if data:

                text = self._decode_pnp_output(data).strip()

                if text:

                    print(
                        "[Bluetooth PnP STDERR]",
                        text,
                    )

        except Exception as e:

            print(
                "[Network] stderr read error:",
                repr(e),
            )

    # =============================================================
    # PROCESS ERROR
    # =============================================================

    def _bluetooth_process_error(
        self,
        error,
    ):

        print(
            "[Network] Bluetooth PnP error:",
            error,
        )

        if error == QProcess.FailedToStart:

            print(
                "[Network] pnputil.exe "
                "failed to start."
            )

            process = self._bluetooth_process

            self._bluetooth_process = None

            if process is not None:

                try:
                    process.deleteLater()
                except Exception:
                    pass

            self._finish_bluetooth_control(
                False
            )

    # =============================================================
    # PROCESS FINISHED
    # =============================================================

    def _bluetooth_control_finished(
        self,
        exit_code,
        exit_status,
    ):

        print(
            "[Network] PnP finished:",
            "exit_code=",
            exit_code,
            "exit_status=",
            exit_status,
        )

        process = self._bluetooth_process

        if process is not None:

            try:

                stdout = bytes(
                    process.readAllStandardOutput()
                ).decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                stderr = bytes(
                    process.readAllStandardError()
                ).decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if stdout:

                    print(
                        "[Bluetooth PnP FINAL STDOUT]",
                        stdout,
                    )

                if stderr:

                    print(
                        "[Bluetooth PnP FINAL STDERR]",
                        stderr,
                    )

            except Exception:
                pass

        # ---------------------------------------------------------
        # ERROR
        # ---------------------------------------------------------

        if exit_code != 0:

            print(
                "[Network] PnP operation FAILED."
            )

            if exit_code == 5:

                print(
                    "[Network] ERROR 5: "
                    "Access denied. "
                    "Run application as administrator."
                )

            self._bluetooth_process = None

            if process is not None:

                try:
                    process.deleteLater()
                except Exception:
                    pass

            self._finish_bluetooth_control(
                False
            )

            return

        # ---------------------------------------------------------
        # SUCCESS
        # ---------------------------------------------------------

        print(
            "[Network] PnP operation completed."
        )

        self._bluetooth_process = None

        if process is not None:

            try:
                process.deleteLater()
            except Exception:
                pass

        # ---------------------------------------------------------
        # Проверяем реальное состояние
        # ---------------------------------------------------------

        self._bluetooth_verify_attempts = 0

        QTimer.singleShot(
            700,
            self._verify_bluetooth_state,
        )

    # =============================================================
    # WATCHDOG
    # =============================================================

    def _bluetooth_process_watchdog(
        self,
        token,
    ):

        if self._is_shutting_down:
            return

        if token != self._bluetooth_watchdog_token:
            return

        if not self._bluetooth_control_in_progress:
            return

        process = self._bluetooth_process

        if process is None:
            return

        try:

            if (
                process.state()
                == QProcess.NotRunning
            ):
                return

        except Exception:
            pass

        print(
            "[Network] Bluetooth PnP watchdog:"
            " process timeout."
        )

        try:
            process.kill()
        except Exception:
            pass

        self._bluetooth_process = None

        try:
            process.deleteLater()
        except Exception:
            pass

        self._finish_bluetooth_control(
            False
        )

    # =============================================================
    # VERIFY BLUETOOTH STATE
    # =============================================================

    def _verify_bluetooth_state(self):

        if self._is_shutting_down:
            return

        if not self._bluetooth_control_in_progress:
            return

        instance_id = (
            self._bluetooth_instance_id_for_control
            or self._bluetooth_instance_id
        )

        target = (
            self._bluetooth_target_state
        )

        self._bluetooth_verify_attempts += 1

        # ---------------------------------------------------------
        # Force refresh
        # ---------------------------------------------------------

        self._bluetooth_state_cache = None
        self._bluetooth_cache_time = 0.0

        state = self._get_bluetooth_state(
            instance_id,
            force=True,
        )

        print(
            "[Network] PnP verify #"
            + str(
                self._bluetooth_verify_attempts
            )
            + ": state="
            + str(state)
            + " target="
            + str(target)
        )

        # ---------------------------------------------------------
        # SUCCESS
        # ---------------------------------------------------------

        if state is not None and state == target:

            print(
                "[Network] Bluetooth state "
                "successfully changed."
            )

            self._finish_bluetooth_control(
                True
            )

            return

        # ---------------------------------------------------------
        # RETRY
        # ---------------------------------------------------------

        if self._bluetooth_verify_attempts < 10:

            QTimer.singleShot(
                600,
                self._verify_bluetooth_state,
            )

            return

        # ---------------------------------------------------------
        # FAILED
        # ---------------------------------------------------------

        print(
            "[Network] Bluetooth state verification FAILED."
        )

        self._finish_bluetooth_control(
            False
        )

    # =============================================================
    # FINISH CONTROL
    # =============================================================

    def _finish_bluetooth_control(
        self,
        success,
    ):

        if self._is_shutting_down:
            return

        print(
            "[Network] Bluetooth control finished:",
            "SUCCESS" if success else "FAILED",
        )

        self._bluetooth_control_in_progress = False

        self._bluetooth_process = None

        self._bluetooth_target_state = None

        self._bluetooth_instance_id_for_control = None

        self._bluetooth_verify_attempts = 0

        self._bluetooth_state_cache = None
        self._bluetooth_cache_time = 0.0

        # ---------------------------------------------------------
        # Restart timer
        # ---------------------------------------------------------

        try:
            self.timer.start()
        except Exception:
            pass

        # ---------------------------------------------------------
        # Refresh UI
        # ---------------------------------------------------------

        QTimer.singleShot(
            300,
            self.update_network,
        )

    # =============================================================
    # FORCE BLUETOOTH REFRESH
    # =============================================================

    def _force_refresh_bluetooth(
        self,
        instance_id=None,
    ):

        if self._is_shutting_down:
            return

        self._bluetooth_state_cache = None
        self._bluetooth_cache_time = 0.0

        state = self._get_bluetooth_state(
            instance_id,
            force=True,
        )

        print(
            "[Network] Bluetooth forced state:",
            state,
        )

        self.update_network()

    # =============================================================
    # ICON
    # =============================================================

    def _get_icon(
        self,
        interface_type,
    ):

        icons = {
            "wifi": "📶",
            "bluetooth": "ᛒ",
            "ethernet": "🔌",
            "loopback": "🔄",
            "other": "🌐",
        }

        return icons.get(
            interface_type,
            "🌐",
        )

    # =============================================================
    # TYPE NAME
    # =============================================================

    def _get_interface_name(self, name):
        """Return a localized display name for common Windows interfaces."""

        if not name:
            return name

        lang = getattr(self, "ui_language", "ru")
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = "ru"

        original = str(name).strip()

        # Unicode-safe Russian names.
        wifi_ru = "\u0411\u0435\u0441\u043f\u0440\u043e\u0432\u043e\u0434\u043d\u0430\u044f \u0441\u0435\u0442\u044c"
        lan_ru = "\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 \u043f\u043e \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0439 \u0441\u0435\u0442\u0438"

        # Remove Windows "*" from local connection names.
        normalized = original.replace("*", "").strip()
        normalized = " ".join(normalized.split())

        # Wi-Fi
        wifi_match = (
            normalized.lower().startswith("wireless network connection")
            or normalized.lower().startswith("wi-fi")
            or normalized.lower().startswith("wifi")
            or normalized.lower().startswith(wifi_ru.lower())
        )

        if wifi_match:
            if normalized.lower().startswith("wireless network connection"):
                suffix = normalized[len("Wireless Network Connection"):].strip()
            elif normalized.lower().startswith("wi-fi"):
                suffix = normalized[len("Wi-Fi"):].strip()
            elif normalized.lower().startswith("wifi"):
                suffix = normalized[len("WiFi"):].strip()
            else:
                suffix = normalized[len(wifi_ru):].strip()

            translations = {
                "ru": wifi_ru,
                "uk": "\u0411\u0435\u0437\u0434\u0440\u043e\u0442\u043e\u0432\u0430 \u043c\u0435\u0440\u0435\u0436\u0430",
                "en": "Wireless Network Connection",
                "de": "Drahtlose Netzwerkverbindung",
                "it": "Connessione di rete wireless",
                "es": "Conexi\u00f3n de red inal\u00e1mbrica",
                "fr": "Connexion r\u00e9seau sans fil",
            }

            return f"{translations[lang]}{(' ' + suffix) if suffix else ''}"

        # Ethernet / Local Area Connection
        lan_match = (
            normalized.lower().startswith("local area connection")
            or normalized.lower().startswith("ethernet")
            or normalized.lower().startswith(lan_ru.lower())
        )

        if lan_match:
            if normalized.lower().startswith("local area connection"):
                suffix = normalized[len("Local Area Connection"):].strip()
            elif normalized.lower().startswith("ethernet"):
                suffix = normalized[len("Ethernet"):].strip()
            else:
                suffix = normalized[len(lan_ru):].strip()

            translations = {
                "ru": lan_ru,
                "uk": "\u041f\u0456\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043d\u044f \u0434\u043e \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0457 \u043c\u0435\u0440\u0435\u0436\u0456",
                "en": "Local Area Connection",
                "de": "LAN-Verbindung",
                "it": "Connessione alla rete locale",
                "es": "Conexi\u00f3n de \u00e1rea local",
                "fr": "Connexion au r\u00e9seau local",
            }

            return f"{translations[lang]}{(' ' + suffix) if suffix else ''}"

        # Loopback stays unchanged.
        return original

    def _get_type_name(
        self,
        interface_type,
    ):

        keys = {
            "wifi": "wifi",
            "bluetooth": "bluetooth",
            "ethernet": "ethernet",
            "loopback": "loopback",
            "other": "other",
        }

        return self._tr(
            keys.get(interface_type, "other")
        )

    # =============================================================
    # CLEAR CARDS
    # =============================================================

    def _clear_cards(self):

        while self.cards_layout.count():

            item = (
                self.cards_layout.takeAt(0)
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

    # =============================================================
    # SHUTDOWN
    # =============================================================

    def shutdown(self):

        self._is_shutting_down = True

        self._bluetooth_watchdog_token += 1

        # ---------------------------------------------------------
        # TIMER
        # ---------------------------------------------------------

        if hasattr(
            self,
            "timer",
        ):

            try:
                self.timer.stop()
            except Exception:
                pass

        # ---------------------------------------------------------
        # Bluetooth process
        # ---------------------------------------------------------

        process = getattr(
            self,
            "_bluetooth_process",
            None,
        )

        if process is not None:

            try:

                if (
                    process.state()
                    != QProcess.NotRunning
                ):

                    process.kill()
                    process.waitForFinished(
                        1000
                    )

            except Exception:
                pass

            try:
                process.deleteLater()
            except Exception:
                pass

            self._bluetooth_process = None

        self._bluetooth_control_in_progress = False

        print(
            "[Network] NetworkPage shutdown"
        )



