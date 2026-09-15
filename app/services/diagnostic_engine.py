from __future__ import annotations

import json
import time
from pathlib import Path


class DiagnosticEngine:
    """
    DiagnosticEngine v3
    PC Control Center Pro.

    Отвечает за:
        - обнаружение проблем;
        - постоянный ID инцидента;
        - изменение уровня проблемы;
        - длительность;
        - количество наблюдений;
        - пик нагрузки;
        - восстановление;
        - историю инцидентов;
        - статистику;
        - анализ повторяемости;
        - приоритет;
        - рекомендации.

    Архитектура:

        AIAnalyzer
             ↓
        DiagnosticEngine
             ↓
        problems / recovered / history
             ↓
        statistics / summary
    """

    PRIORITY = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }

    VALID_LEVELS = {
        "critical",
        "high",
        "medium",
        "low",
    }

    def __init__(
        self,
        history_file: str | Path | None = None,
    ):

        # ======================================================
        # HISTORY FILE
        # ======================================================

        if history_file is None:
            history_file = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "ai_diagnostics.json"
            )

        self.history_file = Path(history_file)

        # ======================================================
        # ACTIVE PROBLEMS
        # ======================================================

        self.active_problems: dict[str, dict] = {}

        # ======================================================
        # HISTORY
        # ======================================================

        self.history: list[dict] = []
        self.language = "ru"

        self._load_history()

    def set_language(self, language: str) -> None:
        if language in {"ru", "uk", "en", "de", "it", "es", "fr"}:
            self.language = language 

    # ==========================================================
    # HISTORY
    # ==========================================================

    def _load_history(self) -> None:
        """Загружает историю диагностики."""

        try:

            if not self.history_file.exists():
                return

            with self.history_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if isinstance(data, list):

                self.history = data

            elif isinstance(data, dict):

                history = data.get(
                    "history",
                    [],
                )

                if isinstance(history, list):
                    self.history = history

        except Exception as exc:

            print(
                "[DiagnosticEngine] "
                f"History load error: {exc}"
            )

            self.history = []

    # ==========================================================
    # SAVE HISTORY
    # ==========================================================

    def _save_history(self) -> None:
        """Сохраняет историю диагностики."""

        try:

            self.history_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # Защита от бесконечного роста.
            self.history = self.history[-500:]

            with self.history_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    self.history,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

        except Exception as exc:

            print(
                "[DiagnosticEngine] "
                f"History save error: {exc}"
            )

    # ==========================================================
    # SAFE FLOAT
    # ==========================================================

    @staticmethod
    def _safe_float(
        value,
        default: float = 0.0,
    ) -> float:

        try:

            if value is None:
                return default

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ==========================================================
    # SAFE INT
    # ==========================================================

    @staticmethod
    def _safe_int(
        value,
        default: int = 0,
    ) -> int:

        try:

            if value is None:
                return default

            return int(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ==========================================================
    # SAFE LEVEL
    # ==========================================================

    @classmethod
    def _safe_level(
        cls,
        level: str,
    ) -> str:

        if level in cls.VALID_LEVELS:
            return level

        return "medium"

    # ==========================================================
    # CREATE PROBLEM
    # ==========================================================

    def _create_problem(
        self,
        resource: str,
        level: str,
        message: str,
        value: float | None = None,
        threshold: float | None = None,
    ) -> dict:

        now = time.time()

        level = self._safe_level(level)

        return {

            "id": resource,

            "resource": resource,

            "level": level,

            "message": message,

            "value": value,

            "threshold": threshold,

            "first_seen": now,

            "last_seen": now,

            "duration_seconds": 0.0,

            "occurrences": 1,

            "peak": value,

            "recovered": False,

            "level_changes": [],
        }

    # ==========================================================
    # UPDATE PROBLEM
    # ==========================================================

    def _update_problem(
        self,
        problem_id: str,
        problem: dict,
    ) -> dict:

        now = time.time()

        existing = self.active_problems.get(
            problem_id
        )

        # ------------------------------------------------------
        # NEW
        # ------------------------------------------------------

        if existing is None:

            self.active_problems[
                problem_id
            ] = problem

            return problem

        # ------------------------------------------------------
        # TIME
        # ------------------------------------------------------

        existing["last_seen"] = now

        first_seen = self._safe_float(
            existing.get(
                "first_seen"
            ),
            now,
        )

        existing["duration_seconds"] = round(
            max(
                0.0,
                now - first_seen,
            ),
            1,
        )

        # ------------------------------------------------------
        # OCCURRENCES
        # ------------------------------------------------------

        existing["occurrences"] = (
            self._safe_int(
                existing.get(
                    "occurrences",
                    0,
                )
            )
            + 1
        )

        # ------------------------------------------------------
        # VALUE
        # ------------------------------------------------------

        current_value = problem.get(
            "value"
        )

        if current_value is not None:

            current_value = self._safe_float(
                current_value
            )

        existing["value"] = current_value

        # ------------------------------------------------------
        # PEAK
        # ------------------------------------------------------

        if current_value is not None:

            old_peak = existing.get(
                "peak"
            )

            if old_peak is None:

                existing["peak"] = current_value

            else:

                old_peak = self._safe_float(
                    old_peak,
                    current_value,
                )

                existing["peak"] = max(
                    old_peak,
                    current_value,
                )

        # ------------------------------------------------------
        # LEVEL
        # ------------------------------------------------------

        old_level = self._safe_level(
            existing.get(
                "level",
                "medium",
            )
        )

        new_level = self._safe_level(
            problem.get(
                "level",
                old_level,
            )
        )

        if old_level != new_level:

            existing.setdefault(
                "level_changes",
                [],
            ).append({

                "timestamp": now,

                "from": old_level,

                "to": new_level,

            })

        existing["level"] = new_level

        # ------------------------------------------------------
        # MESSAGE
        # ------------------------------------------------------

        existing["message"] = problem.get(
            "message",
            existing.get(
                "message",
                "",
            ),
        )

        # ------------------------------------------------------
        # THRESHOLD
        # ------------------------------------------------------

        existing["threshold"] = problem.get(
            "threshold",
            existing.get(
                "threshold"
            ),
        )

        # ------------------------------------------------------
        # RECOVERY
        # ------------------------------------------------------

        existing["recovered"] = False

        return existing

    # ==========================================================
    # REGISTER PROBLEM
    # ==========================================================

    def _register_problem(
        self,
        resource: str,
        level: str,
        message: str,
        value: float | None = None,
        threshold: float | None = None,
    ) -> dict:

        problem = self._create_problem(
            resource=resource,
            level=level,
            message=message,
            value=value,
            threshold=threshold,
        )

        return self._update_problem(
            problem["id"],
            problem,
        )

    # ==========================================================
    # RECOVERY
    # ==========================================================

    def _recover_problem(
        self,
        problem_id: str,
    ) -> dict | None:

        problem = self.active_problems.pop(
            problem_id,
            None,
        )

        if problem is None:
            return None

        now = time.time()

        problem["last_seen"] = now

        problem["recovered"] = True

        first_seen = self._safe_float(
            problem.get(
                "first_seen"
            ),
            now,
        )

        problem["duration_seconds"] = round(
            max(
                0.0,
                now - first_seen,
            ),
            1,
        )

        problem["recovered_at"] = now

        self.history.append(
            dict(problem)
        )

        return problem

    # ==========================================================
    # ANALYZE
    # ==========================================================

    def analyze(
        self,
        cpu: dict | None = None,
        ram: dict | None = None,
        disk: dict | None = None,
        gpu: dict | None = None,
        cpu_stability: dict | None = None,
    ) -> dict:

        cpu = cpu or {}
        ram = ram or {}
        disk = disk or {}
        gpu = gpu or {}
        cpu_stability = cpu_stability or {}

        # ======================================================
        # VALUES
        # ======================================================

        cpu_usage = self._safe_float(
            cpu.get("usage")
        )

        # Критическая загрузка CPU подтверждается только при
        # устойчивом высоком значении. Единичный пик 95-100%
        # не должен создавать Critical-инцидент.
        cpu_stable_high = bool(
            cpu_stability.get("stable_high", False)
        )

        ram_usage = self._safe_float(
            ram.get("usage")
        )

        disk_usage = self._safe_float(
            disk.get("usage")
        )

        gpu_raw = gpu.get(
            "usage"
        )

        gpu_usage = None

        if gpu_raw is not None:

            try:

                gpu_usage = float(
                    gpu_raw
                )

            except (
                TypeError,
                ValueError,
            ):

                gpu_usage = None

        # ======================================================
        # CURRENT IDS
        # ======================================================

        current_ids: set[str] = set()

        problems: list[dict] = []

        # ======================================================
        # CPU
        # ======================================================

        if cpu_usage >= 95:

            if cpu_stable_high:

                problem = self._register_problem(
                    "cpu",
                    "critical",
                    "Процессор почти полностью загружен в течение нескольких измерений.",
                    cpu_usage,
                    95,
                )

                current_ids.add("cpu")
                problems.append(dict(problem))

            else:

                # Единичный пик регистрируем только как high/attention.
                problem = self._register_problem(
                    "cpu",
                    "high",
                    "Зафиксирован кратковременный пик нагрузки процессора.",
                    cpu_usage,
                    95,
                )

                current_ids.add("cpu")
                problems.append(dict(problem))

        elif cpu_usage >= 85:

            problem = self._register_problem(
                "cpu",
                "high",
                "Высокая нагрузка на процессор.",
                cpu_usage,
                85,
            )

            current_ids.add("cpu")
            problems.append(dict(problem))

        elif cpu_usage >= 70:

            problem = self._register_problem(
                "cpu",
                "medium",
                "Процессор работает с повышенной нагрузкой.",
                cpu_usage,
                70,
            )

            current_ids.add("cpu")
            problems.append(dict(problem))

        # ======================================================
        # RAM
        # ======================================================

        if ram_usage >= 95:

            problem = self._register_problem(
                "ram",
                "critical",
                "Оперативная память почти полностью занята.",
                ram_usage,
                95,
            )

            current_ids.add("ram")
            problems.append(dict(problem))

        elif ram_usage >= 90:

            problem = self._register_problem(
                "ram",
                "high",
                "Оперативная память используется очень активно.",
                ram_usage,
                90,
            )

            current_ids.add("ram")
            problems.append(dict(problem))

        elif ram_usage >= 80:

            problem = self._register_problem(
                "ram",
                "medium",
                "Оперативная память используется активно.",
                ram_usage,
                80,
            )

            current_ids.add("ram")
            problems.append(dict(problem))

        # ======================================================
        # DISK
        # ======================================================

        if disk_usage >= 97:

            problem = self._register_problem(
                "disk",
                "critical",
                "На системном диске почти не осталось места.",
                disk_usage,
                97,
            )

            current_ids.add("disk")
            problems.append(dict(problem))

        elif disk_usage >= 90:

            problem = self._register_problem(
                "disk",
                "high",
                "На системном диске мало свободного места.",
                disk_usage,
                90,
            )

            current_ids.add("disk")
            problems.append(dict(problem))

        elif disk_usage >= 80:

            problem = self._register_problem(
                "disk",
                "medium",
                "Системный диск заполнен более чем на 80%.",
                disk_usage,
                80,
            )

            current_ids.add("disk")
            problems.append(dict(problem))

        # ======================================================
        # GPU
        # ======================================================

        if (
            gpu_usage is not None
            and gpu_usage >= 98
        ):

            problem = self._register_problem(
                "gpu",
                "high",
                "Графический процессор работает под высокой нагрузкой.",
                gpu_usage,
                98,
            )

            current_ids.add("gpu")
            problems.append(dict(problem))

        # ======================================================
        # RECOVERY
        # ======================================================

        recovered = []

        for problem_id in list(
            self.active_problems.keys()
        ):

            if problem_id not in current_ids:

                restored = self._recover_problem(
                    problem_id
                )

                if restored is not None:
                    recovered.append(restored)

        # ======================================================
        # SAVE HISTORY
        # ======================================================

        if recovered:
            self._save_history()

        # ======================================================
        # SORT
        # ======================================================

        problems.sort(
            key=lambda item:
                self.PRIORITY.get(
                    item.get("level", "medium"),
                    99,
                )
        )

        # ======================================================
        # GROUPS
        # ======================================================

        critical_problems = [
            item for item in problems
            if item.get("level") == "critical"
        ]

        high_problems = [
            item for item in problems
            if item.get("level") == "high"
        ]

        medium_problems = [
            item for item in problems
            if item.get("level") == "medium"
        ]

        # ======================================================
        # STATUS
        # ======================================================

        if critical_problems:
            status = "critical"

        elif high_problems or medium_problems:
            status = "attention"

        else:
            status = "good"

        # ======================================================
        # RESULT
        # ======================================================

        return {
            "status": status,
            "has_problems": bool(problems),
            "problem_count": len(problems),
            "problems": problems,
            "critical_problems": critical_problems,
            "high_problems": high_problems,
            "medium_problems": medium_problems,
            "recovered": recovered,
            "active_problem_count": len(
                self.active_problems
            ),
            "history_size": len(
                self.history
            ),
            "timestamp": time.time(),
        }

    # ==========================================================
    # ACTIVE PROBLEMS
    # ==========================================================

    def get_active_problems(self) -> list[dict]:
        """Возвращает текущие активные инциденты."""

        problems = [
            dict(problem)
            for problem in self.active_problems.values()
        ]

        problems.sort(
            key=lambda item:
                self.PRIORITY.get(
                    item.get("level", "medium"),
                    99,
                )
        )

        return problems

    # ==========================================================
    # HISTORY
    # ==========================================================

    def get_history(
        self,
        limit: int = 50,
    ) -> list[dict]:
        """Возвращает последние завершённые инциденты."""

        limit = max(
            1,
            self._safe_int(limit, 50),
        )

        return [
            dict(item)
            for item in self.history[-limit:]
        ]

    # ==========================================================
    # RECENT INCIDENTS
    # ==========================================================

    def get_recent_incidents(
        self,
        limit: int = 10,
    ) -> list[dict]:
        """Последние завершённые инциденты."""

        return self.get_history(limit)

    # ==========================================================
    # WORST INCIDENTS
    # ==========================================================

    def get_worst_incidents(
        self,
        limit: int = 5,
    ) -> list[dict]:
        """
        Возвращает наиболее серьёзные
        завершённые инциденты.
        """

        limit = max(
            1,
            self._safe_int(limit, 5),
        )

        incidents = [
            dict(item)
            for item in self.history
        ]

        incidents.sort(
            key=lambda item: (
                self.PRIORITY.get(
                    item.get(
                        "level",
                        "medium",
                    ),
                    99,
                ),
                -self._safe_float(
                    item.get(
                        "peak"
                    )
                ),
                -self._safe_int(
                    item.get(
                        "occurrences"
                    )
                ),
                -self._safe_float(
                    item.get(
                        "duration_seconds"
                    )
                ),
            )
        )

        return incidents[:limit]

    # ==========================================================
    # STATISTICS
    # ==========================================================

    def get_statistics(self) -> dict:
        """
        Возвращает общую статистику диагностики.
        """

        total_incidents = len(
            self.history
        )

        active_count = len(
            self.active_problems
        )

        recovered_count = sum(
            1
            for item in self.history
            if item.get("recovered") is True
        )

        resource_counts: dict[str, int] = {}

        level_counts: dict[str, int] = {}

        total_duration = 0.0

        total_occurrences = 0

        max_peak = 0.0

        max_peak_resource = None

        for item in self.history:

            resource = str(
                item.get(
                    "resource",
                    "unknown",
                )
            )

            level = self._safe_level(
                item.get(
                    "level",
                    "medium",
                )
            )

            resource_counts[resource] = (
                resource_counts.get(
                    resource,
                    0,
                )
                + 1
            )

            level_counts[level] = (
                level_counts.get(
                    level,
                    0,
                )
                + 1
            )

            duration = self._safe_float(
                item.get(
                    "duration_seconds"
                )
            )

            occurrences = self._safe_int(
                item.get(
                    "occurrences"
                )
            )

            peak = self._safe_float(
                item.get(
                    "peak"
                )
            )

            total_duration += duration

            total_occurrences += occurrences

            if peak > max_peak:

                max_peak = peak

                max_peak_resource = resource

        # ------------------------------------------------------
        # MOST PROBLEMATIC RESOURCE
        # ------------------------------------------------------

        most_problematic_resource = None

        if resource_counts:

            most_problematic_resource = max(
                resource_counts,
                key=resource_counts.get,
            )

        # ------------------------------------------------------
        # WORST LEVEL
        # ------------------------------------------------------

        worst_level = None

        if level_counts:

            worst_level = min(
                level_counts,
                key=lambda level:
                    self.PRIORITY.get(
                        level,
                        99,
                    ),
            )

        # ------------------------------------------------------
        # AVERAGES
        # ------------------------------------------------------

        if total_incidents > 0:

            average_duration = (
                total_duration
                / total_incidents
            )

            average_occurrences = (
                total_occurrences
                / total_incidents
            )

        else:

            average_duration = 0.0

            average_occurrences = 0.0

        return {

            "total_incidents":
                total_incidents,

            "active_incidents":
                active_count,

            "recovered_incidents":
                recovered_count,

            "resource_counts":
                resource_counts,

            "level_counts":
                level_counts,

            "most_problematic_resource":
                most_problematic_resource,

            "worst_level":
                worst_level,

            "average_duration_seconds":
                round(
                    average_duration,
                    1,
                ),

            "average_occurrences":
                round(
                    average_occurrences,
                    1,
                ),

            "max_peak":
                round(
                    max_peak,
                    1,
                ),

            "max_peak_resource":
                max_peak_resource,
        }

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def build_summary(self) -> dict:
        """
        Формирует компактное диагностическое резюме
        для AIAnalyzer / Dashboard.
        """

        active = self.get_active_problems()

        statistics = self.get_statistics()

        # ------------------------------------------------------
        # CURRENT WORST LEVEL
        # ------------------------------------------------------

        current_level = None

        if active:

            current_level = min(
                (
                    self._safe_level(
                        item.get(
                            "level",
                            "medium",
                        )
                    )
                    for item in active
                ),
                key=lambda level:
                    self.PRIORITY.get(
                        level,
                        99,
                    ),
            )

        # ------------------------------------------------------
        # STATUS
        # ------------------------------------------------------

        if current_level == "critical":

            status = "critical"

        elif current_level in {
            "high",
            "medium",
        }:

            status = "attention"

        else:

            status = "good"

        return {

            "status":
                status,

            "current_level":
                current_level,

            "active_problems":
                active,

            "active_problem_count":
                len(active),

            "statistics":
                statistics,

            "recent_incidents":
                self.get_recent_incidents(5),

            "worst_incidents":
                self.get_worst_incidents(5),

            "timestamp":
                time.time(),
        }

    # ==========================================================
    # RECOMMENDATIONS
    # ==========================================================

    def build_recommendations(
        self,
        diagnostics: dict | None,
    ) -> list[dict]:

        if not isinstance(
            diagnostics,
            dict,
        ):
            return []

        recommendations = []

        problems = diagnostics.get(
            "problems",
            [],
        )

        if not isinstance(
            problems,
            list,
        ):
            problems = []

        # ======================================================
        # ONE RECOMMENDATION PER RESOURCE
        # ======================================================

        seen_resources: set[str] = set()

        for problem in problems:

            if not isinstance(
                problem,
                dict,
            ):
                continue

            resource = problem.get(
                "resource",
                "system",
            )

            if resource in seen_resources:
                continue

            seen_resources.add(resource)

            level = self._safe_level(
                problem.get(
                    "level",
                    "medium",
                )
            )

            occurrences = self._safe_int(
                problem.get(
                    "occurrences",
                    0,
                )
            )

            duration = self._safe_float(
                problem.get(
                    "duration_seconds",
                    0,
                )
            )

            # ==================================================
            # CPU
            # ==================================================

            if resource == "cpu":

                if level == "critical":

                    if self.language == "uk":
                        title = "Критичне завантаження CPU"
                        message = (
                            "Перевірте процеси "
                            "з високим завантаженням "
                            "процесора."
                        )
                    elif self.language == "en":
                        title = "Critical CPU load"
                        message = (
                            "Check processes "
                            "with high CPU usage."
                        )
                    elif self.language == "de":
                        title = "Kritische CPU-Auslastung"
                        message = (
                            "Überprüfen Sie Prozesse "
                            "mit hoher CPU-Auslastung."
                        )
                    elif self.language == "it":
                        title = "Carico CPU critico"
                        message = (
                            "Controllare i processi "
                            "con un elevato utilizzo della CPU."
                        )
                    elif self.language == "es":
                        title = "Carga crítica de la CPU"
                        message = (
                            "Compruebe los procesos "
                            "con un alto uso de la CPU."
                        )
                    elif self.language == "fr":
                        title = "Charge CPU critique"
                        message = (
                            "Vérifiez les processus "
                            "qui utilisent fortement le processeur."
                        )
                    else:
                        title = "Критическая загрузка CPU"
                        message = (
                            "Проверьте процессы "
                            "с высокой загрузкой "
                            "процессора."
                        )

                elif level == "high":

                    if self.language == "uk":
                        title = "Високе завантаження CPU"
                        message = (
                            "Перевірте фонові процеси "
                            "та програми, які використовують "
                            "процесор."
                        )
                    elif self.language == "en":
                        title = "High CPU load"
                        message = (
                            "Check background processes "
                            "and applications using the CPU."
                        )
                    elif self.language == "de":
                        title = "Hohe CPU-Auslastung"
                        message = (
                            "Überprüfen Sie Hintergrundprozesse "
                            "und Anwendungen, die den Prozessor nutzen."
                        )
                    elif self.language == "it":
                        title = "Elevato utilizzo della CPU"
                        message = (
                            "Controllare i processi in background "
                            "e le applicazioni che utilizzano il processore."
                        )
                    elif self.language == "es":
                        title = "Alta carga de la CPU"
                        message = (
                            "Compruebe los procesos en segundo plano "
                            "y las aplicaciones que utilizan el procesador."
                        )
                    elif self.language == "fr":
                        title = "Charge CPU élevée"
                        message = (
                            "Vérifiez les processus en arrière-plan "
                            "et les applications utilisant le processeur."
                        )
                    else:
                        title = "Высокая загрузка CPU"
                        message = (
                            "Проверьте фоновые процессы "
                            "и приложения, использующие "
                            "процессор."
                        )

                else:

                    if self.language == "uk":
                        title = "Підвищене навантаження CPU"
                        message = (
                            "Якщо навантаження зберігається, "
                            "перевірте активні програми."
                        )
                    elif self.language == "en":
                        title = "Increased CPU load"
                        message = (
                            "If the load persists, "
                            "check active applications."
                        )
                    elif self.language == "de":
                        title = "Erhöhte CPU-Auslastung"
                        message = (
                            "Wenn die Auslastung anhält, "
                            "überprüfen Sie die aktiven Anwendungen."
                        )
                    elif self.language == "it":
                        title = "Carico CPU aumentato"
                        message = (
                            "Se il carico persiste, "
                            "controllare le applicazioni attive."
                        )
                    elif self.language == "es":
                        title = "Carga de CPU elevada"
                        message = (
                            "Si la carga persiste, "
                            "compruebe las aplicaciones activas."
                        )
                    elif self.language == "fr":
                        title = "Charge CPU accrue"
                        message = (
                            "Si la charge persiste, "
                            "vérifiez les applications actives."
                        )
                    else:
                        title = "Повышенная нагрузка CPU"
                        message = (
                            "Если нагрузка сохраняется, "
                            "проверьте активные приложения."
                        )

            # ==================================================
            # RAM
            # ==================================================

            elif resource == "ram":

                if level == "critical":

                    if self.language == "uk":
                        title = "Критично мало RAM"
                        message = (
                            "Закрийте непотрібні програми "
                            "та перевірте програми, "
                            "які споживають багато пам'яті."
                        )
                    elif self.language == "en":
                        title = "Critically low RAM"
                        message = (
                            "Close unnecessary applications "
                            "and check programs using large amounts of memory."
                        )
                    elif self.language == "de":
                        title = "Kritisch wenig RAM"
                        message = (
                            "Schließen Sie unnötige Anwendungen "
                            "und überprüfen Sie Programme mit hohem Speicherverbrauch."
                        )
                    elif self.language == "it":
                        title = "RAM insufficiente"
                        message = (
                            "Chiudere le applicazioni non necessarie "
                            "e controllare i programmi che utilizzano molta memoria."
                        )
                    elif self.language == "es":
                        title = "RAM críticamente baja"
                        message = (
                            "Cierre las aplicaciones innecesarias "
                            "y compruebe los programas que consumen mucha memoria."
                        )
                    elif self.language == "fr":
                        title = "RAM insuffisante"
                        message = (
                            "Fermez les applications inutiles "
                            "et vérifiez les programmes utilisant beaucoup de mémoire."
                        )
                    else:
                        title = "Критически мало RAM"
                        message = (
                            "Закройте ненужные приложения "
                            "и проверьте программы, "
                            "потребляющие много памяти."
                        )

                elif level == "high":

                    if self.language == "uk":
                        title = "Високе використання RAM"
                        message = (
                            "Перевірте програми, "
                            "які використовують "
                            "великий обсяг пам'яті."
                        )
                    elif self.language == "en":
                        title = "High RAM usage"
                        message = (
                            "Check applications "
                            "that use a large amount of memory."
                        )
                    elif self.language == "de":
                        title = "Hoher RAM-Verbrauch"
                        message = (
                            "Überprüfen Sie Anwendungen, "
                            "die viel Arbeitsspeicher verwenden."
                        )
                    elif self.language == "it":
                        title = "Utilizzo elevato della RAM"
                        message = (
                            "Controllare le applicazioni "
                            "che utilizzano molta memoria."
                        )
                    elif self.language == "es":
                        title = "Alto uso de RAM"
                        message = (
                            "Compruebe las aplicaciones "
                            "que utilizan una gran cantidad de memoria."
                        )
                    elif self.language == "fr":
                        title = "Utilisation élevée de la RAM"
                        message = (
                            "Vérifiez les applications "
                            "qui utilisent beaucoup de mémoire."
                        )
                    else:
                        title = "Высокое использование RAM"
                        message = (
                            "Проверьте приложения, "
                            "которые используют "
                            "большой объём памяти."
                        )

                else:

                    if self.language == "uk":
                        title = "RAM використовується активно"
                        message = (
                            "Стежте за вільною "
                            "оперативною пам'яттю."
                        )
                    elif self.language == "en":
                        title = "RAM is actively used"
                        message = (
                            "Monitor the amount of free RAM."
                        )
                    elif self.language == "de":
                        title = "RAM wird stark genutzt"
                        message = (
                            "Überwachen Sie den verfügbaren Arbeitsspeicher."
                        )
                    elif self.language == "it":
                        title = "La RAM è utilizzata attivamente"
                        message = (
                            "Controllare la quantità di memoria RAM disponibile."
                        )
                    elif self.language == "es":
                        title = "La RAM se utiliza activamente"
                        message = (
                            "Controle la cantidad de memoria RAM disponible."
                        )
                    elif self.language == "fr":
                        title = "La RAM est fortement utilisée"
                        message = (
                            "Surveillez la quantité de mémoire RAM disponible."
                        )
                    else:
                        title = "RAM используется активно"
                        message = (
                            "Следите за свободной "
                            "оперативной памятью."
                        )

            # ==================================================
            # DISK
            # ==================================================

            elif resource == "disk":

                if level == "critical":

                    if self.language == "uk":
                        title = "Критично мало місця"
                        message = (
                            "Звільніть місце "
                            "на системному диску."
                        )
                    elif self.language == "en":
                        title = "Critically low disk space"
                        message = (
                            "Free up space "
                            "on the system drive."
                        )
                    elif self.language == "de":
                        title = "Kritisch wenig Speicherplatz"
                        message = (
                            "Geben Sie Speicherplatz "
                            "auf dem Systemlaufwerk frei."
                        )
                    elif self.language == "it":
                        title = "Spazio su disco insufficiente"
                        message = (
                            "Liberare spazio "
                            "sul disco di sistema."
                        )
                    elif self.language == "es":
                        title = "Espacio en disco críticamente bajo"
                        message = (
                            "Libere espacio "
                            "en el disco del sistema."
                        )
                    elif self.language == "fr":
                        title = "Espace disque insuffisant"
                        message = (
                            "Libérez de l'espace "
                            "sur le disque système."
                        )
                    else:
                        title = "Критически мало места"
                        message = (
                            "Освободите место "
                            "на системном диске."
                        )

                elif level == "high":

                    if self.language == "uk":
                        title = "Мало вільного місця"
                        message = (
                            "Видаліть непотрібні файли "
                            "або перемістіть великі "
                            "дані."
                        )
                    elif self.language == "en":
                        title = "Low free disk space"
                        message = (
                            "Delete unnecessary files "
                            "or move large amounts of data."
                        )
                    elif self.language == "de":
                        title = "Wenig freier Speicherplatz"
                        message = (
                            "Löschen Sie unnötige Dateien "
                            "oder verschieben Sie große Datenmengen."
                        )
                    elif self.language == "it":
                        title = "Poco spazio libero"
                        message = (
                            "Eliminare i file non necessari "
                            "o spostare i dati di grandi dimensioni."
                        )
                    elif self.language == "es":
                        title = "Poco espacio libre"
                        message = (
                            "Elimine archivos innecesarios "
                            "o mueva los datos de gran tamaño."
                        )
                    elif self.language == "fr":
                        title = "Peu d'espace libre"
                        message = (
                            "Supprimez les fichiers inutiles "
                            "ou déplacez les données volumineuses."
                        )
                    else:
                        title = "Мало свободного места"
                        message = (
                            "Удалите ненужные файлы "
                            "или переместите крупные "
                            "данные."
                        )

                else:

                    if self.language == "uk":
                        title = "Диск заповнений"
                        message = (
                            "Рекомендується періодично "
                            "очищати системний диск."
                        )
                    elif self.language == "en":
                        title = "Disk is full"
                        message = (
                            "It is recommended to periodically "
                            "clean the system drive."
                        )
                    elif self.language == "de":
                        title = "Festplatte ist voll"
                        message = (
                            "Es wird empfohlen, das Systemlaufwerk "
                            "regelmäßig zu bereinigen."
                        )
                    elif self.language == "it":
                        title = "Disco pieno"
                        message = (
                            "Si consiglia di pulire periodicamente "
                            "il disco di sistema."
                        )
                    elif self.language == "es":
                        title = "Disco lleno"
                        message = (
                            "Se recomienda limpiar periódicamente "
                            "el disco del sistema."
                        )
                    elif self.language == "fr":
                        title = "Disque plein"
                        message = (
                            "Il est recommandé de nettoyer régulièrement "
                            "le disque système."
                        )
                    else:
                        title = "Диск заполнен"
                        message = (
                            "Рекомендуется периодически "
                            "очищать системный диск."
                        )

            # ==================================================
            # GPU
            # ==================================================

            elif resource == "gpu":

                if self.language == "uk":
                    title = "Високе навантаження GPU"
                    message = (
                        "Перевірте програми "
                        "та ігри, які використовують "
                        "графічний процесор."
                    )
                elif self.language == "en":
                    title = "High GPU load"
                    message = (
                        "Check applications "
                        "and games using the GPU."
                    )
                elif self.language == "de":
                    title = "Hohe GPU-Auslastung"
                    message = (
                        "Überprüfen Sie Anwendungen "
                        "und Spiele, die die GPU verwenden."
                    )
                elif self.language == "it":
                    title = "Elevato utilizzo della GPU"
                    message = (
                        "Controllare le applicazioni "
                        "e i giochi che utilizzano la GPU."
                    )
                elif self.language == "es":
                    title = "Alta carga de la GPU"
                    message = (
                        "Compruebe las aplicaciones "
                        "y los juegos que utilizan la GPU."
                    )
                elif self.language == "fr":
                    title = "Charge GPU élevée"
                    message = (
                        "Vérifiez les applications "
                        "et les jeux utilisant le GPU."
                    )
                else:
                    title = "Высокая нагрузка GPU"
                    message = (
                        "Проверьте приложения "
                        "и игры, использующие "
                        "графический процессор."
                    )

            # ==================================================
            # UNKNOWN
            # ==================================================

            else:

                if self.language == "uk":
                    title = "Виявлено проблему"
                    message = str(
                        problem.get(
                            "message",
                            "Потрібна увага.",
                        )
                    )
                elif self.language == "en":
                    title = "Problem detected"
                    message = str(
                        problem.get(
                            "message",
                            "Attention required.",
                        )
                    )
                elif self.language == "de":
                    title = "Problem erkannt"
                    message = str(
                        problem.get(
                            "message",
                            "Aufmerksamkeit erforderlich.",
                        )
                    )
                elif self.language == "it":
                    title = "Problema rilevato"
                    message = str(
                        problem.get(
                            "message",
                            "È richiesta attenzione.",
                        )
                    )
                elif self.language == "es":
                    title = "Problema detectado"
                    message = str(
                        problem.get(
                            "message",
                            "Se requiere atención.",
                        )
                    )
                elif self.language == "fr":
                    title = "Problème détecté"
                    message = str(
                        problem.get(
                            "message",
                            "Une attention est requise.",
                        )
                    )
                else:
                    title = "Обнаружена проблема"
                    message = str(
                        problem.get(
                            "message",
                            "Требуется внимание.",
                        )
                    )

            recommendations.append({

                "title": title,

                "message": message,

                "level": level,

                "resource": resource,

                "occurrences": occurrences,

                "duration_seconds": duration,

            })

        # ======================================================
        # SORT
        # ======================================================

        recommendations.sort(
            key=lambda item: (

                self.PRIORITY.get(
                    item.get(
                        "level",
                        "medium",
                    ),
                    99,
                ),

                -self._safe_int(
                    item.get(
                        "occurrences",
                        0,
                    )
                ),

                -self._safe_float(
                    item.get(
                        "duration_seconds",
                        0,
                    )
                ),
            )
        )

        return recommendations