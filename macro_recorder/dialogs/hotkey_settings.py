"""Диалог настройки глобальных горячих клавиш."""

import threading

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea,
)

import keyboard

from ..i18n import tr
from ..theme import THEMES, CURRENT_THEME, STYLES
from ..hotkeys_utils import hotkey_to_english, contains_forbidden_keys
from .common import ErrorDialog


class HotkeySettingsDialog(QDialog):
    hotkey_updated = pyqtSignal(object, str)
    hotkey_forbidden = pyqtSignal(object, str)
    callback_requested = pyqtSignal(object)

    def __init__(self, parent=None, hotkeys_dict=None, callback=None):
        super().__init__(parent)
        t = THEMES[CURRENT_THEME]

        self.BTN_HOTKEY_STYLE = f"""
            QPushButton {{ 
                background-color: {t['HK_BTN_BG']}; 
                color: white; 
                border-radius: 6px; 
                font-size: 11px; 
                font-weight: bold; 
                border: none; 
                text-transform: none; 
            }}
            QPushButton:hover {{ 
                background-color: {t['GREEN']}; 
            }}
        """

        self.ROW_STYLE = f"""
            QWidget#hotkeyRow {{ background-color: {t['ROW_BG']}; border-radius: 8px; border: 1px solid {t['ROW_BORDER']}; }}
        """

        self.setWindowTitle(tr("hotkey_settings_title"))
        self.setFixedSize(400, 440)
        self.setStyleSheet(f"background-color: {t['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")
        self.hotkeys = dict(hotkeys_dict or {})
        self.callback = callback
        self.btn_refs = {}
        self._capture_lock = threading.Lock()

        self.hotkey_updated.connect(self._apply_new_hotkey)
        self.callback_requested.connect(self._notify_callback)
        self.hotkey_forbidden.connect(self._show_forbidden_error)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QLabel(tr("configure_hotkeys"))
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {t['TEXT_DARK']}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(STYLES["SCROLL_BAR"])

        content = QWidget()
        content.setStyleSheet(f"background-color: {t['PANEL_BG']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)

        self.actions_map = {
            "record_start": tr("act_record_start"),
            "record_stop": tr("act_record_stop"),
            "record_pause": tr("act_record_pause"),
            "play_start": tr("act_play_start"),
            "play_stop": tr("act_play_stop"),
            "play_pause": tr("act_play_pause"),
            "save_profile": tr("act_save_profile"),
            "clear_profile": tr("act_clear_profile"),
            "rename_profile": tr("act_rename_profile"),
            "quit_app": tr("act_quit_app"),
        }

        for key, label_text in self.actions_map.items():
            row = QWidget()
            row.setObjectName("hotkeyRow")
            row.setStyleSheet(self.ROW_STYLE)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(8)

            lbl = QLabel(label_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"QLabel {{ font-size: 11px; font-weight: bold; color: {t['ROW_TEXT']}; border: none; background: transparent; }}")
            row_layout.addWidget(lbl, stretch=1)

            b = QPushButton(hotkey_to_english(self.hotkeys[key]).upper())
            b.setFixedWidth(130)
            b.setFixedHeight(30)
            b.setStyleSheet(self.BTN_HOTKEY_STYLE)

            b.clicked.connect(lambda checked, ak=key: self.capture_hotkey(ak))

            row_layout.addWidget(b, alignment=Qt.AlignmentFlag.AlignTop)
            self.btn_refs[key] = b
            content_layout.addWidget(row)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_reset = QPushButton(tr("reset_defaults"))
        btn_reset.setFixedHeight(36)
        btn_reset.setStyleSheet(f"""
            QPushButton {{ background-color: {t['RESET_BG']}; color: white; border-radius: 8px; font-weight: bold; font-size: 12px; border: none; }}
            QPushButton:hover {{ background-color: {t['GREEN']}; }}
        """)
        btn_reset.clicked.connect(self.reset_defaults)
        layout.addWidget(btn_reset)

    def capture_hotkey(self, action_key):
        btn = self.btn_refs[action_key]
        original_text = btn.text()

        btn.setText(tr("press_combination"))
        btn.setStyleSheet(f"background-color: {THEMES[CURRENT_THEME]['RED']}; color: white; border-radius: 6px; font-weight: bold; text-transform: none;")
        btn.update()

        def listen():
            try:
                new_hotkey = keyboard.read_hotkey(suppress=False)

                if contains_forbidden_keys(new_hotkey):
                    self.hotkey_forbidden.emit(btn, original_text)
                    return

                value = new_hotkey.lower()
                if any(k != action_key and v.lower() == value for k, v in self.hotkeys.items()):
                    self.hotkey_forbidden.emit(btn, original_text)
                    return
                self.hotkeys[action_key] = value
                display_text = hotkey_to_english(new_hotkey).upper()
                self.hotkey_updated.emit(btn, display_text)
                self.callback_requested.emit(dict(self.hotkeys))
            except Exception as e:
                print(f"[DEBUG HOTKEY] Error capturing hotkey: {e}")
                self.hotkey_updated.emit(btn, original_text)

        threading.Thread(target=listen, daemon=True).start()

    @pyqtSlot(object, str)
    def _apply_new_hotkey(self, btn, text):
        if not btn.isVisible():
            return
        btn.setText(text)
        btn.setStyleSheet(self.BTN_HOTKEY_STYLE)
        btn.update()

    @pyqtSlot(object)
    def _notify_callback(self, hotkeys):
        if self.callback:
            self.callback(hotkeys)

    @pyqtSlot(object, str)
    def _show_forbidden_error(self, btn, original_text):
        if btn.isVisible():
            btn.setText(original_text)
            btn.setStyleSheet(self.BTN_HOTKEY_STYLE)
            btn.update()

        err_dlg = ErrorDialog(tr("forbidden_keys_msg"), self)
        err_dlg.exec()

    def reset_defaults(self):
        if self.callback:
            self.callback(None)
        self.accept()