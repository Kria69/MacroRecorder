"""Локализация интерфейса."""

CURRENT_LANG = "en"

TRANSLATIONS = {
    "en": {
        "app_title": "Macro Recorder Pro",
        "ok": "OK",
        "yes": "Yes",
        "no": "No",
        "warning_title": "Warning",
        "error_title": "Error",
        "info_title": "Information",
        "confirm_clear_title": "Confirm Clear",
        "confirm_clear_msg": "Clear macro and reset name?",
        "hotkey_settings_title": "Hotkey Settings",
        "configure_hotkeys": "Configure Global Hotkeys",
        "press_combination": "Press combination...",
        "reset_defaults": "Reset Defaults",
        "forbidden_keys_msg": "Space and Win keys are not allowed!",
        "act_record_start": "Start Recording",
        "act_record_stop": "Stop Recording",
        "act_record_pause": "Pause/Resume Recording",
        "act_play_start": "Start Playback",
        "act_play_stop": "Stop Playback",
        "act_play_pause": "Pause/Resume Playback",
        "act_save_profile": "Save Profile",
        "act_clear_profile": "Clear Profile",
        "act_rename_profile": "Rename Profile",
        "act_quit_app": "Exit App",
        "rename_title": "Rename Profile",
        "new_name": "New Name:",
        "select_profile": "Select Profile:",
        "profile_default_name": "Profile {n}",
        "btn_rename": "Rename",
        "btn_record": "● Record",
        "btn_stop": "■ Stop",
        "btn_pause_rec": "|| Pause Rec",
        "btn_resume": "|| Resume",
        "btn_play": "▶ Play",
        "btn_pause_play": "|| Pause Play",
        "btn_save": "Save",
        "btn_clear": "Clear",
        "lbl_profile": "Profile:",
        "lbl_state": "State:",
        "state_records_exist": "Records exist",
        "state_recording": "RECORDING [{t}]",
        "state_recording_paused": "RECORDING (PAUSED)",
        "state_playing": "PLAYING [{cur} / {tot}]",
        "state_playing_paused": "PLAYING (PAUSED)",
        "event_log": "Event Log:",
        "menu_file": "File",
        "menu_save": "Save",
        "menu_help": "Help",
        "menu_exit": "Exit",
        "menu_settings": "Settings",
        "menu_hotkeys": "Hotkeys...",
        "menu_admin": "Admin Panel...",
        "menu_language": "Language",
        "menu_theme": "Theme",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "menu_profile": "Profile",
        "menu_rename": "Rename...",
        "menu_clear": "Clear",
        "menu_export": "Export Profile...",
        "menu_import": "Import Profile...",
        "export_dialog_title": "Export Profile",
        "import_dialog_title": "Import Profile",
        "file_filter_json": "Macro profile (*.json *.json.gz)",
        "confirm_import_title": "Confirm Import",
        "confirm_import_msg": "Import will overwrite the current profile. Continue?",
        "import_bad_format": "Invalid profile file format!",
        "import_error": "Failed to import profile!",
        "export_error": "Failed to export profile!",
        "log_profile_exported": "Profile {pid} exported to '{path}'.",
        "log_profile_imported": "Profile imported into slot {pid} from '{path}'.",
        "tt_start": "Start",
        "tt_stop": "Stop",
        "tt_pause_resume": "Pause/Resume",
        "tt_save": "Save",
        "tt_clear": "Clear",
        "tt_rename": "Rename current profile",
        "name_exists": "Name already exists!",
        "no_events": "No events to play!",
        "help_title": "Help",
        "help_text": (
            "<h3>Macro Recorder Pro — Help</h3>"
            "<p><b>Recording:</b><br>"
            "Press <b>Record</b> (F5) to start capturing keyboard and mouse events. "
            "Press <b>Stop</b> (F6) to finish. Use <b>Pause Rec</b> (Alt+P) to pause and resume recording.</p>"
            "<p><b>Playback:</b><br>"
            "Press <b>Play</b> (F7) to replay the recorded macro. "
            "Press <b>Stop</b> (F8) to interrupt. Use <b>Pause Play</b> (Alt+O) to pause and resume playback. "
            "The keyboard layout is synchronized automatically with the layout used during recording.</p>"
            "<p><b>Profiles:</b><br>"
            "There are 10 profiles available. Select a profile from the drop-down list. "
            "<b>Save</b> (Alt+S) stores the macro, <b>Clear</b> (Alt+C) removes it and resets the name, "
            "<b>Rename</b> (Alt+R) changes the profile name.</p>"
            "<p><b>Import / Export:</b><br>"
            "Profile → Export Profile... saves the current profile to a .json or .json.gz file. "
            "Profile → Import Profile... loads a profile file into the current slot (with confirmation).</p>"
            "<p><b>Hotkeys:</b><br>"
            "Settings → Hotkeys... lets you reassign any global hotkey. "
            "Keys are always displayed in the English layout. "
            "Space and Win keys are not allowed in hotkeys.</p>"
            "<p><b>Language &amp; Theme:</b><br>"
            "Settings → Language switches the interface between English and Russian. "
            "Settings → Theme switches between Light and Dark themes. "
            "Both choices are saved automatically.</p>"
            "<p><b>Debug Mode:</b><br>"
            "Settings → Admin Panel → Debug Mode enables detailed technical logging of recorded and played events.</p>"
            "<hr>"
            "<p><b>Administrator Privileges (UAC):</b><br>"
            "The app works without admin rights for most tasks. However, Windows isolates "
            "privileged windows (User Interface Privilege Isolation — UIPI). This means:</p>"
            "<ul>"
            "<li><b>Without admin rights:</b> global hotkeys (F5/F7/etc.) and macro playback "
            "work in normal user applications (browser, Office, Notepad, most games), but "
            "<b>will not work</b> in windows running as Administrator (Task Manager, elevated "
            "Command Prompt, installers, some anti-cheat protected games).</li>"
            "<li><b>With admin rights:</b> hotkeys and synthetic input work across <b>all</b> "
            "windows in the system, including elevated ones.</li>"
            "</ul>"
            "<p><b>When do you need to elevate?</b></p>"
            "<ul>"
            "<li>Your macro targets a window that runs as Administrator.</li>"
            "<li>Global hotkeys stop responding in certain applications.</li>"
            "<li>You automate system tools (regedit, elevated cmd, installers).</li>"
            "</ul>"
            "<p><b>How to elevate:</b> open <b>Settings → Admin Panel</b> and click "
            "<b>Restart as Administrator</b>. Windows will show a UAC prompt — click Yes. "
            "The app will restart with full privileges. If you deny the UAC prompt, the app "
            "continues running as a normal user.</p>"
            "<p><b>Note:</b> Some games with kernel-level anti-cheat (EasyAntiCheat, BattlEye, "
            "Vanguard) may still block synthetic input even from an elevated process. In such "
            "cases, macro playback inside the game may be limited regardless of admin rights.</p>"
        ),
        "admin_title": "Admin Panel",
        "admin_status": "Status:",
        "admin_is_admin": "Administrator",
        "admin_is_user": "User (no admin rights)",
        "admin_restart": "Restart as Administrator",
        "admin_restart_hint": "The app will close and request UAC elevation.",
        "admin_hotkeys": "Registered hotkeys:",
        "admin_layout": "Current layout:",
        "admin_uac_denied": "UAC elevation denied or failed. Running as user.",
        "admin_debug_mode": "Debug Mode",
        "admin_debug_hint": "Enables detailed technical logging of recorded and played events.",
        "admin_logs_btn": "Logs",
        "admin_clear_logs_btn": "Clear Logs",
        "admin_logs_title": "Application Logs",
        "confirm_clear_logs_title": "Confirm Clear Logs",
        "confirm_clear_logs_msg": "Delete all log files? This cannot be undone.",
        "log_system_ready": "System Ready.",
        "log_cannot_record_playing": "Cannot record while playing.",
        "log_cannot_play_recording": "Cannot play while recording.",
        "log_recording_started": "Recording started...",
        "log_recording_paused": "Recording paused.",
        "log_recording_resumed": "Recording resumed.",
        "log_stopped_events": "Stopped. {n} events recorded.",
        "log_playback_started": "Playback started...",
        "log_playback_paused": "Playback paused.",
        "log_playback_resumed": "Playback resumed.",
        "log_playback_finished": "Playback finished.",
        "log_profile_saved": "Profile {pid} saved successfully.",
        "log_profile_cleared": "Profile {pid} cleared.",
        "log_hotkeys_updated": "Hotkeys configuration updated.",
        "log_debug_enabled": "Debug mode ENABLED",
        "log_debug_disabled": "Debug mode DISABLED",
        "log_layout_mismatch": "LAYOUT MISMATCH DETECTED! Recorded: {rec}, Current: {cur}. Switching...",
        "log_layout_synced": "Layout successfully synchronized.",
        "log_layout_failed": "WARNING: Failed to sync layout. Text input may be incorrect.",
        "log_lang_changed": "Language changed to English.",
        "log_theme_changed": "Theme changed to Light.",
        "log_cannot_change_profile": "Cannot change profile during recording or playback.",
        "layout_suffix": "layout",
    },
    "ru": {
        "app_title": "Macro Recorder Pro",
        "ok": "OK",
        "yes": "Да",
        "no": "Нет",
        "warning_title": "Предупреждение",
        "error_title": "Ошибка",
        "info_title": "Информация",
        "confirm_clear_title": "Подтверждение очистки",
        "confirm_clear_msg": "Очистить макрос и сбросить имя?",
        "hotkey_settings_title": "Настройки горячих клавиш",
        "configure_hotkeys": "Настройка глобальных горячих клавиш",
        "press_combination": "Нажмите комбинацию...",
        "reset_defaults": "Сбросить по умолчанию",
        "forbidden_keys_msg": "Клавиши Space и Win запрещены!",
        "act_record_start": "Начать запись",
        "act_record_stop": "Остановить запись",
        "act_record_pause": "Пауза/Продолжить\nзапись",
        "act_play_start": "Начать воспроизведение",
        "act_play_stop": "Остановить\nвоспроизведение",
        "act_play_pause": "Пауза/Продолжить\nвоспроизведение",
        "act_save_profile": "Сохранить профиль",
        "act_clear_profile": "Очистить профиль",
        "act_rename_profile": "Переименовать профиль",
        "act_quit_app": "Выход из приложения",
        "rename_title": "Переименование профиля",
        "new_name": "Новое имя:",
        "select_profile": "Выбор профиля:",
        "profile_default_name": "Профиль {n}",
        "btn_rename": "Переименовать",
        "btn_record": "● Запись",
        "btn_stop": "■ Стоп",
        "btn_pause_rec": "|| Пауза зап.",
        "btn_resume": "|| Продолжить",
        "btn_play": "▶ Пуск",
        "btn_pause_play": "|| Пауза воспр.",
        "btn_save": "Сохранить",
        "btn_clear": "Очистить",
        "lbl_profile": "Профиль:",
        "lbl_state": "Состояние:",
        "state_records_exist": "Есть запись",
        "state_recording": "ЗАПИСЬ [{t}]",
        "state_recording_paused": "ЗАПИСЬ (ПАУЗА)",
        "state_playing": "ВОСПРОИЗВЕДЕНИЕ [{cur} / {tot}]",
        "state_playing_paused": "ВОСПРОИЗВЕДЕНИЕ (ПАУЗА)",
        "event_log": "Журнал событий:",
        "menu_file": "Файл",
        "menu_save": "Сохранить",
        "menu_help": "Справка",
        "menu_exit": "Выход",
        "menu_settings": "Настройки",
        "menu_hotkeys": "Горячие клавиши...",
        "menu_admin": "Панель администратора...",
        "menu_language": "Язык",
        "menu_theme": "Тема",
        "theme_light": "Светлая",
        "theme_dark": "Тёмная",
        "menu_profile": "Профиль",
        "menu_rename": "Переименовать...",
        "menu_clear": "Очистить",
        "menu_export": "Экспорт профиля...",
        "menu_import": "Импорт профиля...",
        "export_dialog_title": "Экспорт профиля",
        "import_dialog_title": "Импорт профиля",
        "file_filter_json": "Профиль макроса (*.json *.json.gz)",
        "confirm_import_title": "Подтверждение импорта",
        "confirm_import_msg": "Импорт перезапишет текущий профиль. Продолжить?",
        "import_bad_format": "Неверный формат файла профиля!",
        "import_error": "Не удалось импортировать профиль!",
        "export_error": "Не удалось экспортировать профиль!",
        "log_profile_exported": "Профиль {pid} экспортирован в '{path}'.",
        "log_profile_imported": "Профиль импортирован в слот {pid} из '{path}'.",
        "tt_start": "Старт",
        "tt_stop": "Стоп",
        "tt_pause_resume": "Пауза/Продолжить",
        "tt_save": "Сохранить",
        "tt_clear": "Очистить",
        "tt_rename": "Переименовать текущий профиль",
        "name_exists": "Такое имя уже существует!",
        "no_events": "Нет событий для воспроизведения!",
        "help_title": "Справка",
        "help_text": (
            "<h3>Macro Recorder Pro — Справка</h3>"
            "<p><b>Запись:</b><br>"
            "Нажмите <b>Запись</b> (F5), чтобы начать захват событий клавиатуры и мыши. "
            "Нажмите <b>Стоп</b> (F6) для завершения. Кнопка <b>Пауза зап.</b> (Alt+P) приостанавливает и продолжает запись.</p>"
            "<p><b>Воспроизведение:</b><br>"
            "Нажмите <b>Пуск</b> (F7), чтобы воспроизвести записанный макрос. "
            "Нажмите <b>Стоп</b> (F8) для прерывания. Кнопка <b>Пауза воспр.</b> (Alt+O) приостанавливает и продолжает воспроизведение. "
            "Раскладка клавиатуры синхронизируется автоматически с той, что была при записи.</p>"
            "<p><b>Профили:</b><br>"
            "Доступно 10 профилей. Выберите профиль из выпадающего списка. "
            "<b>Сохранить</b> (Alt+S) сохраняет макрос, <b>Очистить</b> (Alt+C) удаляет его и сбрасывает имя, "
            "<b>Переименовать</b> (Alt+R) меняет имя профиля.</p>"
            "<p><b>Импорт / Экспорт:</b><br>"
            "Профиль → Экспорт профиля... сохраняет текущий профиль в файл .json или .json.gz. "
            "Профиль → Импорт профиля... загружает файл профиля в текущий слот (с подтверждением).</p>"
            "<p><b>Горячие клавиши:</b><br>"
            "Настройки → Горячие клавиши... позволяет переназначить любую глобальную клавишу. "
            "Клавиши всегда отображаются в английской раскладке. "
            "Клавиши Space и Win в хоткеях запрещены.</p>"
            "<p><b>Язык и тема:</b><br>"
            "Настройки → Язык переключает интерфейс между английским и русским. "
            "Настройки → Тема переключает светлую и тёмную темы. "
            "Оба выбора сохраняются автоматически.</p>"
            "<p><b>Режим отладки:</b><br>"
            "Настройки → Панель администратора → Режим отладки включает подробное техническое логирование записываемых и воспроизводимых событий.</p>"
            "<hr>"
            "<p><b>Права администратора (UAC):</b><br>"
            "Приложение работает без прав администратора для большинства задач. Однако Windows "
            "изолирует привилегированные окна (User Interface Privilege Isolation — UIPI). Это означает:</p>"
            "<ul>"
            "<li><b>Без прав администратора:</b> глобальные горячие клавиши (F5/F7 и т.д.) и "
            "воспроизведение макросов работают в обычных пользовательских приложениях (браузер, "
            "Office, Блокнот, большинство игр), но <b>не будут работать</b> в окнах, запущенных "
            "от имени Администратора (Диспетчер задач, Командная строка с повышением прав, "
            "установщики, некоторые игры с античитом).</li>"
            "<li><b>С правами администратора:</b> горячие клавиши и синтетический ввод работают "
            "во <b>всех</b> окнах системы, включая привилегированные.</li>"
            "</ul>"
            "<p><b>Когда нужно повышение прав?</b></p>"
            "<ul>"
            "<li>Ваш макрос нацелен на окно, запущенное от имени Администратора.</li>"
            "<li>Глобальные горячие клавиши перестают реагировать в определённых приложениях.</li>"
            "<li>Вы автоматизируете системные инструменты (regedit, cmd с повышением, установщики).</li>"
            "</ul>"
            "<p><b>Как повысить права:</b> откройте <b>Настройки → Панель администратора</b> и "
            "нажмите <b>Перезапустить с правами администратора</b>. Windows покажет запрос UAC — "
            "нажмите «Да». Приложение перезапустится с полными привилегиями. Если вы отклоните "
            "запрос UAC, приложение продолжит работу от обычного пользователя.</p>"
            "<p><b>Примечание:</b> Некоторые игры с античитом уровня ядра (EasyAntiCheat, BattlEye, "
            "Vanguard) могут блокировать синтетический ввод даже от процесса с повышенными правами. "
            "В таких случаях воспроизведение макросов внутри игры может быть ограничено независимо "
            "от наличия прав администратора.</p>"
        ),
        "admin_title": "Панель администратора",
        "admin_status": "Статус:",
        "admin_is_admin": "Администратор",
        "admin_is_user": "Пользователь (без прав администратора)",
        "admin_restart": "Перезапустить с правами администратора",
        "admin_restart_hint": "Приложение закроется и запросит повышение прав (UAC).",
        "admin_hotkeys": "Зарегистрированные хоткеи:",
        "admin_layout": "Текущая раскладка:",
        "admin_uac_denied": "Повышение прав (UAC) отклонено или не удалось. Запуск от пользователя.",
        "admin_debug_mode": "Режим отладки",
        "admin_debug_hint": "Включает подробное техническое логирование записываемых и воспроизводимых событий.",
        "admin_logs_btn": "Логи",
        "admin_clear_logs_btn": "Очистить логи",
        "admin_logs_title": "Журналы приложения",
        "confirm_clear_logs_title": "Подтверждение очистки логов",
        "confirm_clear_logs_msg": "Удалить все файлы журналов? Это действие нельзя отменить.",
        "log_system_ready": "Система готова.",
        "log_cannot_record_playing": "Нельзя записывать во время воспроизведения.",
        "log_cannot_play_recording": "Нельзя воспроизводить во время записи.",
        "log_recording_started": "Запись начата...",
        "log_recording_paused": "Запись приостановлена.",
        "log_recording_resumed": "Запись продолжена.",
        "log_stopped_events": "Остановлено. Записано событий: {n}.",
        "log_playback_started": "Воспроизведение начато...",
        "log_playback_paused": "Воспроизведение приостановлено.",
        "log_playback_resumed": "Воспроизведение продолжено.",
        "log_playback_finished": "Воспроизведение завершено.",
        "log_profile_saved": "Профиль {pid} успешно сохранён.",
        "log_profile_cleared": "Профиль {pid} очищен.",
        "log_hotkeys_updated": "Конфигурация горячих клавиш обновлена.",
        "log_debug_enabled": "Режим отладки ВКЛЮЧЁН",
        "log_debug_disabled": "Режим отладки ВЫКЛЮЧЕН",
        "log_layout_mismatch": "ОБНАРУЖЕНО НЕСООТВЕТСТВИЕ РАСКЛАДКИ! Запись: {rec}, текущая: {cur}. Переключение...",
        "log_layout_synced": "Раскладка успешно синхронизирована.",
        "log_layout_failed": "ВНИМАНИЕ: Не удалось синхронизировать раскладку. Ввод текста может быть некорректным.",
        "log_lang_changed": "Язык изменён на русский.",
        "log_theme_changed": "Тема изменена на тёмную.",
        "log_cannot_change_profile": "Нельзя менять профиль во время записи или воспроизведения.",
        "layout_suffix": "раскладка",
    },
}


def tr(key, **kwargs):
    """Возвращает перевод строки для текущего языка."""
    text = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["en"]).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text