"""Главное окно приложения Macro Recorder Pro."""

import os
import json
import time
import math
import threading

from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QPoint, QAbstractNativeEventFilter
from PyQt6.QtGui import QIcon, QKeySequence, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QTextEdit, QMenu, QFileDialog, QDialog,
)

import ctypes
from ctypes import wintypes
import win32gui
import win32con
import mouse
import keyboard

from . import theme as theme_mod
from .theme import THEMES, STYLES, build_styles
from . import i18n as i18n_mod
from .i18n import tr
from .bridge import Bridge, safe_invoke
from .paths import get_base_dir, setup_logging
from .widgets import LightToolTip
from .dialogs import (
    WarningDialog, ErrorDialog, ConfirmClearDialog, ConfirmImportDialog,
    HelpDialog, RenameDialog, HotkeySettingsDialog, AdminPanelDialog,
)
from . import layout_utils
from . import profiles as profiles_io


# ==================== NATIVE EVENT FILTER ДЛЯ WM_HOTKEY ====================
class HotkeyEventFilter(QAbstractNativeEventFilter):
    WM_HOTKEY = 0x0312
    
    VK_MAP = {
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
        'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
        'ctrl': win32con.VK_CONTROL, 'control': win32con.VK_CONTROL,
        'alt': win32con.VK_MENU, 'shift': win32con.VK_SHIFT,
        'win': win32con.VK_LWIN, 'windows': win32con.VK_LWIN,
        'space': win32con.VK_SPACE, 'enter': win32con.VK_RETURN,
        'return': win32con.VK_RETURN, 'tab': win32con.VK_TAB,
        'esc': win32con.VK_ESCAPE, 'escape': win32con.VK_ESCAPE,
        'backspace': win32con.VK_BACK, 'delete': win32con.VK_DELETE,
        'insert': win32con.VK_INSERT, 'home': win32con.VK_HOME,
        'end': win32con.VK_END, 'pageup': win32con.VK_PRIOR,
        'pagedown': win32con.VK_NEXT, 'up': win32con.VK_UP,
        'down': win32con.VK_DOWN, 'left': win32con.VK_LEFT,
        'right': win32con.VK_RIGHT,
    }
    
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000
    
    def __init__(self):
        super().__init__()
        self._hotkey_map = {}
        self._next_id = 1
        self._registered_ids = []
    
    def register(self, hotkey_str, callback):
        modifiers, vk = self._parse_hotkey(hotkey_str)
        if vk is None:
            return None
        
        hid = self._next_id
        self._next_id += 1
        
        ret = ctypes.windll.user32.RegisterHotKey(None, hid, modifiers | self.MOD_NOREPEAT, vk)
        if ret == 0:
            err = ctypes.get_last_error()
            print(f"[HotkeyEventFilter] RegisterHotKey failed for '{hotkey_str}', error={err}")
            return None
        
        self._hotkey_map[hid] = callback
        self._registered_ids.append(hid)
        return hid
    
    def unregister_all(self):
        for hid in self._registered_ids:
            ctypes.windll.user32.UnregisterHotKey(None, hid)
        self._registered_ids.clear()
        self._hotkey_map.clear()
    
    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == self.WM_HOTKEY:
                hid = msg.wParam
                callback = self._hotkey_map.get(hid)
                if callback:
                    QTimer.singleShot(0, callback)
                    return True, 0
        return False, 0
    
    def _parse_hotkey(self, hotkey_str):
        parts = [p.strip().lower() for p in hotkey_str.split('+')]
        modifiers = 0
        vk = None
        
        for part in parts:
            if part in ('ctrl', 'control'):
                modifiers |= self.MOD_CONTROL
            elif part == 'alt':
                modifiers |= self.MOD_ALT
            elif part == 'shift':
                modifiers |= self.MOD_SHIFT
            elif part in ('win', 'windows'):
                modifiers |= self.MOD_WIN
            else:
                if part in self.VK_MAP:
                    vk = self.VK_MAP[part]
                elif len(part) == 1 and part.isalnum():
                    vk = ord(part.upper())
                elif part.startswith('f') and part[1:].isdigit():
                    fnum = int(part[1:])
                    if 1 <= fnum <= 24:
                        vk = 0x70 + fnum - 1
        return modifiers, vk


class MacroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger.debug("[INIT] MacroApp constructor started.")

        self.BASE_DIR = get_base_dir()
        self.LOG_DIR = os.path.join(self.BASE_DIR, "logs")
        self.PROFILE_DIR = os.path.join(self.BASE_DIR, "profiles")
        self.CONFIG_PATH = os.path.join(self.BASE_DIR, "hotkeys_config.json")
        self.LANG_CONFIG_PATH = os.path.join(self.BASE_DIR, "language_config.json")
        self.THEME_CONFIG_PATH = os.path.join(self.BASE_DIR, "theme_config.json")

        os.makedirs(self.BASE_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)
        os.makedirs(self.PROFILE_DIR, exist_ok=True)

        self.load_language_config()
        self.load_theme_config()

        self.logger, self.log_file_path = setup_logging(self.LOG_DIR)
        self.logger.info("=" * 50)
        self.logger.info("MACRO RECORDER STARTED")
        self.logger.info(f"Data directory: {self.BASE_DIR}")

        self.bridge = Bridge()
        self.bridge.update_status_signal.connect(self.set_status_texts)
        self.bridge.log_signal.connect(self.add_log)
        self.bridge.playback_started_signal.connect(self._on_playback_started_ui)
        self.bridge.playback_finished_signal.connect(self._on_playback_finished_ui)

        self.setWindowTitle(tr("app_title"))
        self.resize(750, 580)
        self.setMinimumSize(650, 480)

        self.setup_window_icon()

        self.profiles = {i: {"name": tr("profile_default_name", n=i), "events": []} for i in range(1, 11)}
        self.current_profile_id = 1
        self.is_recording = False
        self.is_paused_recording = False
        self.is_playing = False
        self.is_paused_playing = False
        self.debug_mode = False
        self.events = []
        self.start_time = 0
        self.pause_start_time = 0
        self.total_paused_duration = 0

        self.playback_start_time = time.time()
        self.playback_paused_duration = 0
        self.playback_total_duration = 0

        self._playback_launching = False
        self._playback_stop_requested = False

        self.active_modifiers = []
        self.last_modifier_down_time = 0
        self.recording_layout_hkl = None

        self.system_lang_switch_combo = layout_utils.detect_system_language_hotkey(self.logger)
        self.logger.info(f"Detected system language switch combo: {self.system_lang_switch_combo}")

        self.default_hotkeys = {
            "record_start": "f5",
            "record_stop": "f6",
            "record_pause": "alt+p",
            "play_start": "f7",
            "play_stop": "f8",
            "play_pause": "alt+o",
            "save_profile": "alt+s",
            "clear_profile": "alt+c",
            "rename_profile": "alt+r",
            "quit_app": "alt+q",
        }
        self.hotkeys = self.load_hotkeys_config()
        self.saved_window_states = []

        self.tooltips = {}

        self._hotkey_filter = HotkeyEventFilter()
        QApplication.instance().installNativeEventFilter(self._hotkey_filter)

        self.load_all_profiles()
        self.update_current_context()

        self.init_ui()

        self.update_status()

        self.register_hotkeys()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_tick)
        self.timer.start(1000)

        self.logger.info("UI Initialized.")
        self.add_log(tr("log_system_ready"))

    def closeEvent(self, event):
        self.logger.debug("[APP] Close event triggered.")
        self._hotkey_filter.unregister_all()
        super().closeEvent(event)

    # ==================== ЯЗЫК / ТЕМА / КОНФИГ ====================
    def load_language_config(self):
        try:
            if os.path.exists(self.LANG_CONFIG_PATH):
                with open(self.LANG_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    lang = data.get("language", "en")
                    if lang in i18n_mod.TRANSLATIONS:
                        i18n_mod.CURRENT_LANG = lang
                        self.logger.debug(f"[CONFIG] Language loaded: {lang}")
        except Exception:
            pass

    def save_language_config(self):
        try:
            with open(self.LANG_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump({"language": i18n_mod.CURRENT_LANG}, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"[CONFIG] Language config saved: {i18n_mod.CURRENT_LANG}")
        except Exception as e:
            self.logger.error(f"Error saving language config: {e}")

    def change_language(self, lang):
        if lang == i18n_mod.CURRENT_LANG:
            return
        self.logger.info(f"[APP] Changing language to: {lang}")
        i18n_mod.CURRENT_LANG = lang
        self.save_language_config()
        self.retranslate_ui()
        self.bridge.log_signal.emit(tr("log_lang_changed"))

    def load_theme_config(self):
        try:
            if os.path.exists(self.THEME_CONFIG_PATH):
                with open(self.THEME_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    theme = data.get("theme", "light")
                    if theme in THEMES:
                        theme_mod.CURRENT_THEME = theme
                        self.logger.debug(f"[CONFIG] Theme loaded: {theme}")
        except Exception:
            pass
        theme_mod.STYLES = build_styles()

    def save_theme_config(self):
        try:
            with open(self.THEME_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump({"theme": theme_mod.CURRENT_THEME}, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"[CONFIG] Theme config saved: {theme_mod.CURRENT_THEME}")
        except Exception as e:
            self.logger.error(f"Error saving theme config: {e}")

    def change_theme(self, theme):
        if theme == theme_mod.CURRENT_THEME:
            return
        self.logger.info(f"[APP] Changing theme to: {theme}")
        theme_mod.CURRENT_THEME = theme
        theme_mod.STYLES = build_styles()
        self.save_theme_config()
        self.apply_theme()
        self.bridge.log_signal.emit(tr("log_theme_changed"))

    def apply_theme(self):
        self.logger.debug("[UI] Applying theme styles...")
        t = THEMES[theme_mod.CURRENT_THEME]
        self.centralWidget().setStyleSheet(STYLES["MAIN_BG"])
        self.top_frame.setStyleSheet(STYLES["WHITE_PANEL"])
        self.status_frame.setStyleSheet(STYLES["WHITE_PANEL"])
        self.log_frame.setStyleSheet(STYLES["WHITE_PANEL"])
        self.lbl_select_profile.setStyleSheet(STYLES["FONT_BOLD"] + STYLES["TEXT_DARK"] + "background: transparent;")
        self.profile_widget.setStyleSheet(f"background-color: {t['PROFILE_BG']}; border-radius: 10px;")
        self.lbl_current_profile.setStyleSheet(f"padding-left: 12px; font-size: 12px; color: {t['TEXT_DARK']}; border: none; background: transparent;")
        self.btn_dropdown.setStyleSheet(f"QPushButton {{ background-color: {t['GREEN']}; color: white; border-top-right-radius: 10px; border-bottom-right-radius: 10px; border-top-left-radius: 0px; border-bottom-left-radius: 0px; font-size: 10px; border: none; }} QPushButton:hover {{ background-color: {t['GREEN_HOVER']}; }}")
        self.menu_profiles.setStyleSheet(STYLES["MENU"])
        self.btn_rename.setStyleSheet(STYLES["BTN_DARK"] + "QPushButton { padding-left: 12px; padding-right: 12px; }")
        self.btn_record.setStyleSheet(STYLES["BTN_RED"] if self.is_recording else STYLES["BTN_GREEN"])
        self.btn_pause_rec.setStyleSheet(STYLES["BTN_GREEN"] if self.is_paused_recording else STYLES["BTN_GRAY"])
        self.btn_play.setStyleSheet(STYLES["BTN_RED"] if self.is_playing else STYLES["BTN_GREEN"])
        self.btn_pause_play.setStyleSheet(STYLES["BTN_GREEN"] if self.is_paused_playing else STYLES["BTN_GRAY"])
        self.btn_save.setStyleSheet(STYLES["BTN_DARK"])
        self.btn_clear.setStyleSheet(STYLES["BTN_GRAY"])
        self.lbl_profile_title.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_profile_val.setStyleSheet(f"font-weight: normal; {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_sep1.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_state_title.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_state_val.setStyleSheet(f"font-weight: normal; {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_log.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.log_text.setStyleSheet(STYLES["LOG_AREA"] + STYLES["SCROLL_BAR"])
        self.menuBar().setStyleSheet(STYLES["MENU"].replace("QMenu", "QMenuBar").replace("border-radius: 10px;", ""))
        self.menu_language.setStyleSheet(STYLES["MENU"])
        self.menu_theme.setStyleSheet(STYLES["MENU"])
        self.act_theme_light.setChecked(theme_mod.CURRENT_THEME == "light")
        self.act_theme_dark.setChecked(theme_mod.CURRENT_THEME == "dark")

    def retranslate_ui(self):
        self.logger.debug("[UI] Retranslating interface...")
        self.setWindowTitle(tr("app_title"))
        self.lbl_select_profile.setText(tr("select_profile"))
        self.btn_rename.setText(tr("btn_rename"))
        self.btn_rename.adjustSize()
        self.btn_record.setText(tr("btn_stop") if self.is_recording else tr("btn_record"))
        self.btn_pause_rec.setText(tr("btn_resume") if self.is_paused_recording else tr("btn_pause_rec"))
        self.btn_play.setText(tr("btn_stop") if self.is_playing else tr("btn_play"))
        self.btn_pause_play.setText(tr("btn_resume") if self.is_paused_playing else tr("btn_pause_play"))
        self.btn_save.setText(tr("btn_save"))
        self.btn_clear.setText(tr("btn_clear"))
        self.lbl_profile_title.setText(tr("lbl_profile"))
        self.lbl_state_title.setText(tr("lbl_state"))
        self.lbl_log.setText(tr("event_log"))
        self.menu_file.setTitle(tr("menu_file"))
        self.act_save.setText(tr("menu_save"))
        self.act_help.setText(tr("menu_help"))
        self.act_exit.setText(tr("menu_exit"))
        self.menu_settings.setTitle(tr("menu_settings"))
        self.act_hotkeys.setText(tr("menu_hotkeys"))
        self.act_admin.setText(tr("menu_admin"))
        self.menu_language.setTitle(tr("menu_language"))
        self.menu_theme.setTitle(tr("menu_theme"))
        self.act_theme_light.setText(tr("theme_light"))
        self.act_theme_dark.setText(tr("theme_dark"))
        self.menu_profile.setTitle(tr("menu_profile"))
        self.act_rename.setText(tr("menu_rename"))
        self.act_clear.setText(tr("menu_clear"))
        self.act_export.setText(tr("menu_export"))
        self.act_import.setText(tr("menu_import"))
        self.act_lang_en.setChecked(i18n_mod.CURRENT_LANG == "en")
        self.act_lang_ru.setChecked(i18n_mod.CURRENT_LANG == "ru")
        for pid, data in self.profiles.items():
            for lng in ("en", "ru"):
                if data["name"] == i18n_mod.TRANSLATIONS[lng]["profile_default_name"].format(n=pid):
                    data["name"] = tr("profile_default_name", n=pid)
                    break
        self.refresh_profile_menu_labels()
        self.update_tooltip_texts()
        self.update_status()

    def update_tooltip_texts(self):
        if 'rec' in self.tooltips:
            self.tooltips['rec'].update_text(f"{self.hotkeys['record_start'].upper()} - {tr('tt_start')}\n{self.hotkeys['record_stop'].upper()} - {tr('tt_stop')}")
        if 'pause_rec' in self.tooltips:
            self.tooltips['pause_rec'].update_text(f"{self.hotkeys['record_pause'].upper()} - {tr('tt_pause_resume')}")
        if 'play' in self.tooltips:
            self.tooltips['play'].update_text(f"{self.hotkeys['play_start'].upper()} - {tr('tt_start')}\n{self.hotkeys['play_stop'].upper()} - {tr('tt_stop')}")
        if 'pause_play' in self.tooltips:
            self.tooltips['pause_play'].update_text(f"{self.hotkeys['play_pause'].upper()} - {tr('tt_pause_resume')}")
        if 'save' in self.tooltips:
            self.tooltips['save'].update_text(f"{self.hotkeys['save_profile'].upper()} - {tr('tt_save')}")
        if 'clear' in self.tooltips:
            self.tooltips['clear'].update_text(f"{self.hotkeys['clear_profile'].upper()} - {tr('tt_clear')}")
        if 'rename' in self.tooltips:
            self.tooltips['rename'].update_text(f"{self.hotkeys['rename_profile'].upper()} - {tr('tt_rename')}")

    def load_hotkeys_config(self):
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cfg = self.default_hotkeys.copy()
                    cfg.update(data)
                    self.logger.debug(f"[CONFIG] Hotkeys loaded from file.")
                    return cfg
            except Exception as e:
                self.logger.error(f"Error loading hotkeys config: {e}")
        return self.default_hotkeys.copy()

    def save_hotkeys_config(self):
        try:
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.hotkeys, f, indent=2, ensure_ascii=False)
            self.logger.debug("[CONFIG] Hotkeys config saved.")
        except Exception as e:
            self.logger.error(f"Error saving hotkeys config: {e}")

    def load_all_profiles(self):
        self.logger.debug("[PROFILES] Loading all profiles...")
        loaded = profiles_io.load_all_profiles(self.PROFILE_DIR, lambda n: tr("profile_default_name", n=n), self.logger)
        self.profiles.update(loaded)

    def save_current_profile(self):
        pid = self.current_profile_id
        self.profiles[pid]["events"] = list(self.events)
        self.logger.debug(f"[PROFILES] Saving profile {pid} in background thread.")
        threading.Thread(target=profiles_io.save_profile, args=(self.PROFILE_DIR, pid, self.profiles[pid], self.logger), daemon=True).start()

    # ==================== UI ====================
    def set_status_texts(self, profile_name, state_text):
        self.lbl_profile_val.setText(profile_name)
        self.lbl_state_val.setText(state_text)

    def setup_window_icon(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            icon_path = os.path.join(parent_dir, "macro_icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(parent_dir, "macro_icon.png")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(script_dir, "macro_icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(script_dir, "macro_icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                try:
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MacroRecorderPro.App.1.0')
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning(f"Icon load error: {e}")

    def init_ui(self):
        self.logger.debug("[UI] Initializing UI components...")
        t = THEMES[theme_mod.CURRENT_THEME]
        central_widget = QWidget()
        central_widget.setStyleSheet(STYLES["MAIN_BG"])
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.top_frame = QWidget()
        self.top_frame.setStyleSheet(STYLES["WHITE_PANEL"])
        top_layout = QHBoxLayout(self.top_frame)
        top_layout.setContentsMargins(15, 12, 15, 12)
        self.lbl_select_profile = QLabel(tr("select_profile"))
        self.lbl_select_profile.setStyleSheet(STYLES["FONT_BOLD"] + STYLES["TEXT_DARK"] + "background: transparent;")
        top_layout.addWidget(self.lbl_select_profile)
        self.profile_widget = QWidget()
        self.profile_widget.setFixedSize(200, 32)
        self.profile_widget.setStyleSheet(f"background-color: {t['PROFILE_BG']}; border-radius: 10px;")
        profile_layout = QHBoxLayout(self.profile_widget)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(0)
        self.lbl_current_profile = QLabel(self.profiles[self.current_profile_id]["name"])
        self.lbl_current_profile.setStyleSheet(f"padding-left: 12px; font-size: 12px; color: {t['TEXT_DARK']}; border: none; background: transparent;")
        profile_layout.addWidget(self.lbl_current_profile, stretch=1)
        self.btn_dropdown = QPushButton("▼")
        self.btn_dropdown.setFixedSize(40, 32)
        self.btn_dropdown.setStyleSheet(f"QPushButton {{ background-color: {t['GREEN']}; color: white; border-top-right-radius: 10px; border-bottom-right-radius: 10px; border-top-left-radius: 0px; border-bottom-left-radius: 0px; font-size: 10px; border: none; }} QPushButton:hover {{ background-color: {t['GREEN_HOVER']}; }}")
        self.menu_profiles = QMenu(self)
        self.menu_profiles.setStyleSheet(STYLES["MENU"])
        for i in range(1, 11):
            action = QAction(self.profiles[i]["name"], self)
            action.triggered.connect(lambda checked, idx=i: self.select_profile_by_id(idx))
            self.menu_profiles.addAction(action)
        self.btn_dropdown.clicked.connect(self.show_profile_menu)
        profile_layout.addWidget(self.btn_dropdown)
        top_layout.addWidget(self.profile_widget)
        self.btn_rename = QPushButton(tr("btn_rename"))
        self.btn_rename.setFixedHeight(32)
        self.btn_rename.setMinimumWidth(80)
        self.btn_rename.setStyleSheet(STYLES["BTN_DARK"] + "QPushButton { padding-left: 12px; padding-right: 12px; }")
        tt_rename = LightToolTip(self.btn_rename, f"{self.hotkeys['rename_profile'].upper()} - {tr('tt_rename')}")
        self.tooltips['rename'] = tt_rename
        self.btn_rename.clicked.connect(self.rename_current_profile)
        top_layout.addWidget(self.btn_rename)
        top_layout.addStretch()
        main_layout.addWidget(self.top_frame)

        control_frame = QWidget()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)
        rec_col = QWidget()
        rec_col_layout = QVBoxLayout(rec_col)
        rec_col_layout.setContentsMargins(0, 0, 0, 0)
        rec_col_layout.setSpacing(6)
        self.btn_record = QPushButton(tr("btn_record"))
        self.btn_record.setFixedSize(115, 38)
        self.btn_record.setStyleSheet(STYLES["BTN_GREEN"])
        tt_rec = LightToolTip(self.btn_record, f"{self.hotkeys['record_start'].upper()} - {tr('tt_start')}\n{self.hotkeys['record_stop'].upper()} - {tr('tt_stop')}")
        self.tooltips['rec'] = tt_rec
        self.btn_record.clicked.connect(self.toggle_recording)
        rec_col_layout.addWidget(self.btn_record)
        self.btn_pause_rec = QPushButton(tr("btn_pause_rec"))
        self.btn_pause_rec.setFixedSize(115, 30)
        self.btn_pause_rec.setStyleSheet(STYLES["BTN_GRAY"])
        tt_pause_rec = LightToolTip(self.btn_pause_rec, f"{self.hotkeys['record_pause'].upper()} - {tr('tt_pause_resume')}")
        self.tooltips['pause_rec'] = tt_pause_rec
        self.btn_pause_rec.clicked.connect(self.toggle_pause_recording)
        rec_col_layout.addWidget(self.btn_pause_rec)
        control_layout.addWidget(rec_col)
        play_col = QWidget()
        play_col_layout = QVBoxLayout(play_col)
        play_col_layout.setContentsMargins(0, 0, 0, 0)
        play_col_layout.setSpacing(6)
        self.btn_play = QPushButton(tr("btn_play"))
        self.btn_play.setFixedSize(115, 38)
        self.btn_play.setStyleSheet(STYLES["BTN_GREEN"])
        tt_play = LightToolTip(self.btn_play, f"{self.hotkeys['play_start'].upper()} - {tr('tt_start')}\n{self.hotkeys['play_stop'].upper()} - {tr('tt_stop')}")
        self.tooltips['play'] = tt_play
        self.btn_play.clicked.connect(self.toggle_playback)
        play_col_layout.addWidget(self.btn_play)
        self.btn_pause_play = QPushButton(tr("btn_pause_play"))
        self.btn_pause_play.setFixedSize(115, 30)
        self.btn_pause_play.setStyleSheet(STYLES["BTN_GRAY"])
        tt_pause_play = LightToolTip(self.btn_pause_play, f"{self.hotkeys['play_pause'].upper()} - {tr('tt_pause_resume')}")
        self.tooltips['pause_play'] = tt_pause_play
        self.btn_pause_play.clicked.connect(self.toggle_pause_playback)
        play_col_layout.addWidget(self.btn_pause_play)
        control_layout.addWidget(play_col)
        action_col = QWidget()
        action_col_layout = QHBoxLayout(action_col)
        action_col_layout.setContentsMargins(0, 0, 0, 0)
        action_col_layout.setSpacing(10)
        self.btn_save = QPushButton(tr("btn_save"))
        self.btn_save.setFixedSize(90, 38)
        self.btn_save.setStyleSheet(STYLES["BTN_DARK"])
        tt_save = LightToolTip(self.btn_save, f"{self.hotkeys['save_profile'].upper()} - {tr('tt_save')}")
        self.tooltips['save'] = tt_save
        self.btn_save.clicked.connect(self.save_current_profile)
        action_col_layout.addWidget(self.btn_save)
        self.btn_clear = QPushButton(tr("btn_clear"))
        self.btn_clear.setFixedSize(90, 38)
        self.btn_clear.setStyleSheet(STYLES["BTN_GRAY"])
        tt_clear = LightToolTip(self.btn_clear, f"{self.hotkeys['clear_profile'].upper()} - {tr('tt_clear')}")
        self.tooltips['clear'] = tt_clear
        self.btn_clear.clicked.connect(self.clear_current_profile)
        action_col_layout.addWidget(self.btn_clear)
        control_layout.addWidget(action_col)
        control_layout.addStretch()
        main_layout.addWidget(control_frame)

        self.status_frame = QWidget()
        self.status_frame.setStyleSheet(STYLES["WHITE_PANEL"])
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(20, 12, 20, 12)
        status_layout.setSpacing(6)
        self.lbl_profile_title = QLabel(tr("lbl_profile"))
        self.lbl_profile_title.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_profile_val = QLabel(self.profiles[self.current_profile_id]["name"])
        self.lbl_profile_val.setStyleSheet(f"font-weight: normal; {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_sep1 = QLabel("|")
        self.lbl_sep1.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_state_title = QLabel(tr("lbl_state"))
        self.lbl_state_title.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        self.lbl_state_val = QLabel("—")
        self.lbl_state_val.setStyleSheet(f"font-weight: normal; {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        status_layout.addWidget(self.lbl_profile_title)
        status_layout.addWidget(self.lbl_profile_val)
        status_layout.addWidget(self.lbl_sep1)
        status_layout.addWidget(self.lbl_state_title)
        status_layout.addWidget(self.lbl_state_val)
        status_layout.addStretch()
        main_layout.addWidget(self.status_frame)

        self.log_frame = QWidget()
        self.log_frame.setStyleSheet(STYLES["WHITE_PANEL"])
        log_layout = QVBoxLayout(self.log_frame)
        log_layout.setContentsMargins(15, 10, 15, 15)
        log_header = QWidget()
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_log = QLabel(tr("event_log"))
        self.lbl_log.setStyleSheet(f"{STYLES['FONT_BOLD']} {STYLES['TEXT_DARK']} font-size: 12px; background: transparent;")
        log_header_layout.addWidget(self.lbl_log)
        log_header_layout.addStretch()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(STYLES["LOG_AREA"] + STYLES["SCROLL_BAR"])
        log_layout.addWidget(log_header)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(self.log_frame)

        menubar = self.menuBar()
        menubar.setStyleSheet(STYLES["MENU"].replace("QMenu", "QMenuBar").replace("border-radius: 10px;", ""))
        self.menu_file = menubar.addMenu(tr("menu_file"))
        self.act_save = QAction(tr("menu_save"), self)
        self.act_save.setShortcut(QKeySequence(self.hotkeys["save_profile"]))
        self.act_save.triggered.connect(self.save_current_profile)
        self.menu_file.addAction(self.act_save)
        self.menu_file.addSeparator()
        self.act_help = QAction(tr("menu_help"), self)
        self.act_help.triggered.connect(self.open_help)
        self.menu_file.addAction(self.act_help)
        self.menu_file.addSeparator()
        self.act_exit = QAction(tr("menu_exit"), self)
        self.act_exit.setShortcut(QKeySequence(self.hotkeys["quit_app"]))
        self.act_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.act_exit)
        self.menu_settings = menubar.addMenu(tr("menu_settings"))
        self.act_hotkeys = QAction(tr("menu_hotkeys"), self)
        self.act_hotkeys.triggered.connect(self.open_hotkeys_settings)
        self.menu_settings.addAction(self.act_hotkeys)
        self.menu_settings.addSeparator()
        self.act_admin = QAction(tr("menu_admin"), self)
        self.act_admin.triggered.connect(self.open_admin_panel)
        self.menu_settings.addAction(self.act_admin)
        self.menu_settings.addSeparator()
        self.menu_language = self.menu_settings.addMenu(tr("menu_language"))
        self.menu_language.setStyleSheet(STYLES["MENU"])
        self.act_lang_en = QAction("English", self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.setChecked(i18n_mod.CURRENT_LANG == "en")
        self.act_lang_en.triggered.connect(lambda: self.change_language("en"))
        self.menu_language.addAction(self.act_lang_en)
        self.act_lang_ru = QAction("Русский", self)
        self.act_lang_ru.setCheckable(True)
        self.act_lang_ru.setChecked(i18n_mod.CURRENT_LANG == "ru")
        self.act_lang_ru.triggered.connect(lambda: self.change_language("ru"))
        self.menu_language.addAction(self.act_lang_ru)
        self.menu_theme = self.menu_settings.addMenu(tr("menu_theme"))
        self.menu_theme.setStyleSheet(STYLES["MENU"])
        self.act_theme_light = QAction(tr("theme_light"), self)
        self.act_theme_light.setCheckable(True)
        self.act_theme_light.setChecked(theme_mod.CURRENT_THEME == "light")
        self.act_theme_light.triggered.connect(lambda: self.change_theme("light"))
        self.menu_theme.addAction(self.act_theme_light)
        self.act_theme_dark = QAction(tr("theme_dark"), self)
        self.act_theme_dark.setCheckable(True)
        self.act_theme_dark.setChecked(theme_mod.CURRENT_THEME == "dark")
        self.act_theme_dark.triggered.connect(lambda: self.change_theme("dark"))
        self.menu_theme.addAction(self.act_theme_dark)
        self.menu_profile = menubar.addMenu(tr("menu_profile"))
        self.act_rename = QAction(tr("menu_rename"), self)
        self.act_rename.setShortcut(QKeySequence(self.hotkeys["rename_profile"]))
        self.act_rename.triggered.connect(self.rename_current_profile)
        self.menu_profile.addAction(self.act_rename)
        self.act_clear = QAction(tr("menu_clear"), self)
        self.act_clear.setShortcut(QKeySequence(self.hotkeys["clear_profile"]))
        self.act_clear.triggered.connect(self.clear_current_profile)
        self.menu_profile.addAction(self.act_clear)
        self.menu_profile.addSeparator()
        self.act_export = QAction(tr("menu_export"), self)
        self.act_export.triggered.connect(self.export_current_profile)
        self.menu_profile.addAction(self.act_export)
        self.act_import = QAction(tr("menu_import"), self)
        self.act_import.triggered.connect(self.import_profile)
        self.menu_profile.addAction(self.act_import)

    # ==================== ДЕЙСТВИЯ ====================
    def open_help(self):
        self.logger.debug("[ACTION] Opening Help dialog.")
        HelpDialog(self).exec()

    def open_admin_panel(self):
        self.logger.debug("[ACTION] Opening Admin Panel.")
        dlg = AdminPanelDialog(self, data_dir=self.BASE_DIR, hotkeys=self.hotkeys, debug_mode=self.debug_mode, on_debug_changed=self.set_debug_mode)
        dlg.exec()
        if dlg.restart_requested():
            self.logger.info("[ACTION] Restart requested by Admin Panel.")
            self.close()

    def _styled_file_dialog(self, title, accept_mode, file_mode):
        t = THEMES[theme_mod.CURRENT_THEME]
        dlg = QFileDialog(self, title)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dlg.setAcceptMode(accept_mode)
        dlg.setFileMode(file_mode)
        dlg.setNameFilter(tr("file_filter_json"))
        dlg.setStyleSheet(f"QDialog {{ background-color: {t['PANEL_BG']}; }} QLabel {{ color: {t['TEXT_DARK']}; background: transparent; }} QListView, QTreeView {{ background-color: {t['LOG_BG']}; color: {t['TEXT_DARK']}; border: 1px solid {t['INPUT_BORDER']}; border-radius: 6px; }} QLineEdit {{ background-color: {t['INPUT_BG']}; color: {t['TEXT_DARK']}; border: 1px solid {t['INPUT_BORDER']}; border-radius: 4px; padding: 3px; }} QComboBox {{ background-color: {t['INPUT_BG']}; color: {t['TEXT_DARK']}; border: 1px solid {t['INPUT_BORDER']}; border-radius: 4px; padding: 3px; }} QComboBox QAbstractItemView {{ background-color: {t['PANEL_BG']}; color: {t['TEXT_DARK']}; selection-background-color: {t['GREEN']}; selection-color: white; }} QPushButton {{ background-color: {t['BTN_GRAY_BG']}; color: {t['BTN_GRAY_TEXT']}; border-radius: 6px; padding: 5px 14px; font-weight: bold; border: none; }} QPushButton:hover {{ background-color: {t['GREEN']}; color: white; }} QToolButton {{ background-color: {t['BTN_GRAY_BG']}; color: {t['BTN_GRAY_TEXT']}; border-radius: 4px; border: none; }} QToolButton:hover {{ background-color: {t['GREEN']}; color: white; }} QHeaderView::section {{ background-color: {t['ROW_BG']}; color: {t['ROW_TEXT']}; border: none; padding: 4px; }}" + STYLES["SCROLL_BAR"])
        return dlg

    def export_current_profile(self):
        self.logger.debug(f"[ACTION] Exporting profile {self.current_profile_id}.")
        if self.is_recording or self.is_playing:
            self.bridge.log_signal.emit(tr("log_cannot_record_playing") if self.is_recording else tr("log_cannot_play_recording"))
            return
        pid = self.current_profile_id
        self.profiles[pid]["events"] = list(self.events)
        safe_name = "".join(c for c in self.profiles[pid]["name"] if c.isalnum() or c in (" ", "_", "-")).strip() or f"profile_{pid}"
        default_path = os.path.join(self.PROFILE_DIR, f"{safe_name}.json")
        dlg = self._styled_file_dialog(tr("export_dialog_title"), QFileDialog.AcceptMode.AcceptSave, QFileDialog.FileMode.AnyFile)
        dlg.selectFile(default_path)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        selected = dlg.selectedFiles()
        if not selected:
            return
        path = selected[0]
        if not path.lower().endswith((".json", ".gz")):
            path += ".json"
        if profiles_io.export_profile(path, self.profiles[pid], self.logger):
            self.logger.info(f"Profile {pid} exported to '{path}'")
            self.bridge.log_signal.emit(tr("log_profile_exported", pid=pid, path=path))
        else:
            ErrorDialog(tr("export_error"), self).exec()

    def import_profile(self):
        self.logger.debug(f"[ACTION] Importing profile into slot {self.current_profile_id}.")
        if self.is_recording or self.is_playing:
            self.bridge.log_signal.emit(tr("log_cannot_record_playing") if self.is_recording else tr("log_cannot_play_recording"))
            return
        dlg = self._styled_file_dialog(tr("import_dialog_title"), QFileDialog.AcceptMode.AcceptOpen, QFileDialog.FileMode.ExistingFile)
        dlg.setDirectory(self.PROFILE_DIR)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        selected = dlg.selectedFiles()
        if not selected:
            return
        path = selected[0]
        try:
            new_name, new_events = profiles_io.read_imported_profile(path, self.logger)
        except ValueError:
            ErrorDialog(tr("import_bad_format"), self).exec()
            return
        except Exception:
            ErrorDialog(tr("import_error"), self).exec()
            return
        if ConfirmImportDialog(self).exec() != QDialog.DialogCode.Accepted:
            return
        pid = self.current_profile_id
        new_name = profiles_io.resolve_import_name(new_name, path, pid, self.profiles, lambda n: tr("profile_default_name", n=n))
        self.profiles[pid]["name"] = new_name
        self.profiles[pid]["events"] = new_events
        self.update_current_context()
        self.refresh_profile_menu_labels()
        self.save_current_profile()
        self.update_status()
        self.logger.info(f"Profile imported into slot {pid} from '{path}'")
        self.bridge.log_signal.emit(tr("log_profile_imported", pid=pid, path=path))

    def set_debug_mode(self, enabled):
        self.debug_mode = bool(enabled)
        self.logger.info(f"[CONFIG] Debug mode set to: {self.debug_mode}")
        self.bridge.log_signal.emit(tr("log_debug_enabled") if self.debug_mode else tr("log_debug_disabled"))

    def show_profile_menu(self):
        pos = self.profile_widget.mapToGlobal(QPoint(0, self.profile_widget.height()))
        self.menu_profiles.setMinimumWidth(self.profile_widget.width())
        self.menu_profiles.exec(pos)

    def add_log(self, message):
        self.logger.info(message)
        if not message.startswith("DEBUG"):
            self.log_text.append(f"> {message}")
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def open_hotkeys_settings(self):
        self.logger.debug("[ACTION] Opening Hotkey Settings.")
        HotkeySettingsDialog(self, self.hotkeys, self.on_hotkeys_updated).exec()

    def on_hotkeys_updated(self, new_hotkeys):
        self.hotkeys = self.default_hotkeys.copy() if new_hotkeys is None else new_hotkeys
        self.save_hotkeys_config()
        self.register_hotkeys()
        self.update_tooltip_texts()
        self.bridge.log_signal.emit(tr("log_hotkeys_updated"))

    def select_profile_by_id(self, idx):
        self.logger.debug(f"[ACTION] Profile selected: {idx}")
        self.current_profile_id = idx
        self.update_current_context()
        self.lbl_current_profile.setText(self.profiles[self.current_profile_id]["name"])
        self.update_status()

    def update_current_context(self):
        self.events = self.profiles[self.current_profile_id]["events"]

    def refresh_profile_menu_labels(self):
        self.lbl_current_profile.setText(self.profiles[self.current_profile_id]["name"])
        for idx, act in enumerate(self.menu_profiles.actions(), start=1):
            if idx in self.profiles:
                act.setText(self.profiles[idx]["name"])

    def rename_current_profile(self):
        self.logger.debug(f"[ACTION] Renaming profile {self.current_profile_id}.")
        dlg = RenameDialog(self.profiles[self.current_profile_id]["name"], self)
        if dlg.exec():
            new_name = dlg.get_name()
            if new_name:
                for pid, data in self.profiles.items():
                    if data["name"] == new_name and pid != self.current_profile_id:
                        ErrorDialog(tr("name_exists"), self).exec()
                        return
                self.profiles[self.current_profile_id]["name"] = new_name
                self.refresh_profile_menu_labels()
                self.save_current_profile()
                self.logger.info(f"Renamed profile to '{new_name}'")

    def clear_current_profile(self):
        self.logger.debug(f"[ACTION] Clearing profile {self.current_profile_id}.")
        if ConfirmClearDialog(self).exec() == QDialog.DialogCode.Accepted:
            pid = self.current_profile_id
            self.events = []
            self.profiles[pid]["events"] = []
            self.profiles[pid]["name"] = tr("profile_default_name", n=pid)
            self.refresh_profile_menu_labels()
            self.save_current_profile()
            self.bridge.log_signal.emit(tr("log_profile_cleared", pid=pid))
            self.update_status()

    # ==================== СТАТУС ====================
    def update_status(self):
        name = self.profiles[self.current_profile_id]["name"]
        self.lbl_profile_val.setText(name)
        self.lbl_state_val.setText(tr("state_records_exist") if self.events else "—")

    def update_timer_tick(self):
        name = self.profiles[self.current_profile_id]["name"]
        if self.is_recording and not self.is_paused_recording:
            elapsed = time.time() - self.start_time - self.total_paused_duration
            mins, secs = divmod(int(elapsed), 60)
            self.lbl_profile_val.setText(name)
            self.lbl_state_val.setText(tr("state_recording", t=f"{mins:02d}:{secs:02d}"))
        elif self.is_playing and not self.is_paused_playing:
            elapsed = time.time() - self.playback_start_time - self.playback_paused_duration
            cur_m, cur_s = divmod(int(max(0, elapsed)), 60)
            tot_m, tot_s = divmod(int(self.playback_total_duration), 60)
            self.lbl_profile_val.setText(name)
            self.lbl_state_val.setText(tr("state_playing", cur=f"{cur_m:02d}:{cur_s:02d}", tot=f"{tot_m:02d}:{tot_s:02d}"))

    # ==================== ЗАПИСЬ ====================
    def toggle_recording(self):
        self.logger.debug("[ACTION] Toggle recording clicked.")
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.logger.debug("[RECORD] start_recording called.")
        if self.is_playing:
            self.logger.warning("[RECORD] Blocked: playback in progress.")
            self.bridge.log_signal.emit(tr("log_cannot_record_playing"))
            return
        self.recording_layout_hkl = layout_utils.get_current_layout_hkl()
        self.logger.info(f"Recording started with layout HKL: {hex(self.recording_layout_hkl)}")
        self._save_window_states()
        self.is_recording = True
        self.is_paused_recording = False
        self.events = []
        self.active_modifiers = []
        self.last_modifier_down_time = 0
        self.start_time = time.time()
        self.total_paused_duration = 0
        self.btn_record.setText(tr("btn_stop"))
        self.btn_record.setStyleSheet(STYLES["BTN_RED"])
        self.bridge.log_signal.emit(tr("log_recording_started"))
        keyboard.hook(self.on_keyboard_event)
        mouse.hook(self.on_mouse_event)
        self.logger.debug("[RECORD] Hooks installed successfully.")

    def toggle_pause_recording(self):
        self.logger.debug("[ACTION] Toggle pause recording clicked.")
        if not self.is_recording:
            return
        if not self.is_paused_recording:
            self.is_paused_recording = True
            self.pause_start_time = time.time()
            self.btn_pause_rec.setText(tr("btn_resume"))
            self.btn_pause_rec.setStyleSheet(STYLES["BTN_GREEN"])
            self.bridge.log_signal.emit(tr("log_recording_paused"))
            self.lbl_state_val.setText(tr("state_recording_paused"))
        else:
            self.is_paused_recording = False
            self.total_paused_duration += (time.time() - self.pause_start_time)
            self.btn_pause_rec.setText(tr("btn_pause_rec"))
            self.btn_pause_rec.setStyleSheet(STYLES["BTN_GRAY"])
            self.bridge.log_signal.emit(tr("log_recording_resumed"))

    def stop_recording(self):
        self.logger.debug("[RECORD] stop_recording called.")
        self.is_recording = False
        self.is_paused_recording = False
        self.active_modifiers = []
        self.btn_pause_rec.setText(tr("btn_pause_rec"))
        self.btn_pause_rec.setStyleSheet(STYLES["BTN_GRAY"])
        try:
            keyboard.unhook_all()
            mouse.unhook_all()
            self.logger.debug("[RECORD] Hooks removed.")
        except Exception:
            pass
        if self.events:
            stop_time = self.events[-1]["time"]
            filtered = [e for e in self.events if (stop_time - e["time"]) > 0.3]
            self.events = filtered if filtered else (self.events[:-1] if len(self.events) > 1 else [])
        self.btn_record.setText(tr("btn_record"))
        self.btn_record.setStyleSheet(STYLES["BTN_GREEN"])
        self.bridge.log_signal.emit(tr("log_stopped_events", n=len(self.events)))
        self.update_status()
        self.register_hotkeys()

    # ==================== ВОСПРОИЗВЕДЕНИЕ ====================
    def toggle_playback(self):
        self.logger.debug("[ACTION] Toggle playback clicked.")
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def _playback_should_stop(self):
        return self._playback_stop_requested

    def start_playback(self):
        self.logger.debug("[PLAYBACK] start_playback called.")
        self.logger.debug(f"[PLAYBACK] State: is_recording={self.is_recording}, is_playing={self.is_playing}, _launching={self._playback_launching}")
        
        if self.is_recording:
            self.logger.warning("[PLAYBACK] Blocked: recording in progress.")
            self.bridge.log_signal.emit(tr("log_cannot_play_recording"))
            return
        if self.is_playing or self._playback_launching:
            self.logger.warning("[PLAYBACK] Blocked: already playing or launching.")
            return
        if not self.events:
            self.logger.warning("[PLAYBACK] Blocked: no events.")
            safe_invoke(self._show_no_events_warning)
            return

        if self.recording_layout_hkl is not None:
            self.logger.info(f"[PLAYBACK] Recording layout HKL: {hex(self.recording_layout_hkl)} ({layout_utils.layout_name(self.recording_layout_hkl)})")
            
            layout_utils.refresh_input_state()
            
            already_active = layout_utils.is_target_layout_active(self.recording_layout_hkl)
            self.logger.debug(f"[PLAYBACK] is_target_layout_active check: {already_active}")
            
            if not already_active:
                current_hkl = layout_utils.get_current_layout_hkl()
                focus_hkl = layout_utils.get_focus_layout_hkl()
                fg_hkl = layout_utils.get_foreground_layout_hkl()
                
                self.logger.info(f"[PLAYBACK] Current layout HKL: {hex(current_hkl)} ({layout_utils.layout_name(current_hkl)})")
                self.logger.info(f"[PLAYBACK] Focus layout HKL: {hex(focus_hkl) if focus_hkl else 'None'} ({layout_utils.layout_name(focus_hkl) if focus_hkl else '?'})")
                self.logger.info(f"[PLAYBACK] Foreground layout HKL: {hex(fg_hkl) if fg_hkl else 'None'} ({layout_utils.layout_name(fg_hkl) if fg_hkl else '?'})")
                
                self.logger.info("[PLAYBACK] MISMATCH detected - sending lang switch combo")
                
                combo = self.system_lang_switch_combo or "alt+shift"
                self.logger.debug(f"[PLAYBACK] Using combo: '{combo}'")
                
                sent = layout_utils.send_lang_switch_once(combo, self.logger)
                self.logger.debug(f"[PLAYBACK] send_lang_switch_once returned: {sent}")
            else:
                self.logger.debug("[PLAYBACK] Layout already active via all sources - skipping switch")
        else:
            self.logger.debug("[PLAYBACK] No recording_layout_hkl set - skipping layout check")

        self.logger.debug("[PLAYBACK] Starting playback worker thread.")
        self._playback_stop_requested = False
        self._playback_launching = True
        self.playback_start_time = time.time()
        self.playback_paused_duration = 0
        self.playback_total_duration = self.events[-1]['time'] if self.events else 0

        try:
            t = threading.Thread(target=self._playback_worker, daemon=True)
            t.start()
            self.logger.debug(f"[PLAYBACK] Worker thread started, ident={t.ident}")
        except Exception as e:
            self.logger.error(f"[PLAYBACK] Failed to start playback thread: {e}", exc_info=True)
            self._playback_launching = False

    def _show_no_events_warning(self):
        WarningDialog(tr("no_events"), self).exec()

    @pyqtSlot()
    def _on_playback_started_ui(self):
        self.logger.debug("[SIGNAL] _on_playback_started_ui triggered.")
        self._playback_launching = False
        self.is_playing = True
        self.is_paused_playing = False
        self.btn_play.setText(tr("btn_stop"))
        self.btn_play.setStyleSheet(STYLES["BTN_RED"])

    @pyqtSlot()
    def _on_playback_finished_ui(self):
        self.logger.debug("[SIGNAL] _on_playback_finished_ui triggered.")
        self._playback_launching = False
        self._playback_stop_requested = False
        if not self.is_playing:
            self.logger.debug("[SIGNAL] Already not playing, skipping UI reset.")
            return
        self.is_playing = False
        self.is_paused_playing = False
        self.btn_pause_play.setText(tr("btn_pause_play"))
        self.btn_pause_play.setStyleSheet(STYLES["BTN_GRAY"])
        self.btn_play.setText(tr("btn_play"))
        self.btn_play.setStyleSheet(STYLES["BTN_GREEN"])
        layout_utils.release_stuck_modifiers()
        self.bridge.log_signal.emit(tr("log_playback_finished"))
        self.update_status()

    def _playback_worker(self):
        self.logger.debug("[WORKER] Playback worker started.")
        
        try:
            self.logger.debug("[WORKER] Sleeping 100ms for hook release.")
            time.sleep(0.1)

            if self._playback_should_stop():
                self.logger.warning("[WORKER] Stop requested before restore.")
                return

            self.logger.debug("[WORKER] Restoring window states.")
            self._restore_window_states()
            
            if self.recording_layout_hkl is not None:
                self.logger.debug("[WORKER] Waiting 200ms for layout switch to take effect.")
                time.sleep(0.2)
                
                layout_utils.refresh_input_state()
                current_hkl = layout_utils.get_current_layout_hkl()
                focus_hkl = layout_utils.get_focus_layout_hkl()
                
                self.logger.debug(f"[WORKER] After wait - current HKL: {hex(current_hkl)}, focus HKL: {hex(focus_hkl) if focus_hkl else 'None'}")
                self.logger.debug(f"[WORKER] Target HKL: {hex(self.recording_layout_hkl)}")
                
                is_active = layout_utils.is_target_layout_active(self.recording_layout_hkl)
                self.logger.debug(f"[WORKER] is_target_layout_active: {is_active}")
                
                if not is_active:
                    self.logger.warning("[WORKER] Layout still mismatched - retrying switch once.")
                    combo = self.system_lang_switch_combo or "alt+shift"
                    sent = layout_utils.send_lang_switch_once(combo, self.logger)
                    self.logger.debug(f"[WORKER] Retry send result: {sent}")
                    
                    time.sleep(0.2)
                    layout_utils.refresh_input_state()
                    
                    is_active_after_retry = layout_utils.is_target_layout_active(self.recording_layout_hkl)
                    self.logger.debug(f"[WORKER] After retry - is_target_layout_active: {is_active_after_retry}")
                    
                    if is_active_after_retry:
                        self.logger.info("[WORKER] Layout synced successfully after retry.")
                        self.bridge.log_signal.emit(tr("log_layout_synced"))
                    else:
                        self.logger.warning("[WORKER] Layout sync FAILED after retry.")
                        self.bridge.log_signal.emit(tr("log_layout_failed"))
                else:
                    self.logger.debug("[WORKER] Layout already correct after initial wait.")
                    self.bridge.log_signal.emit(tr("log_layout_synced"))

            if self._playback_should_stop():
                self.logger.warning("[WORKER] Stop requested after layout sync.")
                return

            self.logger.debug("[WORKER] Emitting playback_started_signal.")
            self.bridge.playback_started_signal.emit()
            time.sleep(0.02)

            self.logger.debug("[WORKER] Emitting log_playback_started.")
            self.bridge.log_signal.emit(tr("log_playback_started"))
            
            self.logger.info("[WORKER] Starting playback_loop.")
            self.playback_loop()
            self.logger.debug("[WORKER] playback_loop finished.")
            
        except Exception as e:
            self.logger.error(f"[WORKER] Exception in worker: {e}", exc_info=True)
        finally:
            self._playback_launching = False
            self.logger.debug("[WORKER] Worker finished, emitting playback_finished_signal.")
            self.bridge.playback_finished_signal.emit()

    def toggle_pause_playback(self):
        self.logger.debug("[ACTION] Toggle pause playback clicked.")
        if not self.is_playing:
            return
        if not self.is_paused_playing:
            self.is_paused_playing = True
            self.btn_pause_play.setText(tr("btn_resume"))
            self.btn_pause_play.setStyleSheet(STYLES["BTN_GREEN"])
            self.bridge.log_signal.emit(tr("log_playback_paused"))
            self.lbl_state_val.setText(tr("state_playing_paused"))
        else:
            self.is_paused_playing = False
            self.btn_pause_play.setText(tr("btn_pause_play"))
            self.btn_pause_play.setStyleSheet(STYLES["BTN_GRAY"])
            self.bridge.log_signal.emit(tr("log_playback_resumed"))
            elapsed = time.time() - self.playback_start_time - self.playback_paused_duration
            mins, secs = divmod(int(max(0, elapsed)), 60)
            tot_m, tot_s = divmod(int(self.playback_total_duration), 60)
            self.lbl_state_val.setText(tr("state_playing", cur=f"{mins:02d}:{cur_s:02d}", tot=f"{tot_m:02d}:{tot_s:02d}"))

    def stop_playback(self):
        self.logger.debug("[PLAYBACK] stop_playback called.")
        self._playback_stop_requested = True
        self.is_playing = False

    # ==================== ОКНА ====================
    def _save_window_states(self):
        self.logger.debug("[WINDOWS] Saving window states.")
        self.saved_window_states = []
        def enum_cb(hwnd, lParam):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    rect = win32gui.GetWindowRect(hwnd)
                    self.saved_window_states.append({'hwnd': hwnd, 'title': title, 'left': rect[0], 'top': rect[1], 'right': rect[2], 'bottom': rect[3]})
            return True
        win32gui.EnumWindows(enum_cb, None)

    def _restore_window_states(self):
        self.logger.debug("[WINDOWS] Restoring window states.")
        for state in self.saved_window_states:
            try:
                hwnd = state['hwnd']
                if win32gui.IsWindow(hwnd):
                    win32gui.MoveWindow(hwnd, state['left'], state['top'], state['right'] - state['left'], state['bottom'] - state['top'], True)
            except Exception:
                pass

    # ==================== ХУКИ СОБЫТИЙ ====================
    def on_keyboard_event(self, e):
        if not self.is_recording or self.is_paused_recording:
            return
        
        self.logger.debug(f"[HOOK] Key event: name={e.name}, type={e.event_type}, scan_code={e.scan_code}")
        
        if e.name == 'x' or e.name.lower() == 'caps lock':
            self.logger.debug("[HOOK] Ignoring key 'x' or 'caps lock'.")
            return
            
        current_time = time.time() - self.start_time - self.total_paused_duration
        modifier_keys = ['ctrl', 'left ctrl', 'right ctrl', 'alt', 'left alt', 'right alt', 'shift', 'left shift', 'right shift', 'windows', 'left windows', 'right windows']
        is_modifier = e.name in modifier_keys
        
        if is_modifier:
            if e.event_type == 'down':
                if e.name not in self.active_modifiers:
                    self.active_modifiers.append(e.name)
                    self.last_modifier_down_time = current_time
                    self.logger.debug(f"[RECORD] Modifier DOWN added: {e.name}. Active: {self.active_modifiers}")
            elif e.event_type == 'up':
                if e.name in self.active_modifiers:
                    time_since_down = current_time - self.last_modifier_down_time
                    is_standalone = len(self.active_modifiers) == 1 and time_since_down < 0.3
                    if is_standalone:
                        self.logger.debug(f"[RECORD] Standalone modifier detected: {e.name}. Adding as combo.")
                        self.events.append({"time": current_time, "type": "modifier_combo", "data": {"modifiers": list(self.active_modifiers)}})
                    self.active_modifiers.remove(e.name)
                    self.logger.debug(f"[RECORD] Modifier UP removed: {e.name}. Remaining: {self.active_modifiers}")
        else:
            if e.event_type == 'down':
                is_uppercase = len(e.name) == 1 and e.name.isupper()
                effective_modifiers = list(self.active_modifiers)
                if is_uppercase and 'shift' not in effective_modifiers and 'left shift' not in effective_modifiers and 'right shift' not in effective_modifiers:
                    effective_modifiers.append('shift')
                    self.logger.debug(f"[RECORD] Simulating Shift for uppercase char: {e.name}")
                
                if effective_modifiers:
                    self.events.append({"time": current_time, "type": "hotkey_combo", "data": {"modifiers": effective_modifiers, "key": e.name.lower()}})
                    self.logger.debug(f"[RECORD] Hotkey combo saved: {'+'.join(effective_modifiers)}+{e.name}")
                else:
                    self.events.append({"time": current_time, "type": "key_down", "data": {"key": e.name.lower()}})
                    self.logger.debug(f"[RECORD] Key DOWN saved: {e.name}")
            elif e.event_type == 'up':
                if not (len(e.name) == 1 and e.name.isupper()):
                    self.events.append({"time": current_time, "type": "key_up", "data": {"key": e.name.lower()}})
                    self.logger.debug(f"[RECORD] Key UP saved: {e.name}")

    def on_mouse_event(self, e):
        if not self.is_recording or self.is_paused_recording:
            return
        
        current_time = time.time() - self.start_time - self.total_paused_duration
        if isinstance(e, mouse.MoveEvent):
            self.events.append({"time": current_time, "type": "mouse_move", "data": {"x": e.x, "y": e.y}})
            if self.debug_mode:
                self.bridge.log_signal.emit(f"DEBUG RECORD: MOUSE MOVE -> ({e.x}, {e.y})")
            self.logger.debug(f"[HOOK] Mouse move recorded at ({e.x}, {e.y})")
        elif isinstance(e, mouse.ButtonEvent):
            pressed = (e.event_type == 'down')
            try:
                x, y = mouse.get_position()
            except Exception:
                x, y = 0, 0
            self.events.append({"time": current_time, "type": "mouse_click", "data": {"x": x, "y": y, "button": e.button, "pressed": pressed}})
            if self.debug_mode:
                self.bridge.log_signal.emit(f"DEBUG RECORD: MOUSE {'PRESS' if pressed else 'RELEASE'} -> {e.button} at ({x}, {y})")
            self.logger.debug(f"[HOOK] Mouse click recorded: button={e.button}, pressed={pressed} at ({x}, {y})")
        elif isinstance(e, mouse.WheelEvent):
            try:
                x, y = mouse.get_position()
            except Exception:
                x, y = 0, 0
            self.events.append({"time": current_time, "type": "mouse_scroll", "data": {"x": x, "y": y, "dx": 0, "dy": e.delta}})
            if self.debug_mode:
                self.bridge.log_signal.emit(f"DEBUG RECORD: MOUSE SCROLL -> dy={e.delta} at ({x}, {y})")
            self.logger.debug(f"[HOOK] Mouse scroll recorded: dy={e.delta} at ({x}, {y})")

    def _smooth_move_winapi(self, x1, y1, x2, y2):
        dist = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(dist / 4))
        for s in range(1, steps + 1):
            if not self.is_playing:
                break
            while self.is_paused_playing:
                time.sleep(0.1)
                if not self.is_playing:
                    break
            ratio = s / steps
            cx = int(x1 + (x2 - x1) * ratio)
            cy = int(y1 + (y2 - y1) * ratio)
            ctypes.windll.user32.SetCursorPos(cx, cy)
            time.sleep(0.0005)

    def playback_loop(self):
        start = time.time()
        self.playback_start_time = start
        total_events = len(self.events)
        total_duration = self.events[-1]['time'] if total_events > 0 else 0
        self.playback_total_duration = total_duration
        prev_x, prev_y = None, None
        pause_accumulated = 0
        self.playback_paused_duration = 0

        self.logger.debug(f"[PLAYBACK] Loop started. Total events: {total_events}, Duration: {total_duration:.2f}s")

        if self.recording_layout_hkl is not None:
            layout_utils.refresh_input_state()
            if not layout_utils.is_target_layout_active(self.recording_layout_hkl):
                self.logger.warning("[PLAYBACK] Final layout check failed! Retrying switch...")
                combo = self.system_lang_switch_combo or "alt+shift"
                layout_utils.send_lang_switch_once(combo, self.logger)
                time.sleep(0.15)
                layout_utils.refresh_input_state()

        for i, event in enumerate(self.events):
            if not self.is_playing or self._playback_should_stop():
                self.logger.debug(f"[PLAYBACK] Loop interrupted at event {i}.")
                break
            while self.is_paused_playing:
                p_start = time.time()
                time.sleep(0.1)
                if not self.is_playing or self._playback_should_stop():
                    break
                p_duration = time.time() - p_start
                pause_accumulated += p_duration
                self.playback_paused_duration += p_duration
            target = start + event['time'] + pause_accumulated
            sleep_t = target - time.time()
            if sleep_t > 0:
                time.sleep(sleep_t)
            if not self.is_playing or self._playback_should_stop():
                break
            
            etype = event['type']
            data = event['data']
            self.logger.debug(f"[PLAYBACK] Executing event {i+1}/{total_events}: type={etype}")
            
            elapsed = time.time() - start - pause_accumulated
            cur_m, cur_s = divmod(int(elapsed), 60)
            tot_m, tot_s = divmod(int(total_duration), 60)
            name = self.profiles[self.current_profile_id]["name"]
            self.bridge.update_status_signal.emit(name, tr("state_playing", cur=f"{cur_m:02d}:{cur_s:02d}", tot=f"{tot_m:02d}:{tot_s:02d}"))
            
            try:
                if etype == 'mouse_move':
                    x, y = data['x'], data['y']
                    if prev_x is not None:
                        self._smooth_move_winapi(prev_x, prev_y, x, y)
                    else:
                        mouse.move(x, y)
                    prev_x, prev_y = x, y
                    if self.debug_mode:
                        self.bridge.log_signal.emit(f"DEBUG PLAYBACK: MOUSE MOVE -> ({x}, {y})")
                        
                elif etype == 'modifier_combo':
                    modifiers = data.get('modifiers', [])
                    mods_str = "+".join(m.capitalize() for m in modifiers)
                    self.logger.info(f"[PLAYBACK] Emulating modifier_combo: {mods_str}")
                    self.bridge.log_signal.emit(f"MODIFIER COMBO -> {mods_str} | Using system combo: {self.system_lang_switch_combo}")
                    
                    try:
                        layout_utils.release_stuck_modifiers()
                        keyboard.send(self.system_lang_switch_combo, do_press=True, do_release=True)
                        time.sleep(0.2) 
                        layout_utils.release_stuck_modifiers()
                        
                        if self.debug_mode:
                            self.bridge.log_signal.emit("DEBUG PLAYBACK: Physical lang switch emulated successfully")
                    except Exception as e:
                        self.logger.error(f"Physical lang switch emulation failed: {e}")
                        if self.debug_mode:
                            self.bridge.log_signal.emit(f"ERROR: Lang switch emulation failed -> {str(e)}")
                            
                elif etype == 'hotkey_combo':
                    modifiers = data.get('modifiers', [])
                    key = data.get('key', '')
                    if key != 'x':
                        if self.debug_mode:
                            self.bridge.log_signal.emit(f"DEBUG PLAYBACK: HOTKEY COMBO -> {'+'.join(m.capitalize() for m in modifiers)}+{key.upper()}")
                        for mod in modifiers:
                            if mod != 'x':
                                keyboard.press(mod)
                        keyboard.press(key)
                        time.sleep(0.05)
                        keyboard.release(key)
                        for mod in reversed(modifiers):
                            if mod != 'x':
                                keyboard.release(mod)
                                
                elif etype == 'key_down':
                    k = data['key']
                    if k != 'x' and k.lower() != 'caps lock':
                        keyboard.press(k)
                        if self.debug_mode:
                            self.bridge.log_signal.emit(f"DEBUG PLAYBACK: KEY DOWN -> {k}")
                            
                elif etype == 'key_up':
                    k = data['key']
                    if k != 'x' and k.lower() != 'caps lock':
                        keyboard.release(k)
                        if self.debug_mode:
                            self.bridge.log_signal.emit(f"DEBUG PLAYBACK: KEY UP -> {k}")
                            
                elif etype == 'mouse_click':
                    x, y = data['x'], data['y']
                    mouse.move(x, y)
                    prev_x, prev_y = x, y
                    if data['pressed']:
                        mouse.press(data['button'])
                    else:
                        mouse.release(data['button'])
                    if self.debug_mode:
                        self.bridge.log_signal.emit(f"DEBUG PLAYBACK: MOUSE {'PRESS' if data['pressed'] else 'RELEASE'} -> {data['button']} at ({x}, {y})")
                        
                elif etype == 'mouse_scroll':
                    x, y = data['x'], data['y']
                    mouse.move(x, y)
                    prev_x, prev_y = x, y
                    mouse.wheel(data['dy'])
                    if self.debug_mode:
                        self.bridge.log_signal.emit(f"DEBUG PLAYBACK: MOUSE SCROLL -> dy={data['dy']} at ({x}, {y})")
                        
            except Exception as e:
                self.logger.error(f"Playback error at event {i}: {e}")
                if self.debug_mode:
                    self.bridge.log_signal.emit(f"ERROR: Playback failed -> {str(e)}")

    # ==================== ГОРЯЧИЕ КЛАВИШИ ====================
    def register_hotkeys(self):
        self.logger.info("[HOTKEYS] register_hotkeys() called.")
        self._hotkey_filter.unregister_all()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        mappings = {
            "record_start": self.start_recording,
            "record_stop": self.stop_recording,
            "record_pause": self.toggle_pause_recording,
            "play_start": self.start_playback,
            "play_stop": self.stop_playback,
            "play_pause": self.toggle_pause_playback,
            "save_profile": self.save_current_profile,
            "clear_profile": self.clear_current_profile,
            "rename_profile": self.rename_current_profile,
            "quit_app": self.close,
        }
        errors = []
        for action_key, method in mappings.items():
            hk = self.hotkeys.get(action_key)
            if hk:
                hid = self._hotkey_filter.register(hk, method)
                self.logger.debug(f"[HOTKEYS] Registered hotkey '{hk}' for {action_key}, hid={hid}")
                if hid is None:
                    errors.append(f"{action_key} ({hk}): registration failed")
        if errors:
            err_msg = "Hotkey Registration Errors:\n" + "\n".join(errors)
            self.logger.error(err_msg)
            self.bridge.log_signal.emit(err_msg)
        else:
            self.logger.info("[HOTKEYS] All hotkeys registered successfully via RegisterHotKey.")