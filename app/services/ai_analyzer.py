import os
import time
import platform

import psutil

from app.services.gpu_info import get_cached_gpu_info
from app.services.diagnostic_engine import DiagnosticEngine
from app.services.system_info import get_user_info


class AIAnalyzer:
    """
    Быстрый AI-анализатор состояния компьютера.

    Основная задача:
    - быстро получать CPU / RAM / Disk;
    - GPU брать только из общего cache;
    - хранить небольшую историю метрик;
    - определять устойчивую нагрузку;
    - передавать диагностику в DiagnosticEngine;
    - возвращать единый результат для Dashboard / AIWorker.

    Локализация:
    - ru
    - en
    - uk
    - de
    - it
    - es
    - fr
    """

    SUPPORTED_LANGUAGES = {
        "ru",
        "en",
        "uk",
        "de",
        "it",
        "es",
        "fr",
    }

    # ==========================================================
    # LOCALIZATION
    # ==========================================================

    TRANSLATIONS = {
        "ru": {
            "user": "Пользователь",
            "unknown_gpu": "Неизвестная видеокарта",

            "reason_cpu_critical":
                "процессор почти полностью загружен в течение нескольких измерений",
            "reason_cpu_high_stable":
                "высокая нагрузка на процессор сохраняется",
            "reason_cpu_spike":
                "зафиксирован кратковременный пик нагрузки процессора",
            "reason_cpu_elevated":
                "нагрузка на процессор остаётся высокой",

            "reason_ram_critical":
                "оперативная память почти полностью занята",
            "reason_ram_low":
                "мало свободной оперативной памяти",
            "reason_ram_active":
                "оперативная память используется активно",

            "reason_disk_critical":
                "на системном диске почти не осталось места",
            "reason_disk_low":
                "на системном диске мало свободного места",
            "reason_disk_full":
                "системный диск заполнен более чем на 80%",

            "reason_gpu_high":
                "графический процессор работает под высокой нагрузкой",

            "rec_cpu_critical":
                "Критическая загрузка CPU",
            "rec_cpu_critical_msg":
                "Проверьте процессы с высокой загрузкой процессора.",
            "rec_cpu_high":
                "Высокая загрузка CPU",
            "rec_cpu_high_msg":
                "CPU длительное время загружен примерно на {cpu}%. "
                "Проверьте фоновые процессы.",
            "rec_cpu_elevated":
                "Повышенная нагрузка CPU",
            "rec_cpu_elevated_msg":
                "Текущая загрузка CPU около {cpu}%",

            "rec_ram_critical":
                "Критически мало RAM",
            "rec_ram_critical_msg":
                "Используется около {ram}% памяти. "
                "Закройте ненужные приложения.",
            "rec_ram_high":
                "Высокое использование RAM",
            "rec_ram_high_msg":
                "RAM занята примерно на {ram}%. "
                "Проверьте приложения, потребляющие много памяти.",
            "rec_ram_active":
                "RAM используется активно",
            "rec_ram_active_msg":
                "Проверьте приложения, которые используют много оперативной памяти.",

            "rec_disk_critical":
                "Критически мало места",
            "rec_disk_critical_msg":
                "На системном диске осталось очень мало свободного места.",
            "rec_disk_low":
                "Мало свободного места",
            "rec_disk_low_msg":
                "Системный диск заполнен на {disk}%. "
                "Рекомендуется удалить ненужные файлы.",
            "rec_disk_full":
                "Диск заполнен",
            "rec_disk_full_msg":
                "Используется {disk}% системного диска.",

            "rec_gpu_high":
                "Высокая нагрузка GPU",
            "rec_gpu_high_msg":
                "Графический процессор почти полностью загружен.",

            "rec_all_good":
                "Всё в порядке",
            "rec_all_good_msg":
                "Критических проблем в текущем состоянии системы не обнаружено.",

            "msg_good_calm":
                "Система работает спокойно. "
                "Загрузка основных ресурсов находится на комфортном уровне.",
            "msg_good_stable":
                "Система работает стабильно. "
                "CPU: {cpu}%, RAM: {ram}%, диск: {disk}%. "
                "Критических проблем не обнаружено.",
            "msg_attention":
                "Я обнаружил повышенную нагрузку: {reasons}.",
            "msg_attention_generic":
                "Некоторые системные ресурсы используются активнее обычного. "
                "Критического состояния не обнаружено.",
            "msg_critical":
                "Требуется внимание. {reasons}.",
            "msg_ram_critical":
                "Оперативная память почти полностью занята. "
                "Это может привести к замедлению системы.",
            "msg_disk_critical":
                "На системном диске почти не осталось свободного места.",
            "msg_cpu_critical":
                "Процессор почти полностью загружен "
                "в течение нескольких измерений.",
            "msg_critical_generic":
                "Обнаружено состояние, требующее внимания пользователя.",
            "msg_finished":
                "Анализ системы завершён.",

            "diagnostic_invalid":
                "DiagnosticEngine вернул некорректный результат.",
        },

        "en": {
            "user": "User",
            "unknown_gpu": "Unknown GPU",

            "reason_cpu_critical":
                "the processor has been almost fully loaded for several measurements",
            "reason_cpu_high_stable":
                "high CPU load is persistent",
            "reason_cpu_spike":
                "a short CPU load spike was detected",
            "reason_cpu_elevated":
                "CPU load remains high",

            "reason_ram_critical":
                "RAM is almost completely occupied",
            "reason_ram_low":
                "free RAM is low",
            "reason_ram_active":
                "RAM is being used heavily",

            "reason_disk_critical":
                "almost no free space remains on the system drive",
            "reason_disk_low":
                "free space on the system drive is low",
            "reason_disk_full":
                "the system drive is more than 80% full",

            "reason_gpu_high":
                "the GPU is under high load",

            "rec_cpu_critical":
                "Critical CPU Load",
            "rec_cpu_critical_msg":
                "Check processes with high CPU usage.",
            "rec_cpu_high":
                "High CPU Load",
            "rec_cpu_high_msg":
                "CPU has been running at approximately {cpu}% for an extended period. "
                "Check background processes.",
            "rec_cpu_elevated":
                "Elevated CPU Load",
            "rec_cpu_elevated_msg":
                "Current CPU load is approximately {cpu}%",

            "rec_ram_critical":
                "Critically Low RAM",
            "rec_ram_critical_msg":
                "About {ram}% of RAM is in use. Close unnecessary applications.",
            "rec_ram_high":
                "High RAM Usage",
            "rec_ram_high_msg":
                "RAM usage is approximately {ram}%. "
                "Check applications consuming a lot of memory.",
            "rec_ram_active":
                "RAM Is Heavily Used",
            "rec_ram_active_msg":
                "Check applications that are using a large amount of RAM.",

            "rec_disk_critical":
                "Critically Low Disk Space",
            "rec_disk_critical_msg":
                "Very little free space remains on the system drive.",
            "rec_disk_low":
                "Low Free Disk Space",
            "rec_disk_low_msg":
                "The system drive is {disk}% full. "
                "Consider deleting unnecessary files.",
            "rec_disk_full":
                "Disk Is Full",
            "rec_disk_full_msg":
                "{disk}% of the system drive is currently in use.",

            "rec_gpu_high":
                "High GPU Load",
            "rec_gpu_high_msg":
                "The GPU is almost fully loaded.",

            "rec_all_good":
                "Everything Is Fine",
            "rec_all_good_msg":
                "No critical problems were detected in the current system state.",

            "msg_good_calm":
                "The system is running calmly. "
                "Main resource usage is at a comfortable level.",
            "msg_good_stable":
                "The system is running stably. "
                "CPU: {cpu}%, RAM: {ram}%, disk: {disk}%. "
                "No critical problems were detected.",
            "msg_attention":
                "I detected increased system load: {reasons}.",
            "msg_attention_generic":
                "Some system resources are being used more actively than usual. "
                "No critical condition was detected.",
            "msg_critical":
                "Attention is required. {reasons}.",
            "msg_ram_critical":
                "RAM is almost completely occupied. "
                "This may slow down the system.",
            "msg_disk_critical":
                "Almost no free space remains on the system drive.",
            "msg_cpu_critical":
                "The processor has been almost fully loaded "
                "for several measurements.",
            "msg_critical_generic":
                "A condition requiring user attention was detected.",
            "msg_finished":
                "System analysis completed.",

            "diagnostic_invalid":
                "DiagnosticEngine returned an invalid result.",
        },

        "uk": {
            "user": "Користувач",
            "unknown_gpu": "Невідома відеокарта",

            "reason_cpu_critical":
                "процесор майже повністю завантажений протягом кількох вимірювань",
            "reason_cpu_high_stable":
                "високе навантаження на процесор зберігається",
            "reason_cpu_spike":
                "зафіксовано короткочасний пік навантаження на процесор",
            "reason_cpu_elevated":
                "навантаження на процесор залишається високим",

            "reason_ram_critical":
                "оперативна пам'ять майже повністю зайнята",
            "reason_ram_low":
                "залишилося мало вільної оперативної пам'яті",
            "reason_ram_active":
                "оперативна пам'ять використовується активно",

            "reason_disk_critical":
                "на системному диску майже не залишилося вільного місця",
            "reason_disk_low":
                "на системному диску мало вільного місця",
            "reason_disk_full":
                "системний диск заповнений більш ніж на 80%",

            "reason_gpu_high":
                "графічний процесор працює під високим навантаженням",

            "rec_cpu_critical":
                "Критичне навантаження CPU",
            "rec_cpu_critical_msg":
                "Перевірте процеси з високим навантаженням на процесор.",
            "rec_cpu_high":
                "Високе навантаження CPU",
            "rec_cpu_high_msg":
                "CPU тривалий час завантажений приблизно на {cpu}%. "
                "Перевірте фонові процеси.",
            "rec_cpu_elevated":
                "Підвищене навантаження CPU",
            "rec_cpu_elevated_msg":
                "Поточне навантаження CPU становить приблизно {cpu}%",

            "rec_ram_critical":
                "Критично мало RAM",
            "rec_ram_critical_msg":
                "Використовується близько {ram}% пам'яті. "
                "Закрийте непотрібні програми.",
            "rec_ram_high":
                "Високе використання RAM",
            "rec_ram_high_msg":
                "RAM зайнята приблизно на {ram}%. "
                "Перевірте програми, які споживають багато пам'яті.",
            "rec_ram_active":
                "RAM активно використовується",
            "rec_ram_active_msg":
                "Перевірте програми, які використовують багато оперативної пам'яті.",

            "rec_disk_critical":
                "Критично мало місця",
            "rec_disk_critical_msg":
                "На системному диску залишилося дуже мало вільного місця.",
            "rec_disk_low":
                "Мало вільного місця",
            "rec_disk_low_msg":
                "Системний диск заповнений на {disk}%. "
                "Рекомендується видалити непотрібні файли.",
            "rec_disk_full":
                "Диск заповнений",
            "rec_disk_full_msg":
                "Використовується {disk}% системного диска.",

            "rec_gpu_high":
                "Високе навантаження GPU",
            "rec_gpu_high_msg":
                "Графічний процесор майже повністю завантажений.",

            "rec_all_good":
                "Все гаразд",
            "rec_all_good_msg":
                "Критичних проблем у поточному стані системи не виявлено.",

            "msg_good_calm":
                "Система працює спокійно. "
                "Завантаження основних ресурсів перебуває на комфортному рівні.",
            "msg_good_stable":
                "Система працює стабільно. "
                "CPU: {cpu}%, RAM: {ram}%, диск: {disk}%. "
                "Критичних проблем не виявлено.",
            "msg_attention":
                "Я виявив підвищене навантаження: {reasons}.",
            "msg_attention_generic":
                "Деякі системні ресурси використовуються активніше, ніж зазвичай. "
                "Критичного стану не виявлено.",
            "msg_critical":
                "Потрібна увага. {reasons}.",
            "msg_ram_critical":
                "Оперативна пам'ять майже повністю зайнята. "
                "Це може призвести до уповільнення системи.",
            "msg_disk_critical":
                "На системному диску майже не залишилося вільного місця.",
            "msg_cpu_critical":
                "Процесор майже повністю завантажений "
                "протягом кількох вимірювань.",
            "msg_critical_generic":
                "Виявлено стан, що потребує уваги користувача.",
            "msg_finished":
                "Аналіз системи завершено.",

            "diagnostic_invalid":
                "DiagnosticEngine повернув некоректний результат.",
        },

        "de": {
            "user": "Benutzer",
            "unknown_gpu": "Unbekannte Grafikkarte",

            "reason_cpu_critical":
                "der Prozessor ist bei mehreren Messungen nahezu vollständig ausgelastet",
            "reason_cpu_high_stable":
                "eine hohe CPU-Auslastung bleibt bestehen",
            "reason_cpu_spike":
                "eine kurzfristige CPU-Auslastungsspitze wurde erkannt",
            "reason_cpu_elevated":
                "die CPU-Auslastung bleibt hoch",

            "reason_ram_critical":
                "der Arbeitsspeicher ist nahezu vollständig belegt",
            "reason_ram_low":
                "nur wenig freier Arbeitsspeicher ist verfügbar",
            "reason_ram_active":
                "der Arbeitsspeicher wird stark beansprucht",

            "reason_disk_critical":
                "auf dem Systemlaufwerk ist fast kein freier Speicher mehr vorhanden",
            "reason_disk_low":
                "auf dem Systemlaufwerk ist nur wenig freier Speicher verfügbar",
            "reason_disk_full":
                "das Systemlaufwerk ist zu mehr als 80 % belegt",

            "reason_gpu_high":
                "die GPU ist stark ausgelastet",

            "rec_cpu_critical":
                "Kritische CPU-Auslastung",
            "rec_cpu_critical_msg":
                "Überprüfen Sie Prozesse mit hoher CPU-Auslastung.",
            "rec_cpu_high":
                "Hohe CPU-Auslastung",
            "rec_cpu_high_msg":
                "Die CPU ist längere Zeit mit etwa {cpu} % ausgelastet. "
                "Überprüfen Sie Hintergrundprozesse.",
            "rec_cpu_elevated":
                "Erhöhte CPU-Auslastung",
            "rec_cpu_elevated_msg":
                "Die aktuelle CPU-Auslastung beträgt etwa {cpu} %.",

            "rec_ram_critical":
                "Kritisch wenig RAM",
            "rec_ram_critical_msg":
                "Etwa {ram} % des Arbeitsspeichers werden verwendet. "
                "Schließen Sie nicht benötigte Anwendungen.",
            "rec_ram_high":
                "Hohe RAM-Auslastung",
            "rec_ram_high_msg":
                "Der Arbeitsspeicher ist zu etwa {ram} % belegt. "
                "Überprüfen Sie speicherintensive Anwendungen.",
            "rec_ram_active":
                "RAM wird stark beansprucht",
            "rec_ram_active_msg":
                "Überprüfen Sie Anwendungen, die viel Arbeitsspeicher verwenden.",

            "rec_disk_critical":
                "Kritisch wenig Speicherplatz",
            "rec_disk_critical_msg":
                "Auf dem Systemlaufwerk ist nur noch sehr wenig freier Speicher verfügbar.",
            "rec_disk_low":
                "Wenig freier Speicherplatz",
            "rec_disk_low_msg":
                "Das Systemlaufwerk ist zu {disk} % belegt. "
                "Löschen Sie nicht benötigte Dateien.",
            "rec_disk_full":
                "Datenträger fast voll",
            "rec_disk_full_msg":
                "{disk} % des Systemlaufwerks werden verwendet.",

            "rec_gpu_high":
                "Hohe GPU-Auslastung",
            "rec_gpu_high_msg":
                "Die GPU ist nahezu vollständig ausgelastet.",

            "rec_all_good":
                "Alles in Ordnung",
            "rec_all_good_msg":
                "Im aktuellen Systemzustand wurden keine kritischen Probleme festgestellt.",

            "msg_good_calm":
                "Das System läuft ruhig. "
                "Die Auslastung der wichtigsten Ressourcen liegt auf einem komfortablen Niveau.",
            "msg_good_stable":
                "Das System läuft stabil. "
                "CPU: {cpu} %, RAM: {ram} %, Datenträger: {disk} %. "
                "Keine kritischen Probleme wurden festgestellt.",
            "msg_attention":
                "Ich habe eine erhöhte Auslastung festgestellt: {reasons}.",
            "msg_attention_generic":
                "Einige Systemressourcen werden stärker als üblich verwendet. "
                "Es wurde kein kritischer Zustand festgestellt.",
            "msg_critical":
                "Aufmerksamkeit erforderlich. {reasons}.",
            "msg_ram_critical":
                "Der Arbeitsspeicher ist nahezu vollständig belegt. "
                "Dies kann das System verlangsamen.",
            "msg_disk_critical":
                "Auf dem Systemlaufwerk ist fast kein freier Speicher mehr vorhanden.",
            "msg_cpu_critical":
                "Der Prozessor ist bei mehreren Messungen nahezu vollständig ausgelastet.",
            "msg_critical_generic":
                "Es wurde ein Zustand erkannt, der die Aufmerksamkeit des Benutzers erfordert.",
            "msg_finished":
                "Systemanalyse abgeschlossen.",

            "diagnostic_invalid":
                "DiagnosticEngine hat ein ungültiges Ergebnis zurückgegeben.",
        },

        "it": {
            "user": "Utente",
            "unknown_gpu": "Scheda grafica sconosciuta",

            "reason_cpu_critical":
                "il processore è quasi completamente utilizzato da diverse rilevazioni",
            "reason_cpu_high_stable":
                "il carico elevato della CPU persiste",
            "reason_cpu_spike":
                "è stato rilevato un breve picco di carico della CPU",
            "reason_cpu_elevated":
                "il carico della CPU rimane elevato",

            "reason_ram_critical":
                "la memoria RAM è quasi completamente occupata",
            "reason_ram_low":
                "la memoria RAM libera è ridotta",
            "reason_ram_active":
                "la memoria RAM viene utilizzata intensamente",

            "reason_disk_critical":
                "sul disco di sistema è rimasto pochissimo spazio libero",
            "reason_disk_low":
                "lo spazio libero sul disco di sistema è ridotto",
            "reason_disk_full":
                "il disco di sistema è occupato per oltre l'80%",

            "reason_gpu_high":
                "la GPU è sottoposta a un carico elevato",

            "rec_cpu_critical":
                "Carico CPU critico",
            "rec_cpu_critical_msg":
                "Controlla i processi con un elevato utilizzo della CPU.",
            "rec_cpu_high":
                "Carico CPU elevato",
            "rec_cpu_high_msg":
                "La CPU è utilizzata da tempo a circa il {cpu}%. "
                "Controlla i processi in background.",
            "rec_cpu_elevated":
                "Carico CPU aumentato",
            "rec_cpu_elevated_msg":
                "Il carico attuale della CPU è circa il {cpu}%.",

            "rec_ram_critical":
                "RAM criticamente insufficiente",
            "rec_ram_critical_msg":
                "È utilizzato circa il {ram}% della memoria. "
                "Chiudi le applicazioni non necessarie.",
            "rec_ram_high":
                "Utilizzo elevato della RAM",
            "rec_ram_high_msg":
                "La RAM è occupata per circa il {ram}%. "
                "Controlla le applicazioni che utilizzano molta memoria.",
            "rec_ram_active":
                "RAM utilizzata intensamente",
            "rec_ram_active_msg":
                "Controlla le applicazioni che utilizzano molta memoria RAM.",

            "rec_disk_critical":
                "Spazio su disco criticamente ridotto",
            "rec_disk_critical_msg":
                "Sul disco di sistema è rimasto pochissimo spazio libero.",
            "rec_disk_low":
                "Poco spazio libero",
            "rec_disk_low_msg":
                "Il disco di sistema è occupato al {disk}%. "
                "Si consiglia di eliminare i file non necessari.",
            "rec_disk_full":
                "Disco quasi pieno",
            "rec_disk_full_msg":
                "È utilizzato il {disk}% del disco di sistema.",

            "rec_gpu_high":
                "Carico GPU elevato",
            "rec_gpu_high_msg":
                "La GPU è quasi completamente utilizzata.",

            "rec_all_good":
                "Tutto a posto",
            "rec_all_good_msg":
                "Non sono stati rilevati problemi critici nello stato attuale del sistema.",

            "msg_good_calm":
                "Il sistema funziona normalmente. "
                "L'utilizzo delle risorse principali è a un livello confortevole.",
            "msg_good_stable":
                "Il sistema funziona stabilmente. "
                "CPU: {cpu}%, RAM: {ram}%, disco: {disk}%. "
                "Non sono stati rilevati problemi critici.",
            "msg_attention":
                "Ho rilevato un carico elevato: {reasons}.",
            "msg_attention_generic":
                "Alcune risorse di sistema vengono utilizzate più del normale. "
                "Non è stata rilevata una condizione critica.",
            "msg_critical":
                "È richiesta attenzione. {reasons}.",
            "msg_ram_critical":
                "La memoria RAM è quasi completamente occupata. "
                "Questo può rallentare il sistema.",
            "msg_disk_critical":
                "Sul disco di sistema è rimasto pochissimo spazio libero.",
            "msg_cpu_critical":
                "Il processore è quasi completamente utilizzato "
                "da diverse rilevazioni.",
            "msg_critical_generic":
                "È stata rilevata una condizione che richiede l'attenzione dell'utente.",
            "msg_finished":
                "Analisi del sistema completata.",

            "diagnostic_invalid":
                "DiagnosticEngine ha restituito un risultato non valido.",
        },

        "es": {
            "user": "Usuario",
            "unknown_gpu": "GPU desconocida",

            "reason_cpu_critical":
                "el procesador ha estado casi completamente cargado durante varias mediciones",
            "reason_cpu_high_stable":
                "la carga elevada del procesador se mantiene",
            "reason_cpu_spike":
                "se ha detectado un pico breve de carga del procesador",
            "reason_cpu_elevated":
                "la carga del procesador sigue siendo alta",

            "reason_ram_critical":
                "la memoria RAM está casi completamente ocupada",
            "reason_ram_low":
                "queda poca memoria RAM libre",
            "reason_ram_active":
                "la memoria RAM se está utilizando intensamente",

            "reason_disk_critical":
                "queda muy poco espacio libre en la unidad del sistema",
            "reason_disk_low":
                "hay poco espacio libre en la unidad del sistema",
            "reason_disk_full":
                "la unidad del sistema está ocupada en más de un 80%",

            "reason_gpu_high":
                "la GPU está sometida a una carga elevada",

            "rec_cpu_critical":
                "Carga crítica de CPU",
            "rec_cpu_critical_msg":
                "Comprueba los procesos con un uso elevado de CPU.",
            "rec_cpu_high":
                "Carga elevada de CPU",
            "rec_cpu_high_msg":
                "La CPU lleva un tiempo funcionando aproximadamente al {cpu}%. "
                "Comprueba los procesos en segundo plano.",
            "rec_cpu_elevated":
                "Carga elevada de CPU",
            "rec_cpu_elevated_msg":
                "La carga actual de la CPU es aproximadamente del {cpu}%.",

            "rec_ram_critical":
                "RAM críticamente baja",
            "rec_ram_critical_msg":
                "Se utiliza aproximadamente el {ram}% de la memoria. "
                "Cierra las aplicaciones innecesarias.",
            "rec_ram_high":
                "Uso elevado de RAM",
            "rec_ram_high_msg":
                "La RAM está ocupada aproximadamente al {ram}%. "
                "Comprueba las aplicaciones que consumen mucha memoria.",
            "rec_ram_active":
                "Uso intensivo de RAM",
            "rec_ram_active_msg":
                "Comprueba las aplicaciones que utilizan mucha memoria RAM.",

            "rec_disk_critical":
                "Espacio en disco críticamente bajo",
            "rec_disk_critical_msg":
                "Queda muy poco espacio libre en la unidad del sistema.",
            "rec_disk_low":
                "Poco espacio libre",
            "rec_disk_low_msg":
                "La unidad del sistema está ocupada al {disk}%. "
                "Se recomienda eliminar archivos innecesarios.",
            "rec_disk_full":
                "Disco casi lleno",
            "rec_disk_full_msg":
                "Se utiliza el {disk}% de la unidad del sistema.",

            "rec_gpu_high":
                "Carga elevada de GPU",
            "rec_gpu_high_msg":
                "La GPU está casi completamente utilizada.",

            "rec_all_good":
                "Todo está bien",
            "rec_all_good_msg":
                "No se han detectado problemas críticos en el estado actual del sistema.",

            "msg_good_calm":
                "El sistema funciona con normalidad. "
                "El uso de los recursos principales está en un nivel cómodo.",
            "msg_good_stable":
                "El sistema funciona de forma estable. "
                "CPU: {cpu}%, RAM: {ram}%, disco: {disk}%. "
                "No se han detectado problemas críticos.",
            "msg_attention":
                "He detectado una carga elevada: {reasons}.",
            "msg_attention_generic":
                "Algunos recursos del sistema se utilizan más de lo habitual. "
                "No se ha detectado un estado crítico.",
            "msg_critical":
                "Se requiere atención. {reasons}.",
            "msg_ram_critical":
                "La memoria RAM está casi completamente ocupada. "
                "Esto puede ralentizar el sistema.",
            "msg_disk_critical":
                "Queda muy poco espacio libre en la unidad del sistema.",
            "msg_cpu_critical":
                "El procesador ha estado casi completamente cargado "
                "durante varias mediciones.",
            "msg_critical_generic":
                "Se ha detectado un estado que requiere la atención del usuario.",
            "msg_finished":
                "Análisis del sistema completado.",

            "diagnostic_invalid":
                "DiagnosticEngine devolvió un resultado no válido.",
        },

        "fr": {
            "user": "Utilisateur",
            "unknown_gpu": "Carte graphique inconnue",

            "reason_cpu_critical":
                "le processeur est presque entièrement sollicité depuis plusieurs mesures",
            "reason_cpu_high_stable":
                "la charge élevée du processeur persiste",
            "reason_cpu_spike":
                "un pic temporaire de charge du processeur a été détecté",
            "reason_cpu_elevated":
                "la charge du processeur reste élevée",

            "reason_ram_critical":
                "la mémoire vive est presque entièrement utilisée",
            "reason_ram_low":
                "il reste peu de mémoire vive disponible",
            "reason_ram_active":
                "la mémoire vive est fortement sollicitée",

            "reason_disk_critical":
                "il reste presque plus d'espace libre sur le disque système",
            "reason_disk_low":
                "l'espace libre sur le disque système est faible",
            "reason_disk_full":
                "le disque système est rempli à plus de 80 %",

            "reason_gpu_high":
                "le GPU est fortement sollicité",

            "rec_cpu_critical":
                "Charge CPU critique",
            "rec_cpu_critical_msg":
                "Vérifiez les processus qui utilisent beaucoup le processeur.",
            "rec_cpu_high":
                "Forte charge CPU",
            "rec_cpu_high_msg":
                "Le CPU fonctionne depuis un certain temps à environ {cpu} %. "
                "Vérifiez les processus en arrière-plan.",
            "rec_cpu_elevated":
                "Charge CPU élevée",
            "rec_cpu_elevated_msg":
                "La charge actuelle du CPU est d'environ {cpu} %.",

            "rec_ram_critical":
                "RAM extrêmement sollicitée",
            "rec_ram_critical_msg":
                "Environ {ram} % de la mémoire est utilisée. "
                "Fermez les applications inutiles.",
            "rec_ram_high":
                "Forte utilisation de la RAM",
            "rec_ram_high_msg":
                "La RAM est utilisée à environ {ram} %. "
                "Vérifiez les applications qui consomment beaucoup de mémoire.",
            "rec_ram_active":
                "RAM fortement sollicitée",
            "rec_ram_active_msg":
                "Vérifiez les applications qui utilisent beaucoup de mémoire vive.",

            "rec_disk_critical":
                "Espace disque critique",
            "rec_disk_critical_msg":
                "Il reste très peu d'espace libre sur le disque système.",
            "rec_disk_low":
                "Peu d'espace libre",
            "rec_disk_low_msg":
                "Le disque système est rempli à {disk} %. "
                "Il est recommandé de supprimer les fichiers inutiles.",
            "rec_disk_full":
                "Disque presque plein",
            "rec_disk_full_msg":
                "{disk} % du disque système sont actuellement utilisés.",

            "rec_gpu_high":
                "Forte charge GPU",
            "rec_gpu_high_msg":
                "Le GPU est presque entièrement sollicité.",

            "rec_all_good":
                "Tout va bien",
            "rec_all_good_msg":
                "Aucun problème critique n'a été détecté dans l'état actuel du système.",

            "msg_good_calm":
                "Le système fonctionne normalement. "
                "L'utilisation des principales ressources est à un niveau confortable.",
            "msg_good_stable":
                "Le système fonctionne de manière stable. "
                "CPU : {cpu} %, RAM : {ram} %, disque : {disk} %. "
                "Aucun problème critique n'a été détecté.",
            "msg_attention":
                "J'ai détecté une charge élevée : {reasons}.",
            "msg_attention_generic":
                "Certaines ressources système sont davantage sollicitées que d'habitude. "
                "Aucun état critique n'a été détecté.",
            "msg_critical":
                "Une attention est requise. {reasons}.",
            "msg_ram_critical":
                "La mémoire vive est presque entièrement utilisée. "
                "Cela peut ralentir le système.",
            "msg_disk_critical":
                "Il reste presque plus d'espace libre sur le disque système.",
            "msg_cpu_critical":
                "Le processeur est presque entièrement sollicité "
                "depuis plusieurs mesures.",
            "msg_critical_generic":
                "Un état nécessitant l'attention de l'utilisateur a été détecté.",
            "msg_finished":
                "Analyse du système terminée.",

            "diagnostic_invalid":
                "DiagnosticEngine a renvoyé un résultat incorrect.",
        },
    }

    # ==========================================================
    # INIT
    # ==========================================================

    def __init__(self):
        self.ui_language = getattr(
            type(self),
            "_active_language",
            "ru",
        )

        self.username = self._get_username()

        self.system_drive = os.environ.get(
            "SystemDrive",
            "C:",
        )

        self.cache_ttl = 2.0

        self._cache = None
        self._cache_time = 0.0

        self.diagnostic_engine = DiagnosticEngine()
        self.diagnostic_engine.set_language(
            self.ui_language
        )

        self.cpu_interval = 0.10

        self.history_size = 5
        self._recent_metrics = []

    # ==========================================================
    # LANGUAGE
    # ==========================================================

    def set_language(self, language):
        """
        Устанавливает язык AIAnalyzer.

        Поддерживаются:
        ru / en / uk / de / it / es / fr
        """

        language = str(language or "ru").lower().strip()

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language
        type(self)._active_language = language

        self.diagnostic_engine.set_language(
            language
        )
        # Username может быть локализованным fallback,
        # если реальное имя пользователя получить невозможно.
        self.username = self._get_username()

    def _tr(self, key, **kwargs):
        """
        Возвращает локализованную строку.
        """

        language = getattr(
            self,
            "ui_language",
            "ru",
        )

        translations = self.TRANSLATIONS.get(
            language,
            self.TRANSLATIONS["ru"],
        )

        text = translations.get(
            key,
            self.TRANSLATIONS["en"].get(
                key,
                key,
            ),
        )

        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text

    # ==========================================================
    # STATUS PRIORITY
    # ==========================================================

    @staticmethod
    def _status_priority(status: str) -> int:
        priorities = {
            "good": 0,
            "attention": 1,
            "critical": 2,
        }

        return priorities.get(
            str(status or "").lower(),
            0,
        )

    def _merge_statuses(
        self,
        analyzer_status: str,
        engine_status: str,
    ) -> str:

        analyzer_status = str(
            analyzer_status or "good"
        ).lower()

        engine_status = str(
            engine_status or "good"
        ).lower()

        if engine_status not in {
            "good",
            "attention",
            "critical",
        }:
            engine_status = "good"

        if analyzer_status not in {
            "good",
            "attention",
            "critical",
        }:
            analyzer_status = "good"

        if (
            self._status_priority(engine_status)
            > self._status_priority(analyzer_status)
        ):
            return engine_status

        return analyzer_status

    # ==========================================================
    # USERNAME
    # ==========================================================

    def _get_username(self) -> str:

        try:
            user_info = get_user_info()

            if isinstance(user_info, dict):
                username = user_info.get(
                    "username",
                    "",
                )

                if username:
                    return str(
                        username
                    ).strip()

        except Exception as exc:
            print(
                f"[AIAnalyzer] User info error: {exc}"
            )

        return self._tr("user")

    # ==========================================================
    # CPU
    # ==========================================================

    def _get_cpu_usage(self) -> dict:

        started = time.perf_counter()

        try:
            value = psutil.cpu_percent(
                interval=self.cpu_interval
            )

            value = float(value)

            value = max(
                0.0,
                min(
                    100.0,
                    value,
                ),
            )

        except Exception as exc:
            print(
                f"[AIAnalyzer] CPU error: {exc}"
            )

            value = 0.0

        elapsed = (
            time.perf_counter()
            - started
        )

        return {
            "usage": round(value, 1),
            "average": round(value, 1),
            "peak": round(value, 1),
            "samples": 1,
            "measurement_time": round(elapsed, 3),
        }

    # ==========================================================
    # RAM
    # ==========================================================

    def _get_ram_usage(self) -> dict:

        try:
            memory = psutil.virtual_memory()

            total = float(memory.total)
            used = float(memory.used)
            available = float(memory.available)

            percent = float(memory.percent)

            percent = max(
                0.0,
                min(
                    100.0,
                    percent,
                ),
            )

            return {
                "usage": round(percent, 1),
                "used": used,
                "total": total,
                "available": available,
                "used_gb": round(
                    used / (1024 ** 3),
                    2,
                ),
                "total_gb": round(
                    total / (1024 ** 3),
                    2,
                ),
                "available_gb": round(
                    available / (1024 ** 3),
                    2,
                ),
            }

        except Exception as exc:
            print(
                f"[AIAnalyzer] RAM error: {exc}"
            )

            return {
                "usage": 0.0,
                "used": 0.0,
                "total": 0.0,
                "available": 0.0,
                "used_gb": 0.0,
                "total_gb": 0.0,
                "available_gb": 0.0,
            }

    # ==========================================================
    # DISK
    # ==========================================================

    def _get_disk_usage(self) -> dict:

        try:
            disk = psutil.disk_usage(
                self.system_drive
            )

            usage = float(
                disk.percent
            )

            usage = max(
                0.0,
                min(
                    100.0,
                    usage,
                ),
            )

            return {
                "usage": round(usage, 1),
                "used": float(disk.used),
                "total": float(disk.total),
                "free": float(disk.free),
                "used_gb": round(
                    disk.used / (1024 ** 3),
                    2,
                ),
                "total_gb": round(
                    disk.total / (1024 ** 3),
                    2,
                ),
                "free_gb": round(
                    disk.free / (1024 ** 3),
                    2,
                ),
            }

        except Exception as exc:
            print(
                f"[AIAnalyzer] Disk error: {exc}"
            )

            return {
                "usage": 0.0,
                "used": 0.0,
                "total": 0.0,
                "free": 0.0,
                "used_gb": 0.0,
                "total_gb": 0.0,
                "free_gb": 0.0,
            }

    # ==========================================================
    # GPU
    # ==========================================================

    def _get_gpu_usage(self) -> dict:
        """
        GPU берётся только из общего cache.
        AIAnalyzer не запускает PowerShell и не делает
        самостоятельный GPU-запрос.
        """

        try:
            gpu = get_cached_gpu_info()

            if not isinstance(gpu, dict):
                gpu = {}

            name = str(
                gpu.get("name")
                or self._tr("unknown_gpu")
            ).strip()

            vendor = str(
                gpu.get("vendor")
                or "Unknown"
            ).strip()

            usage = gpu.get("usage")

            if usage is not None:
                try:
                    usage = float(usage)
                    usage = max(
                        0.0,
                        min(
                            100.0,
                            usage,
                        ),
                    )
                    usage = round(
                        usage,
                        1,
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    usage = None

            engine_keys = (
                "usage_3d",
                "usage_compute",
                "usage_video_decode",
                "usage_video_encode",
            )

            for key in engine_keys:
                value = gpu.get(key)

                if value is None:
                    gpu[key] = None
                    continue

                try:
                    value = float(value)

                    value = max(
                        0.0,
                        min(
                            100.0,
                            value,
                        ),
                    )

                    gpu[key] = round(
                        value,
                        1,
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    gpu[key] = None

            unknown_names = {
                "Неизвестная видеокарта",
                "Unknown GPU",
                "Невідома відеокарта",
                "Unbekannte Grafikkarte",
                "Scheda grafica sconosciuta",
                "GPU desconocida",
                "Carte graphique inconnue",
            }

            available = bool(
                name
                and name not in unknown_names
            )

            return {
                "name": name,
                "vendor": vendor,
                "usage": usage,
                "usage_3d": gpu.get("usage_3d"),
                "usage_compute": gpu.get("usage_compute"),
                "usage_video_decode": gpu.get(
                    "usage_video_decode"
                ),
                "usage_video_encode": gpu.get(
                    "usage_video_encode"
                ),
                "driver": gpu.get("driver"),
                "memory": gpu.get("memory"),
                "available": available,
            }

        except Exception as exc:
            print(
                "[AIAnalyzer] GPU cache error:",
                repr(exc),
            )

            return {
                "name": self._tr("unknown_gpu"),
                "vendor": "Unknown",
                "usage": None,
                "usage_3d": None,
                "usage_compute": None,
                "usage_video_decode": None,
                "usage_video_encode": None,
                "driver": None,
                "memory": None,
                "available": False,
            }

    # ==========================================================
    # SYSTEM INFO
    # ==========================================================

    def _get_system_info(self) -> dict:

        try:
            return {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            }

        except Exception as exc:
            print(
                f"[AIAnalyzer] System info error: {exc}"
            )

            return {
                "system": "Unknown",
                "release": "",
                "version": "",
                "machine": "",
                "processor": "",
            }

    # ==========================================================
    # RECENT METRICS
    # ==========================================================

    def _remember_metrics(
        self,
        cpu: dict,
        ram: dict,
        disk: dict,
        gpu: dict,
    ) -> None:

        gpu_usage = gpu.get("usage")

        try:
            if gpu_usage is not None:
                gpu_usage = float(gpu_usage)

        except (
            TypeError,
            ValueError,
        ):
            gpu_usage = None

        sample = {
            "timestamp": time.time(),

            "cpu": float(
                cpu.get(
                    "usage",
                    0,
                )
                or 0
            ),

            "ram": float(
                ram.get(
                    "usage",
                    0,
                )
                or 0
            ),

            "disk": float(
                disk.get(
                    "usage",
                    0,
                )
                or 0
            ),

            "gpu": gpu_usage,
        }

        self._recent_metrics.append(
            sample
        )

        if len(
            self._recent_metrics
        ) > self.history_size:

            self._recent_metrics = (
                self._recent_metrics[
                    -self.history_size:
                ]
            )

    # ==========================================================
    # CPU STABILITY
    # ==========================================================

    def _get_cpu_stability(self) -> dict:

        if not self._recent_metrics:
            return {
                "stable_high": False,
                "samples": 0,
                "average": 0.0,
                "peak": 0.0,
                "high_samples": 0,
            }

        cpu_values = []

        for item in self._recent_metrics:
            try:
                value = float(
                    item.get(
                        "cpu",
                        0,
                    )
                    or 0
                )

            except (
                TypeError,
                ValueError,
            ):
                value = 0.0

            cpu_values.append(
                value
            )

        if not cpu_values:
            return {
                "stable_high": False,
                "samples": 0,
                "average": 0.0,
                "peak": 0.0,
                "high_samples": 0,
            }

        peak = max(cpu_values)

        average = (
            sum(cpu_values)
            / len(cpu_values)
        )

        last_three = cpu_values[-3:]

        high_samples = sum(
            1
            for value in last_three
            if value >= 90
        )

        stable_high = (
            len(last_three) >= 3
            and high_samples >= 3
        )

        return {
            "stable_high": stable_high,
            "samples": len(cpu_values),
            "average": round(
                average,
                1,
            ),
            "peak": round(
                peak,
                1,
            ),
            "high_samples": high_samples,
        }

    # ==========================================================
    # STATUS
    # ==========================================================

    def _calculate_status(
        self,
        cpu,
        ram,
        disk,
        gpu,
        cpu_stability=None,
    ):
        """
        Определяет состояние системы.

        Возвращает:
            status
            critical_reasons
            attention_reasons
        """

        critical_reasons = []
        attention_reasons = []

        # ------------------------------------------------------
        # CPU STABILITY
        # ------------------------------------------------------

        if cpu_stability is None:
            cpu_stability = self._get_cpu_stability()

        if isinstance(cpu_stability, dict):
            stable_high = bool(
                cpu_stability.get(
                    "stable_high",
                    False,
                )
            )
        else:
            stable_high = (
                str(cpu_stability).lower()
                == "high"
            )

        # ------------------------------------------------------
        # CPU
        # ------------------------------------------------------

        if cpu >= 95:
            critical_reasons.append(
                self._tr(
                    "reason_cpu_critical"
                )
            )

        elif cpu >= 85:

            if stable_high:
                attention_reasons.append(
                    self._tr(
                        "reason_cpu_high_stable"
                    )
                )

            else:
                attention_reasons.append(
                    self._tr(
                        "reason_cpu_spike"
                    )
                )

        elif cpu >= 70:
            attention_reasons.append(
                self._tr(
                    "reason_cpu_elevated"
                )
            )

        # ------------------------------------------------------
        # RAM
        # ------------------------------------------------------

        if ram >= 95:
            critical_reasons.append(
                self._tr(
                    "reason_ram_critical"
                )
            )

        elif ram >= 85:
            attention_reasons.append(
                self._tr(
                    "reason_ram_low"
                )
            )

        elif ram >= 75:
            attention_reasons.append(
                self._tr(
                    "reason_ram_active"
                )
            )

        # ------------------------------------------------------
        # DISK
        # ------------------------------------------------------

        if disk >= 95:
            critical_reasons.append(
                self._tr(
                    "reason_disk_critical"
                )
            )

        elif disk >= 90:
            attention_reasons.append(
                self._tr(
                    "reason_disk_low"
                )
            )

        elif disk >= 80:
            attention_reasons.append(
                self._tr(
                    "reason_disk_full"
                )
            )

        # ------------------------------------------------------
        # GPU
        # ------------------------------------------------------

        gpu_usage = 0

        if isinstance(gpu, dict):
            try:
                gpu_usage = float(
                    gpu.get("usage")
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                gpu_usage = 0

        if gpu_usage >= 90:
            attention_reasons.append(
                self._tr(
                    "reason_gpu_high"
                )
            )

        # ------------------------------------------------------
        # FINAL STATUS
        # ------------------------------------------------------

        if critical_reasons:
            status = "critical"

        elif attention_reasons:
            status = "attention"

        else:
            status = "good"

        return {
            "status": status,
            "critical_reasons": critical_reasons,
            "attention_reasons": attention_reasons,
            "cpu_stability": {
                "stable_high": stable_high,
            },
        }

    # ==========================================================
    # MESSAGE
    # ==========================================================

    def _build_message(
        self,
        status: str,
        cpu: dict,
        ram: dict,
        disk: dict,
        gpu: dict,
        status_data: dict,
    ) -> str:

        try:
            cpu_value = float(
                cpu.get(
                    "usage",
                    0,
                )
                or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            cpu_value = 0.0

        try:
            ram_value = float(
                ram.get(
                    "usage",
                    0,
                )
                or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            ram_value = 0.0

        try:
            disk_value = float(
                disk.get(
                    "usage",
                    0,
                )
                or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            disk_value = 0.0

        gpu_value = None

        if isinstance(gpu, dict):
            try:
                if gpu.get("usage") is not None:
                    gpu_value = float(
                        gpu.get("usage")
                    )
            except (
                TypeError,
                ValueError,
            ):
                gpu_value = None

        cpu_stability = status_data.get(
            "cpu_stability",
            {},
        )

        stable_high = bool(
            cpu_stability.get(
                "stable_high",
                False,
            )
        )

        # ======================================================
        # GOOD
        # ======================================================

        if status == "good":

            if (
                cpu_value < 50
                and ram_value < 70
                and disk_value < 80
            ):
                return self._tr(
                    "msg_good_calm"
                )

            return self._tr(
                "msg_good_stable",
                cpu=f"{cpu_value:.0f}",
                ram=f"{ram_value:.0f}",
                disk=f"{disk_value:.0f}",
            )

        # ======================================================
        # ATTENTION
        # ======================================================

        if status == "attention":

            reasons = []

            if cpu_value >= 90:

                if stable_high:
                    reasons.append(
                        self._tr(
                            "reason_cpu_high_stable"
                        )
                    )
                else:
                    reasons.append(
                        self._tr(
                            "reason_cpu_spike"
                        )
                    )

            elif cpu_value >= 80:
                reasons.append(
                    self._tr(
                        "reason_cpu_elevated"
                    )
                )

            if ram_value >= 90:
                reasons.append(
                    self._tr(
                        "reason_ram_critical"
                    )
                )

            elif ram_value >= 80:
                reasons.append(
                    self._tr(
                        "reason_ram_active"
                    )
                )

            if disk_value >= 90:
                reasons.append(
                    self._tr(
                        "reason_disk_low"
                    )
                )

            elif disk_value >= 80:
                reasons.append(
                    self._tr(
                        "reason_disk_full"
                    )
                )

            if (
                gpu_value is not None
                and gpu_value >= 98
            ):
                reasons.append(
                    self._tr(
                        "reason_gpu_high"
                    )
                )

            if reasons:
                return self._tr(
                    "msg_attention",
                    reasons="; ".join(
                        reasons[:2]
                    ),
                )

            return self._tr(
                "msg_attention_generic"
            )

        # ======================================================
        # CRITICAL
        # ======================================================

        if status == "critical":

            reasons = status_data.get(
                "critical_reasons",
                [],
            )

            if reasons:
                return self._tr(
                    "msg_critical",
                    reasons="; ".join(
                        reasons[:2]
                    ),
                )

            if ram_value >= 95:
                return self._tr(
                    "msg_ram_critical"
                )

            if disk_value >= 97:
                return self._tr(
                    "msg_disk_critical"
                )

            if (
                cpu_value >= 95
                and stable_high
            ):
                return self._tr(
                    "msg_cpu_critical"
                )

            return self._tr(
                "msg_critical_generic"
            )

        return self._tr(
            "msg_finished"
        )

    # ==========================================================
    # RECOMMENDATIONS
    # ==========================================================

    def _build_recommendations(
        self,
        cpu,
        ram,
        disk,
        gpu,
        status,
    ):
        """
        Формирует локализованные рекомендации.
        """

        recommendations = []

        # ------------------------------------------------------
        # CPU
        # ------------------------------------------------------

        if cpu >= 95:

            recommendations.append({
                "title": self._tr(
                    "rec_cpu_critical"
                ),
                "message": self._tr(
                    "rec_cpu_critical_msg"
                ),
                "type": "critical",
            })

        elif cpu >= 85:

            recommendations.append({
                "title": self._tr(
                    "rec_cpu_high"
                ),
                "message": self._tr(
                    "rec_cpu_high_msg",
                    cpu=round(cpu),
                ),
                "type": "warning",
            })

        elif cpu >= 70:

            recommendations.append({
                "title": self._tr(
                    "rec_cpu_elevated"
                ),
                "message": self._tr(
                    "rec_cpu_elevated_msg",
                    cpu=round(cpu),
                ),
                "type": "info",
            })

        # ------------------------------------------------------
        # RAM
        # ------------------------------------------------------

        if ram >= 95:

            recommendations.append({
                "title": self._tr(
                    "rec_ram_critical"
                ),
                "message": self._tr(
                    "rec_ram_critical_msg",
                    ram=round(ram),
                ),
                "type": "critical",
            })

        elif ram >= 85:

            recommendations.append({
                "title": self._tr(
                    "rec_ram_high"
                ),
                "message": self._tr(
                    "rec_ram_high_msg",
                    ram=round(ram),
                ),
                "type": "warning",
            })

        elif ram >= 75:

            recommendations.append({
                "title": self._tr(
                    "rec_ram_active"
                ),
                "message": self._tr(
                    "rec_ram_active_msg"
                ),
                "type": "info",
            })

        # ------------------------------------------------------
        # DISK
        # ------------------------------------------------------

        if disk >= 95:

            recommendations.append({
                "title": self._tr(
                    "rec_disk_critical"
                ),
                "message": self._tr(
                    "rec_disk_critical_msg"
                ),
                "type": "critical",
            })

        elif disk >= 90:

            recommendations.append({
                "title": self._tr(
                    "rec_disk_low"
                ),
                "message": self._tr(
                    "rec_disk_low_msg",
                    disk=round(disk),
                ),
                "type": "warning",
            })

        elif disk >= 80:

            recommendations.append({
                "title": self._tr(
                    "rec_disk_full"
                ),
                "message": self._tr(
                    "rec_disk_full_msg",
                    disk=round(disk),
                ),
                "type": "info",
            })

        # ------------------------------------------------------
        # GPU
        # ------------------------------------------------------

        gpu_usage = 0

        if isinstance(gpu, dict):
            try:
                gpu_usage = float(
                    gpu.get("usage")
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                gpu_usage = 0

        if gpu_usage >= 90:

            recommendations.append({
                "title": self._tr(
                    "rec_gpu_high"
                ),
                "message": self._tr(
                    "rec_gpu_high_msg"
                ),
                "type": "warning",
            })

        # ------------------------------------------------------
        # NO PROBLEMS
        # ------------------------------------------------------

        if not recommendations:

            recommendations.append({
                "title": self._tr(
                    "rec_all_good"
                ),
                "message": self._tr(
                    "rec_all_good_msg"
                ),
                "type": "good",
            })

        return recommendations

    # ==========================================================
    # ANALYZE
    # ==========================================================

    def analyze(self) -> dict:

        started = time.perf_counter()

        print(
            "[AIAnalyzer] Starting system analysis..."
        )

        # ======================================================
        # CPU
        # ======================================================

        step = time.perf_counter()

        cpu = self._get_cpu_usage()

        cpu_time = (
            time.perf_counter()
            - step
        )

        # ======================================================
        # RAM
        # ======================================================

        step = time.perf_counter()

        ram = self._get_ram_usage()

        ram_time = (
            time.perf_counter()
            - step
        )

        # ======================================================
        # DISK
        # ======================================================

        step = time.perf_counter()

        disk = self._get_disk_usage()

        disk_time = (
            time.perf_counter()
            - step
        )

        # ======================================================
        # GPU
        # ======================================================

        step = time.perf_counter()

        gpu = self._get_gpu_usage()

        gpu_time = (
            time.perf_counter()
            - step
        )

        # ======================================================
        # SYSTEM
        # ======================================================

        step = time.perf_counter()

        system = self._get_system_info()

        system_time = (
            time.perf_counter()
            - step
        )

        # ======================================================
        # REMEMBER
        # ======================================================

        self._remember_metrics(
            cpu,
            ram,
            disk,
            gpu,
        )

        # ======================================================
        # CPU STABILITY
        # ======================================================

        cpu_stability = (
            self._get_cpu_stability()
        )

        # ======================================================
        # LOCAL STATUS
        # ======================================================

        status_data = self._calculate_status(
            float(cpu.get("usage", 0) or 0),
            float(ram.get("usage", 0) or 0),
            float(disk.get("usage", 0) or 0),
            gpu,
            cpu_stability,
        )

        status_data["cpu_stability"] = (
            cpu_stability
        )

        # ======================================================
        # DIAGNOSTIC ENGINE
        # ======================================================

        try:

            diagnostics = (
                self.diagnostic_engine.analyze(
                    cpu,
                    ram,
                    disk,
                    gpu,
                    cpu_stability=cpu_stability,
                )
            )

            if not isinstance(
                diagnostics,
                dict,
            ):

                diagnostics = {
                    "status":
                        status_data.get(
                            "status",
                            "good",
                        ),
                    "has_problems": False,
                    "problem_count": 0,
                    "problems": [],
                    "critical_problems": [],
                    "high_problems": [],
                    "medium_problems": [],
                    "recovered": [],
                    "history_size": 0,
                    "error": self._tr(
                        "diagnostic_invalid"
                    ),
                }

        except Exception as exc:

            print(
                f"[AIAnalyzer] DiagnosticEngine error: {exc}"
            )

            diagnostics = {
                "status": status_data.get(
                    "status",
                    "good",
                ),
                "has_problems": False,
                "problem_count": 0,
                "problems": [],
                "critical_problems": [],
                "high_problems": [],
                "medium_problems": [],
                "recovered": [],
                "history_size": 0,
                "error": str(exc),
            }

        status_data["engine"] = diagnostics

        # ======================================================
        # DIAGNOSTIC RECOMMENDATIONS
        # ======================================================

        try:

            diagnostic_recommendations = (
                self.diagnostic_engine
                .build_recommendations(
                    diagnostics
                )
            )

            if not isinstance(
                diagnostic_recommendations,
                list,
            ):
                diagnostic_recommendations = []

        except Exception as exc:

            print(
                "[AIAnalyzer] "
                f"Diagnostic recommendations error: {exc}"
            )

            diagnostic_recommendations = []

        status_data[
            "engine_recommendations"
        ] = diagnostic_recommendations

        # ======================================================
        # SYNCHRONIZE STATUS
        # ======================================================

        analyzer_status = status_data.get(
            "status",
            "good",
        )

        engine_status = diagnostics.get(
            "status",
            "good",
        )

        status = self._merge_statuses(
            analyzer_status,
            engine_status,
        )

        status_data["status"] = status

        # ======================================================
        # MESSAGE
        # ======================================================

        message = self._build_message(
            status,
            cpu,
            ram,
            disk,
            gpu,
            status_data,
        )

        # ======================================================
        # RECOMMENDATIONS
        # ======================================================

        recommendations = (
            self._build_recommendations(
                float(cpu.get("usage", 0) or 0),
                float(ram.get("usage", 0) or 0),
                float(disk.get("usage", 0) or 0),
                gpu,
                status,
            )
        )

        # ======================================================
        # TOTAL TIME
        # ======================================================

        analysis_time = round(
            time.perf_counter()
            - started,
            3,
        )

        # ======================================================
        # RESULT
        # ======================================================

        result = {
            "username": self.username,

            "status": status,

            "message": message,

            "recommendations":
                recommendations,

            "data": {
                "cpu": cpu,
                "ram": ram,
                "disk": disk,
                "gpu": gpu,
                "system": system,
            },

            "analysis": {
                "critical_reasons":
                    status_data.get(
                        "critical_reasons",
                        [],
                    ),

                "attention_reasons":
                    status_data.get(
                        "attention_reasons",
                        [],
                    ),

                "cpu_stability":
                    cpu_stability,

                "diagnostic":
                    diagnostics,

                "diagnostics":
                    diagnostics,

                "diagnostic_recommendations":
                    diagnostic_recommendations,

                "analysis_time":
                    analysis_time,

                "timing": {
                    "cpu":
                        round(
                            cpu_time,
                            3,
                        ),

                    "ram":
                        round(
                            ram_time,
                            3,
                        ),

                    "disk":
                        round(
                            disk_time,
                            3,
                        ),

                    "gpu":
                        round(
                            gpu_time,
                            3,
                        ),

                    "system":
                        round(
                            system_time,
                            3,
                        ),
                },
            },
        }

        # ======================================================
        # CACHE
        # ======================================================

        self._cache = result

        self._cache_time = (
            time.perf_counter()
        )

        # ======================================================
        # GPU LOG
        # ======================================================

        gpu_value = gpu.get(
            "usage"
        )

        if gpu_value is None:

            gpu_text = "N/A"

        else:

            try:
                gpu_text = (
                    f"{float(gpu_value):.1f}"
                )

            except (
                TypeError,
                ValueError,
            ):
                gpu_text = "N/A"

        # ======================================================
        # PERFORMANCE PROFILE
        # ======================================================

        print()
        print(
            "================================================"
        )
        print(
            "[AIAnalyzer] PERFORMANCE PROFILE"
        )
        print(
            "================================================"
        )

        print(
            f"CPU     : {cpu_time:.3f}s"
        )
        print(
            f"RAM     : {ram_time:.3f}s"
        )
        print(
            f"DISK    : {disk_time:.3f}s"
        )
        print(
            f"GPU     : {gpu_time:.3f}s"
        )
        print(
            f"SYSTEM  : {system_time:.3f}s"
        )

        print(
            "------------------------------------------------"
        )

        print(
            f"TOTAL   : {analysis_time:.3f}s"
        )

        print(
            "------------------------------------------------"
        )

        print(
            f"user={self.username}"
        )

        print(
            f"language={self.ui_language}"
        )

        print(
            f"status={status}"
        )

        print(
            f"CPU={cpu.get('usage', 0):.1f}%"
        )

        print(
            f"RAM={ram.get('usage', 0):.1f}%"
        )

        print(
            f"DISK={disk.get('usage', 0):.1f}%"
        )

        print(
            f"GPU={gpu_text}"
        )

        print(
            f"cpu_history="
            f"{cpu_stability.get('samples', 0)}"
        )

        print(
            f"cpu_stable_high="
            f"{cpu_stability.get('stable_high', False)}"
        )

        print(
            f"cpu_high_samples="
            f"{cpu_stability.get('high_samples', 0)}"
        )

        print(
            f"diagnostic_status="
            f"{diagnostics.get('status', 'unknown')}"
        )

        print(
            f"diagnostic_problems="
            f"{diagnostics.get('problem_count', 0)}"
        )

        print(
            f"diagnostic_recovered="
            f"{len(diagnostics.get('recovered', []))}"
        )

        print(
            "================================================"
        )
        print()

        return result


# ==============================================================
# GLOBAL ANALYZER
# ==============================================================

_analyzer = AIAnalyzer()


def analyze_system(language=None) -> dict:
    """
    Совместимый внешний интерфейс для Dashboard и AIWorker.

    Использует один постоянный экземпляр AIAnalyzer.

    Если language передан, язык глобального анализатора
    переключается перед новым анализом.
    """

    if language is not None:
        _analyzer.set_language(
            language
        )

    return _analyzer.analyze()